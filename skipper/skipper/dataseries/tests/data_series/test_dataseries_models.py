# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Optional, TypeVar, Tuple, Type, Any

from django.db import connection
from django.utils import timezone

from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseDefaultTenantDBTest
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation
from skipper.dataseries.models.metamodel.boolean_fact import BooleanFact, DataSeries_BooleanFact
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import Dimension, DataSeries_Dimension
from skipper.dataseries.models.metamodel.file_fact import FileFact, DataSeries_FileFact
from skipper.dataseries.models.metamodel.json_fact import JsonFact, DataSeries_JsonFact
from skipper.dataseries.models.metamodel.text_fact import TextFact, DataSeries_TextFact
from skipper.dataseries.models.metamodel.timestamp_fact import TimestampFact, DataSeries_TimestampFact
from skipper.dataseries.models.metamodel.string_fact import StringFact, DataSeries_StringFact
from skipper.dataseries.models.metamodel.image_fact import ImageFact, DataSeries_ImageFact
from skipper.dataseries.models.metamodel.float_fact import FloatFact, DataSeries_FloatFact
from skipper.dataseries.raw_sql import partition, limit, dbtime
from skipper.dataseries.raw_sql.tenant import tenant_schema_unescaped
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.actions import handle_create_data_series
from skipper.dataseries.storage.dynamic_sql.models.base_relation import BaseDataPointFactRelation
from skipper.dataseries.storage.dynamic_sql.models.facts.boolean_fact import DataPoint_BooleanFact, \
    WritableDataPoint_BooleanFact
from skipper.dataseries.storage.dynamic_sql.models.facts.json_fact import DataPoint_JsonFact, WritableDataPoint_JsonFact
from skipper.dataseries.storage.dynamic_sql.models.facts.text_fact import DataPoint_TextFact, WritableDataPoint_TextFact
from skipper.dataseries.storage.dynamic_sql.models.facts.timestamp_fact import DataPoint_TimestampFact, \
    WritableDataPoint_TimestampFact
from skipper.dataseries.storage.dynamic_sql.models.facts.string_fact import DataPoint_StringFact, WritableDataPoint_StringFact
from skipper.dataseries.storage.dynamic_sql.models.facts.float_fact import DataPoint_FloatFact, WritableDataPoint_FloatFact
from skipper.dataseries.storage.uuid import gen_uuid
from skipper.dataseries.storage.dynamic_sql.models.datapoint import DataPoint, WritableDataPoint
from skipper.modules import Module
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB

T = TypeVar('T')


def unwrap(obj: Optional[T]) -> T:
    assert obj is not None
    return obj


ParentType = Any
ChildType = Any
RelationType = Any


class Parent_ChildTest(BaseDefaultTenantDBTest):
    parent_class: Type[Any]
    child_class: Type[Any]
    relation_class: Type[Any]

    parent_table_name: str

    def test_child_relation_ship_create(self) -> Tuple[ParentType, ChildType, RelationType]:
        raise NotImplementedError()

    def test_child_relation_ship_delete_django(self) -> None:
        parent, child, relation = self.test_child_relation_ship_create()

        parent.delete()
        self.assertEqual(0, len(self.parent_class.objects.filter(id=parent.id).all()))
        self.assertEqual(0, len(self.relation_class.objects.filter(id=relation.id).all()))
        self.assertEqual(1, len(self.child_class.objects.filter(id=child.id).all()))

        # above was only a soft delete, so we should still be able to retrieve everything
        # if we really want to
        self.assertEqual(1, len(self.parent_class.all_objects.filter(id=parent.id).all()))
        self.assertEqual(1, len(self.relation_class.all_objects.filter(id=relation.id).all()))
        self.assertEqual(1, len(self.child_class.all_objects.filter(id=child.id).all()))

        # hard delete should wipe all data with cascading, though
        parent.hard_delete()
        self.assertEqual(0, len(self.parent_class.all_objects.filter(id=parent.id).all()))
        self.assertEqual(0, len(self.relation_class.all_objects.filter(id=relation.id).all()))
        self.assertEqual(0, len(self.child_class.all_objects.filter(id=child.id).all()))

    def test_child_relation_ship_delete_child_django(self) -> None:
        parent, child, relation = self.test_child_relation_ship_create()

        child.delete()
        self.assertEqual(1, len(self.parent_class.objects.filter(id=parent.id).all()))
        self.assertEqual(0, len(self.relation_class.objects.filter(id=relation.id).all()))
        self.assertEqual(0, len(self.child_class.objects.filter(id=child.id).all()))

        # above was only a soft delete, so we should still be able to retrieve everything
        # if we really want to
        self.assertEqual(1, len(self.parent_class.all_objects.filter(id=parent.id).all()))
        self.assertEqual(1, len(self.relation_class.all_objects.filter(id=relation.id).all()))
        self.assertEqual(1, len(self.child_class.all_objects.filter(id=child.id).all()))

        # hard delete should wipe all data with cascading, though
        child.hard_delete()
        self.assertEqual(1, len(self.parent_class.all_objects.filter(id=parent.id).all()))
        self.assertEqual(0, len(self.relation_class.all_objects.filter(id=relation.id).all()))
        self.assertEqual(0, len(self.child_class.all_objects.filter(id=child.id).all()))

    def test_child_relation_ship_delete_database(self) -> None:
        parent, child, relation = self.test_child_relation_ship_create()

        with connection.cursor() as cursor:
            cursor.execute(f'DELETE FROM {self.parent_table_name}')

        self.assertEqual(0, len(self.parent_class.objects.filter(id=parent.id).all()))
        self.assertEqual(0, len(self.relation_class.objects.filter(id=relation.id).all()))
        self.assertEqual(0, len(self.child_class.objects.filter(id=child.id).all()))

        self.assertEqual(0, len(self.parent_class.all_objects.filter(id=parent.id).all()))
        self.assertEqual(0, len(self.relation_class.all_objects.filter(id=relation.id).all()))
        self.assertEqual(0, len(self.child_class.all_objects.filter(id=child.id).all()))


