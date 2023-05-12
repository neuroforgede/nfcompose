# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.request import Request
from typing import Optional, cast

from skipper.flow.models import HttpEndpoint, Tenant, Engine
from skipper.settings import flow_upstream_impl

_http_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]


class HttpEndpointModelTest(TestCase):

    tenant: Tenant
    user: User

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            name='tenant'
        )
        self.user = User.objects.create(
            username='nf',
            password='nf',
            email='test@neuroforge.de'
        )

    def _endpoint(self, external_id: str = '212', system: bool = False, engine: Optional[Engine] = None) -> HttpEndpoint:
        return HttpEndpoint(
            external_id=external_id,
            tenant=self.tenant,
            path='/whatever/path/may/be/here',
            method='GET',
            public=False,
            engine=engine,
            system=system
        )

    def test_private_by_default(self) -> None:
        tenant = Tenant.objects.create(
            name='other_tenant2'
        )
        for method in _http_methods:
            endpoint = HttpEndpoint.objects.create(
                external_id=method,
                tenant=tenant,
                path='some/stuff/here',
                method=method,
                system=True
            )
            self.assertEquals(False, endpoint.public)

    def test_clean_no_engine_not_system(self) -> None:
        endpoint = self._endpoint()
        with self.assertRaises(ValidationError):
            endpoint.clean()

    def test_clean_no_engine_but_system(self) -> None:
        endpoint = self._endpoint(system=True)
        endpoint.clean()

    def test_clean_engine_not_system(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.clean()

    def test_save_no_engine_not_system(self) -> None:
        endpoint = self._endpoint()
        with self.assertRaises(ValidationError):
            endpoint.save()

    def test_save_no_engine_but_system(self) -> None:
        endpoint = self._endpoint(system=True)
        endpoint.save()

    def test_save_engine_not_system(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.save()

    def test_get_upstream_with_engine_and_system_set(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://some.weird.not.global.thing.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine, system=True)
        endpoint.save()
        upstream = endpoint.get_upstream(None, None)

        self.assertEqual('http://some.weird.not.global.thing.local/', upstream)

    def test_get_public_upstream_system_no_user_no_request(self) -> None:
        endpoint = self._endpoint(system=True)
        endpoint.public = True
        endpoint.save()

        with self.assertRaises(AssertionError) as exm:
            endpoint.get_upstream(None, None)

        self.assertEqual('request is required to get an upstream property from a public system flow if no engine is set', exm.exception.args[0])

    def test_get_upstream_system_no_user_no_request(self) -> None:
        endpoint = self._endpoint(system=True)
        endpoint.save()

        with self.assertRaises(AssertionError) as exm:
            endpoint.get_upstream(None, None)

        self.assertEqual('user and request are required to get an upstream property from a system flow if no engine is set', exm.exception.args[0])

    def test_get_upstream_system_with_user_no_request(self) -> None:
        endpoint = self._endpoint(system=True)
        endpoint.save()

        with self.assertRaises(AssertionError) as exm:
            endpoint.get_upstream(self.user, None)

        self.assertEqual('user and request are required to get an upstream property from a system flow if no engine is set', exm.exception.args[0])

    def test_get_upstream_system_with_request_no_user(self) -> None:
        endpoint = self._endpoint(system=True)
        endpoint.save()

        with self.assertRaises(AssertionError) as exm:
            endpoint.get_upstream(None, cast(Request, object()))

        self.assertEqual('user and request are required to get an upstream property from a system flow if no engine is set', exm.exception.args[0])

    def test_get_public_upstream_system_with_request_no_user(self) -> None:
        endpoint = self._endpoint(system=True)
        endpoint.public = True
        endpoint.save()

        request = cast(Request, object())

        upstream = endpoint.get_upstream(None, request)

        self.assertEqual(upstream, flow_upstream_impl(self.tenant, self.user, request))

    def test_get_upstream_system(self) -> None:
        endpoint = self._endpoint(system=True)
        endpoint.save()

        request = cast(Request, object())

        upstream = endpoint.get_upstream(self.user, request)

        self.assertEqual(upstream, flow_upstream_impl(self.tenant, self.user, request))

    def test_get_upstream_with_engine(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.save()
        upstream = endpoint.get_upstream(None, None)

        self.assertEqual('http://nodered.local/', upstream)

    def test_delete_on_engine_keeps_engine_reference(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.save()

        engine.delete()

        endpoint.refresh_from_db()

        self.assertIsNotNone(endpoint.engine_id)
        self.assertEqual(engine.id, endpoint.engine_id)

        __a = endpoint.engine
        self.assertIsNotNone(__a.deleted_at)
        self.assertEqual(engine.id, __a.id)

    def test_get_upstream_with_deleted_engine(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.save()

        engine.delete()

        with self.assertRaises(AssertionError) as exm:
            endpoint.get_upstream(None, None)

        self.assertEqual('referenced engine seems to be deleted', exm.exception.args[0])

    def test_hard_delete_on_engine_keeps_engine_id(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.save()

        _engine_id = engine.id
        engine.hard_delete()

        endpoint.refresh_from_db()

        self.assertIsNotNone(endpoint.engine_id)
        self.assertEqual(_engine_id, endpoint.engine_id)

        with self.assertRaises(Engine.DoesNotExist):
            __a = endpoint.engine

    def test_get_upstream_with_hard_deleted_engine(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.save()

        engine.hard_delete()

        endpoint.refresh_from_db()

        with self.assertRaises(AssertionError) as exm:
            endpoint.get_upstream(None, None)

        self.assertEqual('referenced engine seems to not exist or was hard deleted', exm.exception.args[0])
        self.assertEqual(Engine.DoesNotExist, exm.exception.args[1].__class__)

    def test_active_endpoints_only_returns_flows_with_active_engine_after_engine_delete(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.save()

        engine.delete()

        self.assertEqual(0, len(HttpEndpoint.active_endpoints(
            tenant=self.tenant,
            method=endpoint.method,
            public=endpoint.public
        )))

    def test_active_endpoints_only_returns_flows_with_active_engine_after_engine_hard_delete(self) -> None:
        engine = Engine.objects.create(
            external_id='external_id',
            upstream='http://nodered.local/',
            tenant=self.tenant
        )
        endpoint = self._endpoint(engine=engine)
        endpoint.save()

        engine.hard_delete()

        self.assertEqual(0, len(HttpEndpoint.active_endpoints(
            tenant=self.tenant,
            method=endpoint.method,
            public=endpoint.public
        )))

    def test_external_id_uniqueness_in_full_clean(self) -> None:
        endpoint_1 = self._endpoint(external_id='1', system=True)
        endpoint_1.save()

        with self.assertRaises(ValidationError):
            endpoint_1_again = self._endpoint(external_id='1', system=True)
            endpoint_1_again.full_clean()

    def test_external_id_uniqueness_in_db(self) -> None:
        endpoint_1 = self._endpoint(external_id='1', system=True)
        endpoint_1.save()

        with self.assertRaises(IntegrityError):
            endpoint_1_again = self._endpoint(external_id='1', system=True)
            endpoint_1_again.save()

    def test_active_endpoints_has_system_flows_as_last(self) -> None:
        for i in range(0, 100):
            engine = Engine.objects.create(
                external_id=f'external_id_{i}',
                upstream=f'http://nodered{i}.local/',
                tenant=self.tenant
            )
            endpoint = self._endpoint(external_id=f'non_system_flow_{i}', engine=engine)
            endpoint.save()

        for i in range(0, 100):
            endpoint = self._endpoint(external_id=f'system_flow_{i}', system=True)
            endpoint.save()

        active_endpoints = list(HttpEndpoint.active_endpoints(
            tenant=self.tenant,
            method='GET',
            public=False
        ))

        self.assertEqual(200, len(active_endpoints))

        for i in range(0, 100):
            self.assertFalse(active_endpoints[i].system)

        for i in range(100, 200):
            self.assertTrue(active_endpoints[i].system)

