# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import List, Optional, TypeVar

from django.utils import timezone

from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseDefaultTenantDBTest
from skipper.dataseries.models.metamodel.boolean_fact import BooleanFact
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import Dimension
from skipper.dataseries.models.metamodel.text_fact import TextFact
from skipper.dataseries.models.metamodel.image_fact import ImageFact
from skipper.dataseries.models.metamodel.file_fact import FileFact
from skipper.dataseries.models.metamodel.float_fact import FloatFact
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.actions import handle_create_data_series
from skipper.dataseries.storage.uuid import gen_uuid
from skipper.dataseries.storage.dynamic_sql.models.datapoint import DataPoint

T = TypeVar('T')


def unwrap(obj: Optional[T]) -> T:
    assert obj is not None
    return obj


class DataSeriesTest(BaseDefaultTenantDBTest):

    def test_create(self) -> List[DataSeries]:
        tenant = Tenant.objects.create(
            name='tenant'
        )

        obj1 = DataSeries.objects.create(
            tenant=tenant,
            name="some_name",
            external_id='1'
        )
        obj1.save()

        self.assertEqual(
            'some_name',
            unwrap(DataSeries.objects.filter(id=obj1.id).first()).name
        )

        count = len(DataSeries.objects.all())
        self.assertEqual(1, count)

        obj2 = DataSeries.objects.create(
            tenant=tenant,
            name="some_other_name",
            external_id='2',
        )
        obj2.save()

        count = len(DataSeries.objects.all())
        self.assertEqual(2, count)

        return [obj1, obj2]

    def test_delete(self) -> None:
        created = self.test_create()

        DataSeries.objects.filter(id=created[0].id).delete()

        count = len(DataSeries.objects.all())
        self.assertEqual(len(created) - 1, count)

        self.assertEqual(
            created[1].name,
            unwrap(DataSeries.objects.filter(id=created[1].id).first()).name
        )

    def test_update(self) -> None:
        created = self.test_create()

        created[0].name = 'some_new_name'
        created[0].save()

        self.assertEqual(
            'some_new_name',
            unwrap(DataSeries.objects.filter(id=created[0].id).first()).name
        )


class DimensionTest(BaseDefaultTenantDBTest):
    def test_orphan_create(self) -> List[Dimension]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        data_series_1 = DataSeries.objects.create(
            tenant=tenant,
            name='ds1',
            external_id='1'
        )
        data_series_1.save()

        obj1 = Dimension.objects.create(
            tenant=tenant,
            name='some_dimension_name',
            reference=data_series_1,
            optional=False
        )
        obj1.save()

        self.assertEqual(
            obj1.id,
            unwrap(Dimension.objects.filter(id=obj1.id).first()).id
        )

        count = len(Dimension.objects.all())
        self.assertEqual(1, count)

        data_series_2 = DataSeries.objects.create(
            tenant=tenant,
            external_id='2',
            name='ds1'
        )
        data_series_2.save()
        obj2 = Dimension.objects.create(
            tenant=tenant,
            name='some_other_dimension_name',
            reference=data_series_2,
            optional=False
        )
        obj2.save()

        count = len(Dimension.objects.all())
        self.assertEqual(2, count)

        return [obj1, obj2]

    def test_orphan_delete(self) -> None:
        created = self.test_orphan_create()

        Dimension.objects.filter(id=created[0].id).delete()

        count = len(Dimension.objects.all())
        self.assertEqual(len(created) - 1, count)

        self.assertEqual(
            created[1].id,
            unwrap(Dimension.objects.filter(id=created[1].id).first()).id
        )

    def test_orphan_update(self) -> None:
        created = self.test_orphan_create()

        created[0].name = 'some_new_name'
        created[0].save()

        self.assertEqual(
            'some_new_name',
            unwrap(Dimension.objects.filter(id=created[0].id).first()).name
        )


