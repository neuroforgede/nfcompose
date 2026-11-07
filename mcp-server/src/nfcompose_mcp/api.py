"""One-page REST adapter using compose_client's interface and raw model."""
from __future__ import annotations

import json
from datetime import datetime
import os
from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlsplit

import requests
from compose_client.library.connection.client import APIClient, Credentials, RequestsSessionRestClient
from compose_client.library.models.raw.data_series import RawDataSeriesAPIConverter


class BoundedSession(requests.Session):
    """Bound requests, including the SDK's internal username/password login."""
    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.update(timeout=(5, 30), allow_redirects=False, stream=True, verify=True)
        try:
            response = super().request(method, url, **kwargs)
            with response:
                if response.status_code != 200:
                    raise ValueError(f"NF Compose returned HTTP {response.status_code}; check credentials, access and identifiers")
                body = bytearray()
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > 2_000_000:
                        raise ValueError("Response exceeds 2 MB; select fewer fields or use a smaller page")
                response._content = bytes(body)
                response._content_consumed = True
            return response
        except requests.RequestException as exc:
            raise ValueError("NF Compose request failed") from exc


class ReadOnlyClient(RequestsSessionRestClient):
    def __init__(self, base_url: str, username: str, password: str):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in {"http", "https"} or not parsed.netloc
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in {"", "/"}):
            raise ValueError("NFCOMPOSE_URL must be an HTTP(S) origin, e.g. https://compose.example.com")
        if not username or not password:
            raise ValueError("Set NFCOMPOSE_USERNAME and NFCOMPOSE_PASSWORD")
        self.base_url = base_url.rstrip("/")
        super().__init__(session=BoundedSession(),
                         credentials=Credentials(self.base_url, username, password))

    @classmethod
    def from_env(cls) -> ReadOnlyClient:
        return cls(os.environ["NFCOMPOSE_URL"], os.environ["NFCOMPOSE_USERNAME"],
                   os.environ["NFCOMPOSE_PASSWORD"])

    def url(self, path: str) -> str:
        if not path.startswith("/api/dataseries/") or "#" in path:
            raise ValueError("Only DataSeries API paths are allowed")
        return self.base_url + path

    def get(self, url: str) -> Any:
        parsed = urlsplit(url)
        origin = urlsplit(self.base_url)
        if (parsed.scheme, parsed.netloc) != (origin.scheme, origin.netloc) or not parsed.path.startswith("/api/dataseries/"):
            raise ValueError("Refusing a URL outside the configured DataSeries API")
        try:
            return super().get(url)
        except (requests.RequestException, json.JSONDecodeError) as exc:
            raise ValueError("NF Compose request failed or returned invalid JSON") from exc

    def _deny(self, *args: Any, **kwargs: Any) -> Any:
        raise ValueError("This MCP adapter only supports GET for data; login is handled internally by compose_client")

    post = put = patch = delete = post_multipart = patch_multipart = _deny


ROOT = "/api/dataseries/"
FACT_TYPES = ("float", "string", "text", "timestamp", "image", "file", "json", "boolean")


