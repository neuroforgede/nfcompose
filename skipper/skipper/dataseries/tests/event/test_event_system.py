# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import functools
import json
import threading
import time

import asyncio
import requests
import selectors
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import List, Type, Any, TypeVar, Dict, Optional

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.models.metamodel.consumer import Consumer
from skipper.dataseries.models.event import ConsumerEvent, ConsumerEventState, try_send_events

_ServerSelector: Any
if hasattr(selectors, 'PollSelector'):
    _ServerSelector = selectors.PollSelector
else:
    _ServerSelector = selectors.SelectSelector


class TestHTTPServer(HTTPServer):
    _async_stopped: List[bool]
    _failed: List[Any]

    _handle_request_noblock: Any

    def start_selector(self) -> None:
        self.selector = _ServerSelector()
        self.selector.register(self, selectors.EVENT_READ)

    def stop_selector(self) -> None:
        self.selector.close()

    def serve_once(self, poll_interval: float = 0.5) -> None:
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        try:
            # XXX: Consider using another file descriptor or connecting to the
            # socket to wake this up instead of polling. Polling reduces our
            # responsiveness to a shutdown request and wastes cpu at all other
            # times.
            ready = self.selector.select(poll_interval)
            if ready:
                self._handle_request_noblock()

            self.service_actions()
        finally:
            self.__shutdown_request = False


async def handle(http_server: TestHTTPServer, timeout: float) -> None:
    _waiting_since: float = 0
    while not http_server._async_stopped[0]:
        if _waiting_since > timeout:
            http_server._failed[0] = AssertionError('timeout after ' + str(_waiting_since))
            break
        http_server.serve_once(0.1)
        await asyncio.sleep(0.1)
        _waiting_since += 0.1


_T = TypeVar('_T')


def run_in_executor(f: Any) -> Any:
    @functools.wraps(f)
    def inner(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, functools.partial(f, *args, **kwargs))

    return inner


def run_requests(server_handler_clz: Type[SimpleHTTPRequestHandler], callable: Any, timeout: float) -> None:
    _failed: List[Any] = [None]

    _port: Optional[int] = None
    _done = [False]

    async def runner() -> None:
        nonlocal _done
        nonlocal _failed
        nonlocal _port
        http_server = TestHTTPServer(('', 0), server_handler_clz)
        http_server._async_stopped = _done
        http_server._failed = _failed
        try:
            http_server.start_selector()
            try:
                handler = asyncio.create_task(handle(http_server, timeout))
                _port = http_server.server_port
                await handler
                if _failed[0] is not None:
                    print(_failed)
                    raise _failed[0]
            finally:
                http_server.stop_selector()
        finally:
            http_server.server_close()

    thread = threading.Thread(target=lambda: asyncio.run(runner()), args=())
    thread.start()

    _waiting_since: float = 0
    while _port is None:
        if _waiting_since > 10:
            break
        time.sleep(0.1)
        _waiting_since += 0.1

    callable(_port)
    _done[0] = True

    thread.join(10)

    if _failed[0] is not None:
        print(_failed)
        raise _failed[0]


DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class EventSystemTest(BaseViewTest):
    simulate_other_tenant = False
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    max_events: Optional[int] = None

    def assert_single_event_state(self, consumer: Consumer, state: ConsumerEventState) -> ConsumerEvent:
        consumer_events: List[ConsumerEvent] = list(ConsumerEvent.objects.filter(
            consumer=consumer
        ).all())
        self.assertEqual(len(consumer_events), 1)
        self.assertEqual(consumer_events[0].state, state.value)
        return consumer_events[0]

    def test_unit_test_request_mechanism(self) -> None:
        _response: Any = None

        class RequestHandler(SimpleHTTPRequestHandler):
            def do_POST(self) -> None:
                payload_len = int(str(self.headers.get('content-length', 0)))
                payload_bytes = self.rfile.read(payload_len)
                payload = json.loads(payload_bytes.decode())
                self.send_response(200)
                self.end_headers()
                self.wfile.write('{"success": "ok"}\n'.encode())

        def call(port: int) -> None:
            nonlocal _response
            _response = requests.post(f'http://localhost:{port}/', json={"test": "toast"}, timeout=10)

        run_requests(RequestHandler, call, 10)
        self.assertEqual(_response.json()["success"], "ok")

    def test_insert_event(self) -> None:
        _events: List[Dict[str, Any]] = []

        class RequestHandler(SimpleHTTPRequestHandler):
            def do_POST(self) -> None:
                payload_len = int(str(self.headers.get('content-length', 0)))
                payload_bytes = self.rfile.read(payload_len)
                payload = json.loads(payload_bytes.decode())
                nonlocal _events
                _events.append(payload)
                self.send_response(200)
                self.end_headers()
                self.wfile.write('{"success": "ok"}\n'.encode())

        def call(port: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            }, simulate_tenant=False)

            consumer = self.create_payload(data_series['consumers'], payload={
                "external_id": "my_consumer",
                "name": "my_consumer_name",
                "target": f"http://localhost:{port}/",
                "headers": {},
                "timeout": 10,
                "retry_backoff_every": 0,
                "retry_backoff_delay": 0,
                "retry_max": 0
            })

            data_point = self.create_payload(data_series['data_points'], payload={
                'external_id': 'data_point_1',
                'payload': {}
            })

            consumer = Consumer.objects.get(id=consumer['id'])

            try_send_events(consumer, proxy_url=None, log_errors=True, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.SUCCESS)
            # try to send a second time, should only send one still
            try_send_events(consumer, proxy_url=None, log_errors=True, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.SUCCESS)

        run_requests(RequestHandler, call, 10)

        self.assertEqual(1, len(_events))


    def test_insert_event_proxied(self) -> None:
        _events: List[Dict[str, Any]] = []
        _headers: List[Dict[str, str]] = []

        class RequestHandler(SimpleHTTPRequestHandler):
            def do_POST(self) -> None:
                payload_len = int(str(self.headers.get('content-length', 0)))
                payload_bytes = self.rfile.read(payload_len)
                payload = json.loads(payload_bytes.decode())
                nonlocal _events
                _events.append(payload)
                nonlocal _headers
                _headers.append(dict(self.headers))  # type: ignore
                self.send_response(200)
                self.end_headers()
                self.wfile.write('{"success": "ok"}\n'.encode())

        def call(port: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            }, simulate_tenant=False)

            consumer = self.create_payload(data_series['consumers'], payload={
                "external_id": "my_consumer",
                "name": "my_consumer_name",
                # this should never be used
                "target": "http://potatoe.local:22/",
                "headers": {},
                "timeout": 10,
                "retry_backoff_every": 0,
                "retry_backoff_delay": 0,
                "retry_max": 0
            })

            data_point = self.create_payload(data_series['data_points'], payload={
                'external_id': 'data_point_1',
                'payload': {}
            })

            consumer = Consumer.objects.get(id=consumer['id'])

            try_send_events(consumer, proxy_url=f"http://localhost:{port}/", log_errors=True, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.SUCCESS)
            # try to send a second time, should only send one still
            try_send_events(consumer, proxy_url=f"http://localhost:{port}/", log_errors=True, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.SUCCESS)

        run_requests(RequestHandler, call, 10)

        self.assertEqual(1, len(_events))
        self.assertEqual(1, len(_headers))
        self.assertEqual("http://potatoe.local:22/", _headers[0]['x-skipper-proxied-url'])
        self.assertEqual("potatoe.local", _headers[0]['x-skipper-proxied-host'])


    def test_event_error(self) -> None:
        _events: List[Dict[str, Any]] = []

        class RequestHandler(SimpleHTTPRequestHandler):
            def do_POST(self) -> None:
                payload_len = int(str(self.headers.get('content-length', 0)))
                payload_bytes = self.rfile.read(payload_len)
                payload = json.loads(payload_bytes.decode())
                nonlocal _events
                if len(_events) == 0:
                    self.send_response(400)
                else:
                    self.send_response(200)
                _events.append(payload)
                self.end_headers()
                self.wfile.write('{"success": "ok"}\n'.encode())

        def call(port: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            }, simulate_tenant=False)

            consumer = self.create_payload(data_series['consumers'], payload={
                "external_id": "my_consumer",
                "name": "my_consumer_name",
                "target": f"http://localhost:{port}/",
                "headers": {},
                "timeout": 10,
                "retry_backoff_every": 0,
                "retry_backoff_delay": 0,
                "retry_max": 0
            })

            data_point = self.create_payload(data_series['data_points'], payload={
                'external_id': 'data_point_1',
                'payload': {}
            })

            consumer = Consumer.objects.get(id=consumer['id'])

            # first one will fail
            try_send_events(consumer, proxy_url=None, log_errors=False, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.RETRY)
            # second call should only send data
            try_send_events(consumer, proxy_url=None, log_errors=True, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.SUCCESS)
            # second time should have done it already
            try_send_events(consumer, proxy_url=None, log_errors=True, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.SUCCESS)

        run_requests(RequestHandler, call, 10)

        self.assertEqual(2, len(_events))

    def test_backoff(self) -> None:
        _events: List[Dict[str, Any]] = []

        class RequestHandler(SimpleHTTPRequestHandler):
            def do_POST(self) -> None:
                payload_len = int(str(self.headers.get('content-length', 0)))
                payload_bytes = self.rfile.read(payload_len)
                payload = json.loads(payload_bytes.decode())
                nonlocal _events
                self.send_response(400)
                _events.append(payload)
                self.end_headers()
                self.wfile.write('{"success": "ok"}\n'.encode())

        def call(port: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            }, simulate_tenant=False)

            consumer = self.create_payload(data_series['consumers'], payload={
                "external_id": "my_consumer",
                "name": "my_consumer_name",
                "target": f"http://localhost:{port}/",
                "headers": {},
                "timeout": 10,
                "retry_backoff_every": 0,
                "retry_backoff_delay": 1000000,
                "retry_max": 0
            })

            data_point = self.create_payload(data_series['data_points'], payload={
                'external_id': 'data_point_1',
                'payload': {}
            })

            consumer = Consumer.objects.get(id=consumer['id'])

            # first one will fail
            try_send_events(consumer, proxy_url=None, log_errors=False, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.RETRY)
            # second call should not send data as it should be backing off
            try_send_events(consumer, proxy_url=None, log_errors=True, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.RETRY)

        run_requests(RequestHandler, call, 10)

        self.assertEqual(1, len(_events))

    def test_max_tries(self) -> None:
        _events: List[Dict[str, Any]] = []

        class RequestHandler(SimpleHTTPRequestHandler):
            def do_POST(self) -> None:
                payload_len = int(str(self.headers.get('content-length', 0)))
                payload_bytes = self.rfile.read(payload_len)
                payload = json.loads(payload_bytes.decode())
                nonlocal _events
                self.send_response(400)
                _events.append(payload)
                self.end_headers()
                self.wfile.write('{"success": "ok"}\n'.encode())

        def call(port: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            }, simulate_tenant=False)

            consumer = self.create_payload(data_series['consumers'], payload={
                "external_id": "my_consumer",
                "name": "my_consumer_name",
                "target": f"http://localhost:{port}/",
                "headers": {},
                "timeout": 10,
                "retry_backoff_every": 0,
                "retry_backoff_delay": 0,
                "retry_max": 2
            })

            data_point = self.create_payload(data_series['data_points'], payload={
                'external_id': 'data_point_1',
                'payload': {}
            })

            consumer = Consumer.objects.get(id=consumer['id'])

            # first one will fail
            try_send_events(consumer, proxy_url=None, log_errors=False, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.RETRY)
            try_send_events(consumer, proxy_url=None, log_errors=False, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.RETRY)
            try_send_events(consumer, proxy_url=None, log_errors=False, max_events=self.max_events)
            self.assert_single_event_state(consumer, ConsumerEventState.FAILED)

            # last one should set the event to failed
            try_send_events(consumer, proxy_url=None, log_errors=True, max_events=self.max_events)
            # event should be marked as broken completely should have been stopped
            self.assert_single_event_state(consumer, ConsumerEventState.FAILED)

        run_requests(RequestHandler, call, 10)

        self.assertEqual(3, len(_events))

    def test_timeout(self) -> None:
        _events: List[Dict[str, Any]] = []

        class RequestHandler(SimpleHTTPRequestHandler):
            def do_POST(self) -> None:
                payload_len = int(str(self.headers.get('content-length', 0)))
                payload_bytes = self.rfile.read(payload_len)
                payload = json.loads(payload_bytes.decode())
                nonlocal _events
                _events.append(payload)
                time.sleep(3)
                # just crash this thing

        def call(port: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            }, simulate_tenant=False)

            consumer = self.create_payload(data_series['consumers'], payload={
                "external_id": "my_consumer",
                "name": "my_consumer_name",
                "target": f"http://localhost:{port}/",
                "headers": {},
                "timeout": 0.1,
                "retry_backoff_every": 0,
                "retry_backoff_delay": 0,
                "retry_max": 2
            })

            data_point = self.create_payload(data_series['data_points'], payload={
                'external_id': 'data_point_1',
                'payload': {}
            })

            consumer = Consumer.objects.get(id=consumer['id'])

            # first one will fail
            try_send_events(consumer, proxy_url=None, log_errors=False, max_events=self.max_events)
            consumer_event = self.assert_single_event_state(consumer, ConsumerEventState.RETRY)
            print(consumer_event.response)

        run_requests(RequestHandler, call, 10)

        self.assertEqual(1, len(_events))


class EventSystemMaxEventsTest(EventSystemTest):
    max_events = 100