class FloatFactTest(BaseDefaultTenantDBTest):
    def test_orphan_create(self) -> List[FloatFact]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        obj1 = FloatFact.objects.create(
            tenant=tenant,
            name='some_time_dimension_name',
            optional=True
        )
        obj1.save()

        self.assertEqual(
            obj1.id,
            unwrap(FloatFact.objects.filter(id=obj1.id).first()).id
        )

        count = len(FloatFact.objects.all())
        self.assertEqual(1, count)

        obj2 = FloatFact.objects.create(
            tenant=tenant,
            name='some_other_time_dimension_name',
            optional=True
        )
        obj2.save()

        count = len(FloatFact.objects.all())
        self.assertEqual(2, count)

        return [obj1, obj2]

    def test_orphan_delete(self) -> None:
        created = self.test_orphan_create()

        FloatFact.objects.filter(id=created[0].id).delete()

        count = len(FloatFact.objects.all())
        self.assertEqual(len(created) - 1, count)

        self.assertEqual(
            created[1].id,
            unwrap(FloatFact.objects.filter(id=created[1].id).first()).id
        )

    def test_orphan_update(self) -> None:
        created = self.test_orphan_create()

        created[0].name = 'some_new_name'
        created[0].save()

        self.assertEqual(
            'some_new_name',
            unwrap(FloatFact.objects.filter(id=created[0].id).first()).name
        )

        created[1].optional = False
        created[1].save()

        self.assertEqual(
            False,
            unwrap(FloatFact.objects.filter(id=created[1].id).first()).optional
        )


class ImageFactTest(BaseDefaultTenantDBTest):
    def test_orphan_create(self) -> List[ImageFact]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        obj1 = ImageFact.objects.create(
            tenant=tenant,
            name='some_time_dimension_name',
            optional=True
        )
        obj1.save()

        self.assertEqual(
            obj1.id,
            unwrap(ImageFact.objects.filter(id=obj1.id).first()).id
        )

        count = len(ImageFact.objects.all())
        self.assertEqual(1, count)

        obj2 = ImageFact.objects.create(
            tenant=tenant,
            name='some_other_time_dimension_name',
            optional=True
        )
        obj2.save()

        count = len(ImageFact.objects.all())
        self.assertEqual(2, count)

        return [obj1, obj2]

    def test_orphan_delete(self) -> None:
        created = self.test_orphan_create()

        ImageFact.objects.filter(id=created[0].id).delete()

        count = len(ImageFact.objects.all())
        self.assertEqual(len(created) - 1, count)

        self.assertEqual(
            created[1].id,
            unwrap(ImageFact.objects.filter(id=created[1].id).first()).id
        )

    def test_orphan_update(self) -> None:
        created = self.test_orphan_create()

        created[0].name = 'some_new_name'
        created[0].save()

        self.assertEqual(
            'some_new_name',
            unwrap(ImageFact.objects.filter(id=created[0].id).first()).name
        )

        created[1].optional = False
        created[1].save()

        self.assertEqual(
            False,
            unwrap(ImageFact.objects.filter(id=created[1].id).first()).optional
        )


class TextFactTest(BaseDefaultTenantDBTest):
    def test_orphan_create(self) -> List[TextFact]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        obj1 = TextFact.objects.create(
            tenant=tenant,
            name='some_time_dimension_name',
            optional=True
        )
        obj1.save()

        self.assertEqual(
            obj1.id,
            unwrap(TextFact.objects.filter(id=obj1.id).first()).id
        )

        count = len(TextFact.objects.all())
        self.assertEqual(1, count)

        obj2 = TextFact.objects.create(
            tenant=tenant,
            name='some_other_time_dimension_name',
            optional=True
        )
        obj2.save()

        count = len(TextFact.objects.all())
        self.assertEqual(2, count)

        return [obj1, obj2]

    def test_orphan_delete(self) -> None:
        created = self.test_orphan_create()

        TextFact.objects.filter(id=created[0].id).delete()

        count = len(TextFact.objects.all())
        self.assertEqual(len(created) - 1, count)

        self.assertEqual(
            created[1].id,
            unwrap(TextFact.objects.filter(id=created[1].id).first()).id
        )

    def test_orphan_update(self) -> None:
        created = self.test_orphan_create()

        created[0].name = 'some_new_name'
        created[0].save()

        self.assertEqual(
            'some_new_name',
            unwrap(TextFact.objects.filter(id=created[0].id).first()).name
        )

        created[1].optional = False
        created[1].save()

        self.assertEqual(
            False,
            unwrap(TextFact.objects.filter(id=created[1].id).first()).optional
        )


