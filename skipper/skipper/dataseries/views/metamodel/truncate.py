# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.db.models import QuerySet
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from typing import Any

from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.serializers.metamodel.data_series import \
    DataSeriesTruncateSerializer
from skipper.dataseries.storage import actions
from skipper.dataseries.views.common import get_dataseries_permissions_class
from skipper.dataseries.views.contract import get_data_series_object
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.dataseries.views.metamodel.permissions import metamodel_base_line_permissions


class DataSeriesTruncateView(
    CustomizableBrowsableAPIRendererObjectMixin,
    GenericAPIView,  # type: ignore
):
    """
    API to trigger a truncate asynchronous job.
    If triggered (simple POST with an empty json object is enough), ALL datapoints of this dataseries
    are deleted in an unrecoverable way.
    """

    permission_classes = [
        *metamodel_base_line_permissions,
        get_dataseries_permissions_class(DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES)
    ]

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    def get_name_string(self) -> str:
        _ds_object = self.get_object()
        return f'{_ds_object.name} - Truncate'

    def get_serializer_class(self) -> Any:
        return DataSeriesTruncateSerializer

    def get_queryset(self) -> QuerySet[DataSeries]:
        # check permission
        get_data_series_object(
            kwargs_object=self.kwargs,
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            request=self.request
        )
        return DataSeries.objects.none()

    def get_object(self) -> DataSeries:
        data_series = get_data_series_object(
            kwargs_object=self.kwargs,
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            request=self.request
        )
        if data_series is None:
            raise NotFound('data_series not found')
        return data_series

    def post(self, request: Request, **kwargs: str) -> Response:
        data_series = self.get_object()

        serializer_class = DataSeriesTruncateSerializer
        serializer = serializer_class(
            data=request.data,
            context=self.get_serializer_context(),
            many=False
        )
        serializer.is_valid(raise_exception=True)
        tenant = get_current_tenant()
        actions.truncate_data_series(
            tenant_id=tenant.id,
            data_series_id=str(data_series.id)
        )

        return Response()