def identifier(value: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError("External IDs must be nonempty single path segments")
    return quote(value, safe="")


def validate_pagesize(pagesize: int) -> None:
    if not 1 <= pagesize <= 100:
        raise ValueError("pagesize must be between 1 and 100")


class ComposeTools:
    def __init__(self, client: APIClient):
        self.client = client

    def _links(self, path: str, params: dict[str, Any] | None = None) -> dict[str, str]:
        params = params or {}
        api_url = self.client.url(path + ("?" + urlencode(params) if params else ""))
        # Keep filter JSON editable while protecting query separators, fragments,
        # literal percent/plus signs, whitespace, and non-ASCII values.
        browser_query = "&".join(
            quote(key, safe="") + "=" + quote(str(value), safe='{}[]":,$/' if key == "filter" else "")
            for key, value in {**params, "format": "api"}.items()
        )
        browser_url = self.client.url(path + "?" + browser_query)
        return {"api_url": api_url, "browser_url": browser_url}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = "?" + urlencode(params) if params else ""
        return self.client.get(self.client.url(path + query))

    @staticmethod
    def _summary(ds: dict[str, Any]) -> dict[str, Any]:
        return {key: ds[key] for key in ("external_id", "name", "backend", "allow_extra_fields") if key in ds}

    def list_data_series(self, pagesize: int = 20, page: int = 1) -> dict[str, Any]:
        validate_pagesize(pagesize)
        if page < 1:
            raise ValueError("page must be positive")
        result = self._get(ROOT + "dataseries/", {"pagesize": pagesize, "page": page})
        return {"data_series": [self._summary(ds) for ds in result["results"]],
                "next_page": page + 1 if result.get("next") else None,
                **self._links(ROOT + "dataseries/", {"pagesize": pagesize, "page": page})}

    def describe_data_series(self, data_series: str) -> dict[str, Any]:
        path = ROOT + "by-external-id/dataseries/" + identifier(data_series) + "/"
        raw = self._get(path)
        ds = RawDataSeriesAPIConverter()(raw)
        fields = []
        # Child structure endpoints return unpaginated lists. No consumers,
        # permissions, or indexes are fetched merely to describe the schema.
        for kind in (*FACT_TYPES, "dimension"):
            suffix = "dimensions" if kind == "dimension" else kind + "_facts"
            entries = self.client.get(getattr(ds, suffix))
            for entry in entries:
                field = {key: entry[key] for key in ("external_id", "name", "optional")}
                field["type"] = kind
                if kind == "dimension":
                    field["reference"] = entry["reference"]
                fields.append(field)
        return {**self._summary(raw), "fields": fields, **self._links(path),
                "filter_operators": ["$or", "$and", "$not", "$eq", "$lt", "$lte", "$ne", "$gte", "$gt", "$in", "$nin", "$prefix"],
                "filter_example": {"FIELD_EXTERNAL_ID": {"$eq": "value"}},
                "notes": "Use field external IDs in filters and fields. Dimension payload values are external IDs. Referenced dataset URLs identify relationships; access requires separate permissions."}

    def _data_points_request(self, data_series: str, filter: dict[str, Any] | None = None,
                          fields: list[str] | None = None, pagesize: int = 20,
                          cursor: str | None = None,
                          changes_since: str | None = None, count: bool = False) -> tuple[str, dict[str, Any]]:
        validate_pagesize(pagesize)
        path = ROOT + "by-external-id/dataseries/" + identifier(data_series) + "/datapoint/"
        params: dict[str, Any] = {"pagesize": pagesize, "identify_dimensions_by_external_id": "true"}
        if count:
            params["count"] = "true"
        if changes_since is not None:
            try:
                timestamp = datetime.fromisoformat(changes_since)
                if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                    raise ValueError("Missing timezone")
            except ValueError:
                raise ValueError("changes_since must be an ISO 8601 datetime with timezone, e.g. 2026-11-07T00:00:00Z") from None
            params["changes_since"] = timestamp.isoformat()
        if filter is not None:
            params["filter"] = json.dumps(filter, separators=(",", ":"))
        if fields is not None:
            if not fields or any(not name or "," in name for name in fields):
                raise ValueError("fields must contain nonempty field external IDs without commas")
            params["include_in_payload"] = ",".join(fields)
        if cursor is not None:
            if len(cursor) > 8192:
                raise ValueError("Cursor is too long")
            params["last"] = cursor
        return path, params

    def build_data_points_url(self, data_series: str, filter: dict[str, Any] | None = None,
                              fields: list[str] | None = None, pagesize: int = 20,
                              cursor: str | None = None,
                          changes_since: str | None = None, count: bool = False) -> dict[str, Any]:
        path, params = self._data_points_request(data_series, filter, fields, pagesize, cursor, changes_since, count)
        return {**self._links(path, params), "executed": False,
                "notes": "URL generated locally; query and access have not been checked by NF Compose."}

    def query_data_points(self, data_series: str, filter: dict[str, Any] | None = None,
                          fields: list[str] | None = None, pagesize: int = 20,
                          cursor: str | None = None,
                          changes_since: str | None = None, count: bool = False) -> dict[str, Any]:
        path, params = self._data_points_request(data_series, filter, fields, pagesize, cursor, changes_since, count)
        result = self._get(path, params)
        next_url = result.get("next")
        # Extract only the backend cursor; never follow model-supplied URLs.
        next_cursor = parse_qs(urlsplit(next_url).query).get("last", [None])[0] if next_url else None
        if next_url and next_cursor is None:
            raise ValueError("NF Compose returned an unsupported pagination link")
        return {"data": result["data"], "next_cursor": next_cursor, "has_more": bool(next_url),
                **self._links(path, params),
                **({"count": result["count"]} if "count" in result else {}),
                "notes": "Reuse the same dataset, filter, fields, pagesize, changes_since, and count with next_cursor."}

    def get_data_point(self, data_series: str, external_id: str) -> dict[str, Any]:
        path = (ROOT + "by-external-id/dataseries/" + identifier(data_series)
                + "/datapoint/" + identifier(external_id) + "/")
        params = {"identify_dimensions_by_external_id": "true"}
        return {**self._get(path, params), **self._links(path, params)}
