# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.test import TestCase
from django_multitenant.utils import set_current_tenant  # type: ignore

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.views.contract import get_data_series_id


class GetDataSeriesIdTest(TestCase):

    tenant: Tenant
    data_series: DataSeries

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            name='tenant'
        )
        self.tenant.save()
        set_current_tenant(self.tenant)

        self.data_series = DataSeries.objects.create(
            name='my_ds',
            external_id='1',
            tenant=self.tenant
        )

        self.data_series.save()

    def tearDown(self) -> None:
        set_current_tenant(None)

    def test_get_data_series_id_regular(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }

        self.assertEquals(str(self.data_series.id), get_data_series_id(kwargs_object=kwargs))
        self.assertEquals(str(self.data_series.id), get_data_series_id(kwargs))

    def test_get_data_series_id_by_external_id(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.external_id),
            'by_external_id': True
        }

        self.assertEquals(str(self.data_series.id), get_data_series_id(kwargs_object=kwargs))
        self.assertEquals(str(self.data_series.id), get_data_series_id(kwargs))
