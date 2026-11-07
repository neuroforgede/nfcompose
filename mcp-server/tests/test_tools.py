import asyncio
from urllib.parse import parse_qs, urlsplit
from unittest.mock import MagicMock, Mock, patch

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from nfcompose_mcp.api import ComposeTools, ReadOnlyClient
from nfcompose_mcp.server import create_server


@pytest.fixture
def client():
    return ReadOnlyClient("https://compose.example", "test-user", "test-password")


def test_query_encoding_and_one_page(client):
    client.get = Mock(return_value={"data": [{"external_id": "a"}], "next":
        "https://compose.example/api/dataseries/x/?last=YWJj%2B%2F%3D"})
    result = ComposeTools(client).query_data_points(
        "orders & stuff", {"name": {"$eq": "a&b+#"}}, ["name", "total"], 5)
    url = client.get.call_args.args[0]
    assert "orders%20%26%20stuff" in url
    params = parse_qs(urlsplit(url).query)
    assert params["filter"] == ['{"name":{"$eq":"a&b+#"}}']
    assert params["include_in_payload"] == ["name,total"]
    assert params["pagesize"] == ["5"]
    assert result["next_cursor"] == "YWJj+/="
    assert client.get.call_count == 1


def test_cursor_never_becomes_request_url(client):
    client.get = Mock(return_value={"data": [], "next": None})
    ComposeTools(client).query_data_points("orders", cursor="https://evil.example/?secret")
    url = client.get.call_args.args[0]
    assert url.startswith("https://compose.example/api/dataseries/")
    assert parse_qs(urlsplit(url).query)["last"] == ["https://evil.example/?secret"]


@pytest.mark.parametrize("pagesize", [0, -1, 101])
def test_pagesize_bounds_before_network(client, pagesize):
    client.get = Mock()
    with pytest.raises(ValueError, match="pagesize"):
        ComposeTools(client).query_data_points("orders", pagesize=pagesize)
    client.get.assert_not_called()


@pytest.mark.parametrize("external_id", ["..", ".", "", "a/b", "a\\b"])
def test_path_segments(client, external_id):
    with pytest.raises(ValueError):
        ComposeTools(client).get_data_point("orders", external_id)


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete", "post_multipart", "patch_multipart"])
def test_transport_denies_writes(client, method):
    with pytest.raises(ValueError, match="only supports GET"):
        getattr(client, method)("https://compose.example", {})


def test_untrusted_schema_links_rejected(client):
    client.session.get = MagicMock()
    with pytest.raises(ValueError):
        client.get("https://evil.example/api/dataseries/")
    client.session.get.assert_not_called()


def test_redirects_and_timeouts(client):
    response = MagicMock(status_code=302)
    with patch("requests.Session.request", return_value=response) as request:
        with pytest.raises(ValueError, match="302"):
            client.session.get(client.url("/api/dataseries/dataseries/"))
        kwargs = request.call_args.kwargs
        assert kwargs["allow_redirects"] is False
        assert kwargs["timeout"] == (5, 30)
        assert kwargs["verify"] is True


def test_response_size_limit(client):
    response = MagicMock(status_code=200)
    response.iter_content.return_value = [b"x" * 2_000_001]
    with patch("requests.Session.request", return_value=response):
        with pytest.raises(ValueError, match="2 MB"):
            client.session.get(client.url("/api/dataseries/dataseries/"))


def test_mcp_discovery_and_call(client):
    client.get = Mock(return_value={"results": [{"external_id": "orders", "name": "Orders"}], "next": None})

    async def run():
        server = create_server(client)
        async with create_connected_server_and_client_session(server._mcp_server) as session:
            tools = (await session.list_tools()).tools
            assert {t.name for t in tools} == {"list_data_series", "describe_data_series", "query_data_points", "get_data_point", "build_data_points_url"}
            assert all(t.annotations.readOnlyHint for t in tools)
            result = await session.call_tool("list_data_series", {})
            assert not result.isError
            assert result.structuredContent["data_series"][0]["external_id"] == "orders"
            error = await session.call_tool("query_data_points", {"data_series": "orders", "pagesize": 1000})
            assert error.isError
    asyncio.run(run())


