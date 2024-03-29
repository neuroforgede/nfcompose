# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Type, Any

from skipper.core.tests.base import BaseDefaultTenantDBTest
from skipper.dataseries.models import DataSeries
from skipper.dataseries.models.metamodel.boolean_fact import BooleanFact, DataSeries_BooleanFact
from skipper.dataseries.models.metamodel.dimension import Dimension, DataSeries_Dimension
from skipper.dataseries.models.metamodel.file_fact import FileFact, DataSeries_FileFact
from skipper.dataseries.models.metamodel.float_fact import FloatFact, DataSeries_FloatFact
from skipper.dataseries.models.metamodel.image_fact import ImageFact, DataSeries_ImageFact
from skipper.dataseries.models.metamodel.json_fact import JsonFact, DataSeries_JsonFact
from skipper.dataseries.models.metamodel.string_fact import StringFact, DataSeries_StringFact
from skipper.dataseries.models.metamodel.text_fact import DataSeries_TextFact, TextFact


class MetaModelDataSeriesChildSoftDeletionTest(BaseDefaultTenantDBTest):

    rel_class: Type[Any]
    child_class: Type[Any]

    def _child(self) -> Any:
        return self.child_class.objects.create(
            name="child",
            optional=False
        )

    def _rel(self, data_series: Any, child: Any) -> Any:
        return self.rel_class.objects.create(
            external_id="child",
            fact=child,
            data_series=data_series
        )

    def test_double_soft_delete_from_ds(self) -> None:
        data_series = DataSeries.objects.create(
            name="ds",
            external_id="12123",
        )
        child = self._child()
        rel = self._rel(data_series=data_series, child=child)

        data_series.delete()
        data_series.refresh_from_db()
        rel.refresh_from_db()

        self.assertIsNotNone(data_series.deleted_at)
        self.assertIsNotNone(rel.deleted_at)
        self.assertEqual(data_series.deleted_at, rel.deleted_at)

        _del_at = data_series.deleted_at

        data_series.delete()
        data_series.refresh_from_db()
        rel.refresh_from_db()

        self.assertEqual(_del_at, rel.deleted_at)
        self.assertEqual(_del_at, data_series.deleted_at)

        # even if the child was marked as undeleted, this should not work
        # this tests the trigger in db
        data_series.deleted_at = None
        data_series.save()

        data_series.delete()
        data_series.refresh_from_db()
        rel.refresh_from_db()

        self.assertEqual(_del_at, rel.deleted_at)
        self.assertNotEqual(_del_at, data_series.deleted_at)

    def test_double_soft_delete_from_child(self) -> None:
        data_series = DataSeries.objects.create(
            name="ds",
            external_id="12123"
        )
        child = self._child()
        rel = self._rel(data_series=data_series, child=child)

        child.delete()
        child.refresh_from_db()
        rel.refresh_from_db()

        self.assertIsNotNone(child.deleted_at)
        self.assertIsNotNone(rel.deleted_at)
        self.assertEqual(child.deleted_at, rel.deleted_at)

        _del_at = child.deleted_at

        child.delete()
        child.refresh_from_db()
        rel.refresh_from_db()

        self.assertEqual(_del_at, rel.deleted_at)
        self.assertEqual(_del_at, child.deleted_at)

        # even if the child was marked as undeleted, this should not work
        # this tests the trigger in db
        child.deleted_at = None
        child.save()

        child.delete()
        child.refresh_from_db()
        rel.refresh_from_db()

        self.assertEqual(_del_at, rel.deleted_at)
        self.assertNotEqual(_del_at, child.deleted_at)


class FloatFactDataSeriesChildSoftDeletionTest(MetaModelDataSeriesChildSoftDeletionTest):
    child_class = FloatFact
    rel_class = DataSeries_FloatFact


class StringFactDataSeriesChildSoftDeletionTest(MetaModelDataSeriesChildSoftDeletionTest):
    child_class = StringFact
    rel_class = DataSeries_StringFact


class TextFactDataSeriesChildSoftDeletionTest(MetaModelDataSeriesChildSoftDeletionTest):
    child_class = TextFact
    rel_class = DataSeries_TextFact


class JSONFactDataSeriesChildSoftDeletionTest(MetaModelDataSeriesChildSoftDeletionTest):
    child_class = JsonFact
    rel_class = DataSeries_JsonFact


class BooleanFactDataSeriesChildSoftDeletionTest(MetaModelDataSeriesChildSoftDeletionTest):
    child_class = BooleanFact
    rel_class = DataSeries_BooleanFact


class ImageFactDataSeriesChildSoftDeletionTest(MetaModelDataSeriesChildSoftDeletionTest):
    child_class = ImageFact
    rel_class = DataSeries_ImageFact


class FileFactDataSeriesChildSoftDeletionTest(MetaModelDataSeriesChildSoftDeletionTest):
    child_class = FileFact
    rel_class = DataSeries_FileFact


class DimensionDataSeriesChildSoftDeletionTest(MetaModelDataSeriesChildSoftDeletionTest):
    child_class = Dimension
    rel_class = DataSeries_Dimension

    def _child(self) -> Any:
        _ds = DataSeries.objects.create(
            name="ds2",
            external_id="12123ss"
        )
        return self.child_class.objects.create(
            name="child",
            optional=False,
            reference=_ds
        )

    def _rel(self, data_series: Any, child: Any) -> Any:
        return self.rel_class.objects.create(
            external_id="child",
            dimension=child,
            data_series=data_series
        )


del MetaModelDataSeriesChildSoftDeletionTest