class DataSeries_DimensionTest(Parent_ChildTest):
    parent_class = DataSeries
    child_class = Dimension
    relation_class = DataSeries_Dimension
    parent_table_name = f'_{str(Module.DATA_SERIES.value)}_data_series'

    def test_child_relation_ship_create(self) -> Tuple[DataSeries, Dimension, DataSeries_Dimension]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        data_series = DataSeries.objects.create(
            tenant=tenant,
            name="some_name",
            external_id='1'
        )
        data_series.save()

        data_series_2 = DataSeries.objects.create(
            tenant=tenant,
            name='ds2',
            external_id='2'
        )
        data_series_2.save()

        dimension = Dimension.objects.create(
            tenant=tenant,
            name='some_dim',
            reference=data_series_2,
            optional=False
        )
        dimension.save()

        relation = DataSeries_Dimension.objects.create(
            tenant=tenant,
            data_series=data_series,
            external_id='1',
            dimension=dimension
        )
        relation.save()

        self.assertEqual(relation.id, unwrap(data_series.dataseries_dimension_set.first()).id)
        self.assertEqual(dimension.id, unwrap(data_series.dataseries_dimension_set.first()).dimension.id)

        self.assertEqual(relation.id, dimension.dataseries_dimension.id)
        self.assertEqual(data_series.id, dimension.dataseries_dimension.data_series.id)

        return data_series, dimension, relation


class DataSeries_FloatFactTest(Parent_ChildTest):
    parent_class = DataSeries
    child_class = FloatFact
    relation_class = DataSeries_FloatFact
    parent_table_name = f'_{str(Module.DATA_SERIES.value)}_data_series'

    def test_child_relation_ship_create(self) -> Tuple[DataSeries, FloatFact, DataSeries_FloatFact]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        parent = DataSeries.objects.create(
            tenant=tenant,
            external_id='1',
            name="some_name"
        )
        parent.save()

        child = FloatFact.objects.create(
            tenant=tenant,
            name='some_fact',
            optional=True
        )
        child.save()

        relation = DataSeries_FloatFact.objects.create(
            tenant=tenant,
            external_id='1',
            data_series=parent,
            fact=child
        )
        relation.save()

        self.assertEqual(relation.id, unwrap(parent.dataseries_floatfact_set.first()).id)
        self.assertEqual(child.id, unwrap(parent.dataseries_floatfact_set.first()).fact.id)

        self.assertEqual(relation.id, child.dataseries_floatfact.id)
        self.assertEqual(parent.id, child.dataseries_floatfact.data_series.id)

        return parent, child, relation


class DataSeries_ImageFactTest(Parent_ChildTest):
    parent_class = DataSeries
    child_class = ImageFact
    relation_class = DataSeries_ImageFact
    parent_table_name = f'_{str(Module.DATA_SERIES.value)}_data_series'

    def test_child_relation_ship_create(self) -> Tuple[DataSeries, ImageFact, DataSeries_ImageFact]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        parent = DataSeries.objects.create(
            tenant=tenant,
            external_id='1',
            name="some_name"
        )
        parent.save()

        child = ImageFact.objects.create(
            tenant=tenant,
            name='some_fact',
            optional=True
        )
        child.save()

        relation = DataSeries_ImageFact.objects.create(
            tenant=tenant,
            external_id='1',
            data_series=parent,
            fact=child
        )
        relation.save()

        self.assertEqual(relation.id, unwrap(parent.dataseries_imagefact_set.first()).id)
        self.assertEqual(child.id, unwrap(parent.dataseries_imagefact_set.first()).fact.id)

        self.assertEqual(relation.id, child.dataseries_imagefact.id)
        self.assertEqual(parent.id, child.dataseries_imagefact.data_series.id)

        return parent, child, relation