def test_describe_uses_client_model_without_admin_reads(client):
    from dataclasses import fields
    from compose_client.library.models.raw.data_series import RawDataSeries

    raw = {field.name: "unused" for field in fields(RawDataSeries)}
    raw.update(external_id="orders", name="Orders", backend="DYNAMIC_SQL_NO_HISTORY",
               allow_extra_fields=False, locked=False, data_point_structure={}, extra_config={})
    for kind in ("float", "string", "text", "timestamp", "image", "file", "json", "boolean"):
        raw[kind + "_facts"] = client.url(f"/api/dataseries/dataseries/id/{kind}fact/")
    raw["dimensions"] = client.url("/api/dataseries/dataseries/id/dimension/")

    def get(url):
        if "/by-external-id/" in url:
            return raw
        if url.endswith("/floatfact/"):
            return [{"external_id": "total", "name": "Total", "optional": False}]
        if url.endswith("/dimension/"):
            return [{"external_id": "customer", "name": "Customer", "optional": True,
                     "reference": "https://compose.example/api/dataseries/dataseries/customer-id/"}]
        return []

    client.get = Mock(side_effect=get)
    result = ComposeTools(client).describe_data_series("orders")
    assert result["fields"] == [
        {"external_id": "total", "name": "Total", "optional": False, "type": "float"},
        {"external_id": "customer", "name": "Customer", "optional": True,
         "type": "dimension", "reference": "https://compose.example/api/dataseries/dataseries/customer-id/"}]
    assert client.get.call_count == 10
    assert all("permission" not in call.args[0] and "consumer" not in call.args[0]
               for call in client.get.call_args_list)


def test_sdk_login_cache_and_refresh(client):
    import datetime
    import requests

    def response(token):
        result = requests.Response()
        result.status_code = 200
        result._content = ('{"token":"' + token + '"}').encode()
        return result

    client.session.post = Mock(side_effect=[response("first"), response("second")])
    assert client.headers["Authorization"] == "Token first"
    assert client.headers["Authorization"] == "Token first"
    assert client.session.post.call_count == 1
    client._headers_cache_timestamp = datetime.datetime.now() - datetime.timedelta(seconds=121)
    assert client.headers["Authorization"] == "Token second"
    assert client.session.post.call_args.kwargs["json"] == {
        "username": "test-user", "password": "test-password"}
    assert client.session.post.call_args.kwargs["url"] == "https://compose.example/api/common/auth/authtoken/"


def test_username_password_environment(monkeypatch):
    monkeypatch.setenv("NFCOMPOSE_URL", "https://compose.example")
    monkeypatch.setenv("NFCOMPOSE_USERNAME", "alice")
    monkeypatch.setenv("NFCOMPOSE_PASSWORD", "secret")
    client = ReadOnlyClient.from_env()
    assert client.credentials.user == "alice"
    assert client.credentials.password == "secret"
    client.session.close()


def test_query_links_match_executed_request(client):
    client.get = Mock(return_value={"data": [], "next": None})
    result = ComposeTools(client).query_data_points(
        "orders & stuff", {"name": {"$eq": "a&b+# ü"}}, ["name", "total"], 7, "YWJj+/=")
    assert result["api_url"] == client.get.call_args.args[0]
    browser = urlsplit(result["browser_url"])
    api = urlsplit(result["api_url"])
    assert (browser.scheme, browser.netloc, browser.path) == (api.scheme, api.netloc, api.path)
    assert parse_qs(browser.query) == {**parse_qs(api.query), "format": ["api"]}
    assert "test-password" not in result["browser_url"]
    assert "test-user" not in result["browser_url"]


def test_build_link_does_not_fetch_or_login(client):
    client.get = Mock()
    client.session.post = Mock()
    tools = ComposeTools(client)
    link = tools.build_data_points_url("orders", {"total": {"$gte": 1000}}, ["total"], 5)
    assert link["executed"] is False
    client.get.assert_not_called()
    client.session.post.assert_not_called()
    client.get.return_value = {"data": [], "next": None}
    executed = tools.query_data_points("orders", {"total": {"$gte": 1000}}, ["total"], 5)
    assert link["api_url"] == executed["api_url"]
    assert link["browser_url"] == executed["browser_url"]


def test_list_and_record_links(client):
    tools = ComposeTools(client)
    client.get = Mock(return_value={"results": [], "next": None})
    listing = tools.list_data_series(5, 2)
    assert listing["api_url"] == client.get.call_args.args[0]
    assert parse_qs(urlsplit(listing["browser_url"]).query) == {
        "pagesize": ["5"], "page": ["2"], "format": ["api"]}
    client.get.return_value = {"external_id": "order #1", "payload": {"total": 100}}
    record = tools.get_data_point("orders", "order #1")
    assert record["payload"] == {"total": 100}
    assert record["api_url"] == client.get.call_args.args[0]
    assert "/order%20%231/" in record["browser_url"]


def test_browser_filter_readable_with_necessary_escaping(client):
    import json
    filter_value = {"$and": [{"total": {"$gte": 1000}}, {"name": "a&b+#% ü /?=\\\""}]}
    link = ComposeTools(client).build_data_points_url("orders", filter_value)
    browser_url = link["browser_url"]
    assert 'filter={"$and":[{"total":{"$gte":1000}},{"name":' in browser_url
    assert '%26' in browser_url
    assert '%2B' in browser_url
    assert '%23' in browser_url
    assert '%25' in browser_url
    assert urlsplit(browser_url).fragment == ""
    params = parse_qs(urlsplit(browser_url).query)
    assert json.loads(params["filter"][0]) == filter_value
    assert set(params) == {"pagesize", "identify_dimensions_by_external_id", "filter", "format"}


