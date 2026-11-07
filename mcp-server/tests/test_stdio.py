"""Exercise a real MCP subprocess and HTTP transport against a local REST stub."""
import asyncio
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_stdio_to_rest():
    received = []
    logins = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            assert self.path == "/api/common/auth/authtoken/"
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            logins.append(body)
            result = b'{"token":"stub-token"}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(result)))
            self.end_headers()
            self.wfile.write(result)

        def do_GET(self):
            received.append((self.path, self.headers.get("Authorization")))
            body = json.dumps({"results": [{"external_id": "orders", "name": "Orders"}],
                               "next": None}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=http.serve_forever, daemon=True)
    thread.start()

    async def run():
        env = dict(os.environ, NFCOMPOSE_URL=f"http://127.0.0.1:{http.server_port}",
                   NFCOMPOSE_USERNAME="stub-user", NFCOMPOSE_PASSWORD="stub-password")
        params = StdioServerParameters(command=sys.executable,
                                       args=["-m", "nfcompose_mcp.server"], env=env)
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                result = await session.call_tool("list_data_series", {"pagesize": 3})
                assert not result.isError
                assert result.structuredContent["data_series"] == [{"external_id": "orders", "name": "Orders"}]
                assert not (await session.call_tool("list_data_series", {"pagesize": 3})).isError
    try:
        asyncio.run(run())
        assert logins == [{"username": "stub-user", "password": "stub-password"}]
        assert received == [("/api/dataseries/dataseries/?pagesize=3&page=1", "Token stub-token")] * 2
    finally:
        http.shutdown()
        http.server_close()
        thread.join()