class DataSeries_FileFactTest(Parent_ChildTest):
    parent_class = DataSeries
    child_class = FileFact
    relation_class = DataSeries_FileFact
    parent_table_name = f'_{str(Module.DATA_SERIES.value)}_data_series'

    def test_child_relation_ship_create(self) -> Tuple[DataSeries, FileFact, DataSeries_FileFact]:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        parent = DataSeries.objects.create(
            tenant=tenant,
            external_id='1',
            name="some_name"
        )
        parent.save()

        child = FileFact.objects.create(
            tenant=tenant,
            name='some_fact',
            optional=True
        )
        child.save()

        relation = DataSeries_FileFact.objects.create(
            tenant=tenant,
            external_id='1',
            data_series=parent,
            fact=child
        )
        relation.save()

        self.assertEqual(relation.id, unwrap(parent.dataseries_filefact_set.first()).id)
        self.assertEqual(child.id, unwrap(parent.dataseries_filefact_set.first()).fact.id)

        self.assertEqual(relation.id, child.dataseries_filefact.id)
        self.assertEqual(parent.id, child.dataseries_filefact.data_series.id)

        return parent, child, relation


class DataPointTest(BaseDefaultTenantDBTest):
    data_point: DataPoint

    def test_versioning_for_data_point_django_way(self) -> None:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        data_series = DataSeries.objects.create(
            tenant=tenant,
            name="data_series",
            external_id='1'
        )

        handle_create_data_series(data_series.id, data_series.external_id,
                                  tenant_name='123', external_id='1',
                                  backend=StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value,
                                  tenant_id=str(tenant.id))

        data_point_id = gen_uuid(
            data_series_id=data_series.id,
            external_id='1'
        )

        def assert_count(cnt: int) -> None:
            writable_data_points = list(WritableDataPoint.objects.filter(id=data_point_id).all())
            self.assertEqual(cnt, len(writable_data_points))

        idx = 0

        def create_dp() -> None:
            nonlocal idx
            self.data_point = DataPoint.objects.create(
                id=data_point_id,
                data_series_id=data_series.id,
                external_id='1',
                point_in_time=dbtime.now(),
                sub_clock=idx
            )
            idx += 1
            self.assertTrue(self.data_point.id.startswith(str(data_series.id)))
            self.assertEqual(1, len(DataPoint.objects.filter(
                id=data_point_id
            )))

        create_dp()
        assert_count(1)

        # create the data point again
        create_dp()
        assert_count(2)

        # overwriting should always work
        create_dp()
        assert_count(3)
        create_dp()
        assert_count(4)


class BaseDataPointFactTest(BaseDefaultTenantDBTest):
    data_point: DataPoint
    data_point_fact: BaseDataPointFactRelation

    fact_type: Type[BaseFact]
    data_series_fact_type: Type[BaseDataSeriesFactRelation]
    data_point_fact_type: Type[BaseDataPointFactRelation]
    writable_data_point_fact_type: Type[BaseDataPointFactRelation]

    dp_rel_table_name: str
    dp_rel_partition_base_name: str

    def get_value(self, idx: int) -> Any:
        raise NotImplementedError()

    def test_versioning_data_point_fact_django_way(self) -> None:
        tenant = Tenant.objects.create(
            name='tenant'
        )
        data_series = DataSeries.objects.create(
            tenant=tenant,
            name="data_series",
            external_id='1'
        )
        handle_create_data_series(data_series.id, data_series.external_id, tenant_name='123',
                                  external_id='1', backend=StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value,
                                  tenant_id=str(tenant.id))

        fact = self.fact_type.objects.create(
            tenant=tenant,
            name='fact',
            optional=False
        )

        partition_name = limit.limit_length(f'{self.dp_rel_partition_base_name}_{str(fact.id)}')
        partition.partition(
            table_name=self.dp_rel_table_name,
            partition_name=partition_name,
            partition_key=fact.id,
            connection_name=DATA_SERIES_DYNAMIC_SQL_DB,
            tenant=tenant
        )

        data_series_fact = self.data_series_fact_type.objects.create(
            tenant=tenant,
            data_series=data_series,
            fact=fact,
            external_id='fact'
        )

        data_point_id = gen_uuid(
            data_series_id=data_series.id,
            external_id='1'
        )

        def create_dp() -> None:
            self.data_point = DataPoint.objects.create(
                id=data_point_id,
                data_series_id=data_series.id,
                external_id='1',
                point_in_time=dbtime.now()
            )
            self.assertTrue(self.data_point.id.startswith(str(data_series.id)))

        create_dp()

        def add_fact_version(
                idx: int
        ) -> None:
            value = self.get_value(idx)
            self.data_point_fact = self.data_point_fact_type.objects.create(
                data_point_id=data_point_id,
                fact_id=fact.id,
                value=value,
                point_in_time=dbtime.now(),
                sub_clock=idx
            )
            self.assertEqual(1, len(self.data_point_fact_type.objects.filter(
                data_point_id=data_point_id,
                fact_id=fact.id,
                sub_clock=idx
            )))

        add_fact_version(1)
        self.assertEqual(1, len(self.writable_data_point_fact_type.objects.filter(
            data_point_id=data_point_id,
            fact_id=fact.id
        )))

        add_fact_version(2)
        self.assertEqual(2, len(self.writable_data_point_fact_type.objects.filter(
            data_point_id=data_point_id,
            fact_id=fact.id
        )))


