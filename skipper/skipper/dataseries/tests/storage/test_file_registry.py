# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import uuid

import datetime
import pytz
from django.test import TransactionTestCase
from django.utils import timezone

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models import FileLookup
from skipper.dataseries.storage.contract import file_registry
from skipper.dataseries.storage.contract.file_registry import HistoryDataPointIdentifier


class FileLookupRegistryTest(TransactionTestCase):

    def test_register_and_file_exists(self) -> None:
        tenant = Tenant.objects.create(
            name='default_tenant'
        )
        data_series_id = uuid.uuid4()
        fact_id = uuid.uuid4()
        history_data_point_identifier = HistoryDataPointIdentifier(
            data_point_id='123',
            sub_clock=1,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )
        file_name = 'file_name'

        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=history_data_point_identifier,
            file_name=file_name
        )

        self.assertTrue(file_registry.file_exists(
            tenant_id=tenant.id,
            file_name=file_name
        ))

    def test_delete_all_matching(self) -> None:
        tenant = Tenant.objects.create(
            name='default_tenant'
        )

        data_series_id = uuid.uuid4()
        fact_id = uuid.uuid4()
        file_name = 'file_name'

        file_name_2 = 'file_name_2'

        dp_1_1 = HistoryDataPointIdentifier(
            data_point_id='dp_1',
            sub_clock=1,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )
        dp_1_2 = HistoryDataPointIdentifier(
            data_point_id='dp_1',
            sub_clock=2,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )

        dp_2 = HistoryDataPointIdentifier(
            data_point_id='dp_2',
            sub_clock=1,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )

        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_1_1,
            file_name=file_name
        )
        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_1_2,
            file_name=file_name
        )

        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_2,
            file_name=file_name_2
        )

        file_registry.delete_all_matching(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifiers=[dp_1_1]
        )

        self.assertTrue(file_registry.file_exists(
            tenant_id=tenant.id,
            file_name=file_name
        ))

        file_registry.delete_all_matching(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifiers=[dp_1_2]
        )

        self.assertFalse(file_registry.file_exists(
            tenant_id=tenant.id,
            file_name=file_name
        ))

        self.assertTrue(file_registry.file_exists(
            tenant_id=tenant.id,
            file_name=file_name_2
        ))

    def test_garbage_collect_only_deletes_actually_deleted(self) -> None:
        tenant = Tenant.objects.create(
            name='default_tenant'
        )

        data_series_id = uuid.uuid4()
        fact_id = uuid.uuid4()
        file_name = 'file_name'

        file_name_2 = 'file_name_2'

        dp_1_1 = HistoryDataPointIdentifier(
            data_point_id='dp_1',
            sub_clock=1,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )
        dp_1_2 = HistoryDataPointIdentifier(
            data_point_id='dp_1',
            sub_clock=2,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )

        dp_2 = HistoryDataPointIdentifier(
            data_point_id='dp_2',
            sub_clock=1,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )

        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_1_1,
            file_name=file_name
        )
        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_1_2,
            file_name=file_name
        )

        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_2,
            file_name=file_name_2
        )

        file_registry.delete_all_matching(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifiers=[dp_1_1]
        )

        class FailingStorage:
            def delete(self, name: str) -> None:
                raise AssertionError('should not be called at this point')

        file_registry.garbage_collect(
            storage=FailingStorage(),
            older_than=datetime.datetime.now() + timezone.timedelta(days=7)
        )

        self.assertTrue(file_registry.file_exists(
            tenant_id=tenant.id,
            file_name=file_name
        ))

        file_registry.delete_all_matching(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifiers=[dp_1_2]
        )

        class SucceedingStorage:
            def __init__(self) -> None:
                self.called = False

            def delete(self, name: str) -> None:
                self.called = True
                assert name == file_name

        succeeding_storage = SucceedingStorage()
        file_registry.garbage_collect(
            storage=succeeding_storage,
            older_than=datetime.datetime.now() + timezone.timedelta(days=7)
        )
        self.assertTrue(succeeding_storage.called)

        self.assertFalse(file_registry.file_exists(
            tenant_id=tenant.id,
            file_name=file_name
        ))

        self.assertTrue(file_registry.file_exists(
            tenant_id=tenant.id,
            file_name=file_name_2
        ))


class FileLookupIntegrationTest(TransactionTestCase):

    def test_garbage_collect_deletes_data(self) -> None:
        tenant = Tenant.objects.create(
            name='default_tenant'
        )

        data_series_id = uuid.uuid4()
        fact_id = uuid.uuid4()
        file_name = 'file_name'

        file_name_2 = 'file_name_2'

        dp_1_1 = HistoryDataPointIdentifier(
            data_point_id='dp_1',
            sub_clock=1,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )
        dp_1_2 = HistoryDataPointIdentifier(
            data_point_id='dp_1',
            sub_clock=2,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )

        dp_2 = HistoryDataPointIdentifier(
            data_point_id='dp_2',
            sub_clock=1,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )

        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_1_1,
            file_name=file_name
        )
        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_1_2,
            file_name=file_name
        )

        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=dp_2,
            file_name=file_name_2
        )

        file_registry.delete_all_matching(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifiers=[dp_1_1]
        )

        class IgnoringStorage:
            def delete(self, name: str) -> None:
                pass

        file_registry.garbage_collect(
            storage=IgnoringStorage(),
            older_than=datetime.datetime.now() + timezone.timedelta(days=7)
        )

        file_registry.delete_all_matching(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifiers=[dp_1_2]
        )
        self.assertEqual(2, FileLookup.all_objects.all().count())

        succeeding_storage = IgnoringStorage()
        file_registry.garbage_collect(
            storage=succeeding_storage,
            older_than=datetime.datetime.now() + timezone.timedelta(days=7)
        )
        self.assertEqual(1, FileLookup.all_objects.all().count())

    def test_register_creates_FileLookup_and_file_exists_works(self) -> None:
        tenant = Tenant.objects.create(
            name='default_tenant'
        )
        data_series_id = uuid.uuid4()
        fact_id = uuid.uuid4()
        history_data_point_identifier = HistoryDataPointIdentifier(
            data_point_id='123',
            sub_clock=1,
            point_in_time=datetime.datetime.now(tz=pytz.utc)
        )
        file_name = 'file_name'
        file_registry.register(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=history_data_point_identifier,
            file_name=file_name
        )

        self.assertTrue(FileLookup.objects.filter(
            tenant_id=tenant.id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            point_in_time=history_data_point_identifier.point_in_time,
            sub_clock=history_data_point_identifier.sub_clock,
            data_point_id=history_data_point_identifier.data_point_id
        ).exists())
        self.assertEqual(1, FileLookup.objects.all().count())