def test_changes_since_request_links_and_pagination(client):
    client.get = Mock(return_value={"data": [], "next": "https://compose.example/?last=YWJj"})
    tools = ComposeTools(client)
    timestamp = "2026-11-07T09:00:00+01:00"
    first = tools.query_data_points("orders", filter={"total": {"$gte": 10}}, changes_since=timestamp)
    for key in ("api_url", "browser_url"):
        assert parse_qs(urlsplit(first[key]).query)["changes_since"] == [timestamp]
    assert first["api_url"] == client.get.call_args.args[0]
    second = tools.query_data_points("orders", filter={"total": {"$gte": 10}},
                                     changes_since=timestamp, cursor=first["next_cursor"])
    query = parse_qs(urlsplit(second["api_url"]).query)
    assert query["changes_since"] == [timestamp]
    assert query["last"] == ["YWJj"]
    link = tools.build_data_points_url("orders", filter={"total": {"$gte": 10}}, changes_since=timestamp)
    assert link["browser_url"] == first["browser_url"]


@pytest.mark.parametrize("timestamp", ["", "nonsense", "2026-11-07", "2026-11-07T09:00:00", "2026-99-07T00:00:00Z"])
def test_invalid_changes_since_rejected_before_request(client, timestamp):
    client.get = Mock()
    for method in (ComposeTools(client).query_data_points, ComposeTools(client).build_data_points_url):
        with pytest.raises(ValueError, match="changes_since"):
            method("orders", changes_since=timestamp)
    client.get.assert_not_called()


def test_changes_since_utc_and_omission(client):
    tools = ComposeTools(client)
    link = tools.build_data_points_url("orders", changes_since="2026-11-07T00:00:00Z")
    assert parse_qs(urlsplit(link["api_url"]).query)["changes_since"] == ["2026-11-07T00:00:00+00:00"]
    assert "changes_since" not in parse_qs(urlsplit(tools.build_data_points_url("orders")["api_url"]).query)


@pytest.mark.parametrize("total", [0, 1234])
def test_count_request_response_and_links(client, total):
    client.get = Mock(return_value={"data": [], "next": None, "count": total})
    tools = ComposeTools(client)
    result = tools.query_data_points("orders", filter={"total": {"$gte": 10}},
                                     changes_since="2026-11-07T00:00:00Z", count=True)
    assert result["count"] == total
    assert result["api_url"] == client.get.call_args.args[0]
    for key in ("api_url", "browser_url"):
        params = parse_qs(urlsplit(result[key]).query)
        assert params["count"] == ["true"]
        assert "changes_since" in params
        assert "filter" in params
    client.get.reset_mock()
    link = tools.build_data_points_url("orders", filter={"total": {"$gte": 10}},
                                       changes_since="2026-11-07T00:00:00Z", count=True)
    assert link["browser_url"] == result["browser_url"]
    client.get.assert_not_called()


@pytest.mark.parametrize("count", [False, True])
def test_missing_count_not_invented(client, count):
    client.get = Mock(return_value={"data": [], "next": None})
    result = ComposeTools(client).query_data_points("orders", count=count)
    assert "count" not in result
    params = parse_qs(urlsplit(result["api_url"]).query)
    assert ("count" in params) == count


def test_mcp_count_schema_and_call(client):
    client.get = Mock(return_value={"data": [], "next": None, "count": 12})

    async def run():
        async with create_connected_server_and_client_session(create_server(client)._mcp_server) as session:
            tools = (await session.list_tools()).tools
            for tool in tools:
                if tool.name in {"query_data_points", "build_data_points_url"}:
                    assert tool.inputSchema["properties"]["count"]["type"] == "boolean"
                    assert tool.inputSchema["properties"]["count"]["default"] is False
            result = await session.call_tool("query_data_points", {"data_series": "orders", "count": True})
            assert not result.isError
            assert result.structuredContent["count"] == 12
            assert parse_qs(urlsplit(client.get.call_args.args[0]).query)["count"] == ["true"]
    asyncio.run(run())


def test_mcp_pagesize_matches_rest_naming(client):
    client.get = Mock(return_value={"data": [], "next": None})

    async def run():
        async with create_connected_server_and_client_session(create_server(client)._mcp_server) as session:
            for tool in (await session.list_tools()).tools:
                if tool.name in {"list_data_series", "query_data_points", "build_data_points_url"}:
                    properties = tool.inputSchema["properties"]
                    assert "limit" not in properties
                    assert properties["pagesize"]["default"] == 20
            result = await session.call_tool("query_data_points", {"data_series": "orders", "pagesize": 7})
            assert not result.isError
            assert parse_qs(urlsplit(client.get.call_args.args[0]).query)["pagesize"] == ["7"]
    asyncio.run(run())