class DataPointFloatFactTest(BaseDataPointFactTest):
    fact_type: Type[BaseFact] = FloatFact
    data_series_fact_type: Type[BaseDataSeriesFactRelation] = DataSeries_FloatFact
    data_point_fact_type: Type[BaseDataPointFactRelation] = DataPoint_FloatFact
    writable_data_point_fact_type: Type[BaseDataPointFactRelation] = WritableDataPoint_FloatFact

    dp_rel_table_name = '_3_data_point_float_fact'
    dp_rel_partition_base_name = '_3_dp_float_fact'

    def get_value(self, idx: int) -> Any:
        return float(idx)


class DataPointStringFactTest(BaseDataPointFactTest):
    fact_type: Type[BaseFact] = StringFact
    data_series_fact_type: Type[BaseDataSeriesFactRelation] = DataSeries_StringFact
    data_point_fact_type: Type[BaseDataPointFactRelation] = DataPoint_StringFact
    writable_data_point_fact_type: Type[BaseDataPointFactRelation] = WritableDataPoint_StringFact

    dp_rel_table_name = '_3_data_point_string_fact'
    dp_rel_partition_base_name = '_3_dp_string_fact'

    def get_value(self, idx: int) -> Any:
        return str(idx)


class DataPointTextFactTest(BaseDataPointFactTest):
    fact_type: Type[BaseFact] = TextFact
    data_series_fact_type: Type[BaseDataSeriesFactRelation] = DataSeries_TextFact
    data_point_fact_type: Type[BaseDataPointFactRelation] = DataPoint_TextFact
    writable_data_point_fact_type: Type[BaseDataPointFactRelation] = WritableDataPoint_TextFact

    dp_rel_table_name = '_3_data_point_text_fact'
    dp_rel_partition_base_name = '_3_dp_text_fact'

    def get_value(self, idx: int) -> Any:
        return str(idx)


class DataPointTimestampFactTest(BaseDataPointFactTest):
    fact_type: Type[BaseFact] = TimestampFact
    data_series_fact_type: Type[BaseDataSeriesFactRelation] = DataSeries_TimestampFact
    data_point_fact_type: Type[BaseDataPointFactRelation] = DataPoint_TimestampFact
    writable_data_point_fact_type: Type[BaseDataPointFactRelation] = WritableDataPoint_TimestampFact

    dp_rel_table_name = '_3_data_point_timestamp_fact'
    dp_rel_partition_base_name = '_3_dp_timestamp_fact'

    def get_value(self, idx: int) -> Any:
        return dbtime.now()


class DataPointJsonFactTest(BaseDataPointFactTest):
    fact_type: Type[BaseFact] = JsonFact
    data_series_fact_type: Type[BaseDataSeriesFactRelation] = DataSeries_JsonFact
    data_point_fact_type: Type[BaseDataPointFactRelation] = DataPoint_JsonFact
    writable_data_point_fact_type: Type[BaseDataPointFactRelation] = WritableDataPoint_JsonFact

    dp_rel_table_name = '_3_data_point_json_fact'
    dp_rel_partition_base_name = '_3_dp_json_fact'

    def get_value(self, idx: int) -> Any:
        return {
            'value': idx
        }


class DataPointBooleanFactTest(BaseDataPointFactTest):
    fact_type: Type[BaseFact] = BooleanFact
    data_series_fact_type: Type[BaseDataSeriesFactRelation] = DataSeries_BooleanFact
    data_point_fact_type: Type[BaseDataPointFactRelation] = DataPoint_BooleanFact
    writable_data_point_fact_type: Type[BaseDataPointFactRelation] = WritableDataPoint_BooleanFact

    dp_rel_table_name = '_3_data_point_boolean_fact'
    dp_rel_partition_base_name = '_3_dp_boolean_fact'

    def get_value(self, idx: int) -> Any:
        return True


# TODO: test for dimension relation

del Parent_ChildTest
del BaseDataPointFactTest
