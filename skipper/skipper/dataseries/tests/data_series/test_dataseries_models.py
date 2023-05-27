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
# FIXME: unit tests
from skipper.dataseries.models.metamodel.boolean_fact import BooleanFact, DataSeries_BooleanFact
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import Dimension, DataSeries_Dimension
from skipper.dataseries.models.metamodel.file_fact import FileFact, DataSeries_FileFact
# FIXME: unit tests
from skipper.dataseries.models.metamodel.json_fact import JsonFact, DataSeries_JsonFact
# FIXME: unit tests
from skipper.dataseries.models.metamodel.text_fact import TextFact, DataSeries_TextFact
# FIXME: unit tests
from skipper.dataseries.models.metamodel.timestamp_fact import TimestampFact, DataSeries_TimestampFact
# FIXME: unit tests
from skipper.dataseries.models.metamodel.string_fact import StringFact, DataSeries_StringFact
from skipper.dataseries.models.metamodel.image_fact import ImageFact, DataSeries_ImageFact
from skipper.dataseries.models.metamodel.float_fact import FloatFact, DataSeries_FloatFact
from skipper.modules import Module

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


# TODO: test for dimension relation

del Parent_ChildTest
