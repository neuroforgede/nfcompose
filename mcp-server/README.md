# NF Compose REST MCP server

A separate, stdio-only MCP server with five tools:

| Tool | Purpose |
| --- | --- |
| `list_data_series(pagesize=20, page=1)` | List datasets; continue with `next_page` |
| `describe_data_series(data_series)` | Read typed facts and dimension references |
| `query_data_points(data_series, filter, fields, pagesize=20, cursor, changes_since, count=false)` | Read one page of current records |
| `get_data_point(data_series, external_id)` | Retrieve one current record |
| `build_data_points_url(data_series, filter, fields, pagesize=20, cursor, changes_since, count=false)` | Build query links without running the query |

Dataset, record, and field identifiers are **external IDs**. Dimension payload
values are requested as external IDs. Dimension schema references remain dataset
URLs, so describing a schema does not require read access to referenced datasets.
The upstream REST API validates filters and permissions. Schema discovery needs
structure-read permissions in addition to access to the dataset itself.

## Install

Python 3.11+; from the repository root:

```bash
python3 -m venv mcp-server/.venv
mcp-server/.venv/bin/python -m pip install -e ./client -e './mcp-server[test]'
```

This uses the local Python client library. It reuses `APIClient` and the raw
DataSeries converter, with a bounded transport and its existing username/password login. Existing high-level
fetchers traverse all pages and can fetch consumers, permissions, and indexes;
those behaviors are unsuitable for bounded interactive queries. The existing
client library and backend are unchanged.

The MCP dependency deliberately stays on the official Python SDK's v1 API
(`mcp>=1.20,<2`); moving to v2 requires migrating its server imports.

## Run

Supply the origin, without `/api`, and the username/password of an appropriately
scoped nfcompose user. The Python client logs in and caches its API credential
internally; no manually managed token is needed. Environment variables are not loaded from `.env` files.

```bash
export NFCOMPOSE_URL=https://compose.example.com
export NFCOMPOSE_USERNAME=your-user
export NFCOMPOSE_PASSWORD=your-password
mcp-server/.venv/bin/nfcompose-mcp
```

The process speaks MCP on stdin/stdout. Configure your MCP host to launch it;
manual startup waits for protocol input. Example host configuration (adapt its
location and environment handling to your host):

```json
{
  "mcpServers": {
    "nfcompose": {
      "command": "/absolute/path/nfcompose/mcp-server/.venv/bin/nfcompose-mcp",
      "env": {
        "NFCOMPOSE_URL": "https://compose.example.com",
        "NFCOMPOSE_USERNAME": "your-user",
        "NFCOMPOSE_PASSWORD": "your-password"
      }
    }
  }
}
```

Keep actual credentials out of committed config. Each process uses one upstream
identity; tenant selection and authorization remain with nfcompose. This is not
a hosted multi-user OAuth service.

## Example workflow

1. Call `list_data_series`.
2. Call `describe_data_series` with an accessible dataset external ID.
3. Query using field names from that schema, for example:

```json
{
  "data_series": "orders",
  "filter": {"total": {"$gte": 1000}},
  "fields": ["total", "customer"],
  "pagesize": 20
}
```

`query_data_points` returns `data`, `has_more`, and `next_cursor`. Continue with
that cursor and the **same dataset, filter, fields, pagesize, and changes_since**. It never follows
a caller-supplied URL. Listings use page numbers instead of datapoint cursors.
Records retain the upstream REST response format, including metadata and payload.

## Bounds and current scope

- Data operations use GET only; mutation methods reject calls locally.
  The Python client internally POSTs username/password to
  `/api/common/auth/authtoken/` for authentication and refreshes its cache
  after 120 seconds.
- 1–100 records per page, 5-second connect / 30-second socket read timeouts,
  and a 2 MB cap per HTTP response. The read timeout is not a total query deadline.
- Credentials only go to the configured origin; redirects are rejected and TLS
  verification stays enabled. Use HTTPS outside local development.
- Schema child lists are unpaginated upstream. Very large schemas may hit the
  response cap; selecting fewer fields helps datapoint queries, not schema reads.
- Permission failures return the HTTP status without echoing server bodies.
- No writes, history, SQL generation/execution, Flow calls, file downloads,
  local file access tools, or arbitrary REST request tool.
- No schema cache or client-side field/type validator; the REST API remains
  authoritative. A smaller page/field selection is needed for oversized records.

## Verify

```bash
mcp-server/.venv/bin/python -m pytest mcp-server/tests -q
```

Tests cover URL encoding, pagination, read-only enforcement, response bounds,
schema discovery using the client model, MCP tool discovery/calls, and a real
stdio subprocess making an HTTP request against a local REST stub. These do not
replace validation against a running nfcompose instance with representative
permissions and datasets.

## Links for reviewing queries

Every read tool returns `api_url` and `browser_url`. The latter selects the
nfcompose browsable API (`format=api`), preserving the exact request parameters,
including filters, selected fields, page size, and continuation cursor. Filter
JSON punctuation stays readable in browser links; URL-significant characters
inside values are escaped so the query still means the same thing. The
coworker should include this link with its findings so the user can inspect the
request. Schema descriptions link to the dataset detail page; individual record
reads link to that record.

`build_data_points_url` accepts the same arguments as `query_data_points` but
performs no HTTP requests or login. Its result includes `executed: false`:
constructing a URL does not validate fields, permissions, or query results.

Links contain no authentication credentials. Users authenticate separately in
the browser and see data according to their own permissions. Links use the
configured nfcompose origin, which must be reachable from the user's browser.
These are live queries, not saved results; data may change after the MCP read.
Filter values appear in the URL, so share links only with appropriate recipients.

## Changes since a timestamp

Both `query_data_points` and `build_data_points_url` accept `changes_since`,
for example `"2026-11-07T00:00:00Z"` or `"2026-11-07T09:00:00+01:00"`.
The timestamp must include a timezone. Invalid or timezone-less values are
rejected locally, avoiding the REST endpoint silently ignoring invalid input.
It combines with filters and field selection, and is retained in both links.
Keep the same `changes_since` when continuing with `next_cursor`. This selects
changed records in the current-state endpoint; it does not expose full history.

## Counting matching records

Set `count: true` on `query_data_points` to request the upstream total matching
records alongside the current page. The response includes `count` when nfcompose
returns it, including zero; this is not the length of the page. Counting is off
by default to avoid extra query cost. `build_data_points_url` supports the same
flag and adds `count=true` to both links without making a request. Keep the same
flag when continuing with a cursor. Counts and page contents reflect live data.