class BooleanFactTest(BaseDefaultTenantDBTest):
    def test_orphan_create(self) -> List[BooleanFact]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        obj1 = BooleanFact.objects.create(
            tenant=tenant,
            name='some_boolean_dimension_name',
            optional=True
        )
        obj1.save()

        self.assertEqual(
            obj1.id,
            unwrap(BooleanFact.objects.filter(id=obj1.id).first()).id
        )

        count = len(BooleanFact.objects.all())
        self.assertEqual(1, count)

        obj2 = BooleanFact.objects.create(
            tenant=tenant,
            name='some_other_boolean_dimension_name',
            optional=True
        )
        obj2.save()

        count = len(BooleanFact.objects.all())
        self.assertEqual(2, count)

        return [obj1, obj2]

    def test_orphan_delete(self) -> None:
        created = self.test_orphan_create()

        BooleanFact.objects.filter(id=created[0].id).delete()

        count = len(BooleanFact.objects.all())
        self.assertEqual(len(created) - 1, count)

        self.assertEqual(
            created[1].id,
            unwrap(BooleanFact.objects.filter(id=created[1].id).first()).id
        )

    def test_orphan_update(self) -> None:
        created = self.test_orphan_create()

        created[0].name = 'some_new_name'
        created[0].save()

        self.assertEqual(
            'some_new_name',
            unwrap(BooleanFact.objects.filter(id=created[0].id).first()).name
        )

        created[1].optional = False
        created[1].save()

        self.assertEqual(
            False,
            unwrap(BooleanFact.objects.filter(id=created[1].id).first()).optional
        )


class FileFactTest(BaseDefaultTenantDBTest):
    def test_orphan_create(self) -> List[FileFact]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        obj1 = FileFact.objects.create(
            tenant=tenant,
            name='some_file_dimension_name',
            optional=True
        )
        obj1.save()

        self.assertEqual(
            obj1.id,
            unwrap(FileFact.objects.filter(id=obj1.id).first()).id
        )

        count = len(FileFact.objects.all())
        self.assertEqual(1, count)

        obj2 = FileFact.objects.create(
            tenant=tenant,
            name='some_other_file_dimension_name',
            optional=True
        )
        obj2.save()

        count = len(FileFact.objects.all())
        self.assertEqual(2, count)

        return [obj1, obj2]

    def test_orphan_delete(self) -> None:
        created = self.test_orphan_create()

        FileFact.objects.filter(id=created[0].id).delete()

        count = len(FileFact.objects.all())
        self.assertEqual(len(created) - 1, count)

        self.assertEqual(
            created[1].id,
            unwrap(FileFact.objects.filter(id=created[1].id).first()).id
        )

    def test_orphan_update(self) -> None:
        created = self.test_orphan_create()

        created[0].name = 'some_new_name'
        created[0].save()

        self.assertEqual(
            'some_new_name',
            unwrap(FileFact.objects.filter(id=created[0].id).first()).name
        )

        created[1].optional = False
        created[1].save()

        self.assertEqual(
            False,
            unwrap(FileFact.objects.filter(id=created[1].id).first()).optional
        )


class DataPointTest(BaseDefaultTenantDBTest):
    def test_orphan_create(self) -> List[DataPoint]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        ds = DataSeries.objects.create(
            tenant=tenant,
            name="some_name",
            external_id='1'
        )

        handle_create_data_series(ds.id, ds.external_id, tenant_name='123', external_id='1',
                                  backend=StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value, tenant_id=str(tenant.id))

        obj1 = DataPoint.objects.create(
            id=gen_uuid(ds.id, '1'),
            data_series_id=ds.id,
            external_id='1',
            point_in_time=dbtime.now()
        )

        self.assertEqual(
            obj1.id,
            unwrap(DataPoint.objects.filter(id=obj1.id).first()).id
        )

        count = len(DataPoint.objects.all())
        self.assertEqual(1, count)

        obj2 = DataPoint.objects.create(
            id=gen_uuid(ds.id, '2'),
            data_series_id=ds.id,
            external_id='2',
            point_in_time=dbtime.now()
        )

        count = len(DataPoint.objects.all())
        self.assertEqual(2, count)

        return [obj1, obj2]
