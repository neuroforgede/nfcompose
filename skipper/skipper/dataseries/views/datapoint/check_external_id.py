# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.db.models import QuerySet
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from typing import Any, Optional

from skipper.core.utils.memoize import Memoize
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.storage.contract.view import EmptySerializer, \
    StorageViewAdapter
from skipper.dataseries.storage.views import storage_view_adapter
from skipper.dataseries.views.common import get_dataseries_permissions_class
from skipper.dataseries.views.contract import get_data_series_object
from skipper.dataseries.storage.contract.models import DisplayDataPoint
from skipper.core.renderers import CustomizableBrowsableAPIRendererObjectMixin, \
    CustomizableBrowsableAPIRenderer
from skipper.dataseries.views.metamodel.permissions import metamodel_base_line_permissions


class DataSeriesCheckExternalIdsView(CustomizableBrowsableAPIRendererObjectMixin,
                                     GenericAPIView,  # type: ignore
    ):
    """
    For application/json, accepts a list of regular external_ids in the body { "external_ids": [...] }

    Returns the list of external ids already present in the dataseries out of the passed list
    """

    permission_classes = [
        *metamodel_base_line_permissions,
        get_dataseries_permissions_class(DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS)
    ]

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    _storage_view_adapter: Optional[StorageViewAdapter] = None

    def __init__(self, **kwargs: Any):
        super().__init__()

        def _access_data_series(data: Any) -> Optional[DataSeries]:
            return get_data_series_object(self.kwargs, DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS, self.request)

        self.data_series_memo = Memoize(_access_data_series)

    def get_name_string(self) -> str:
        return f'{self.access_data_series().name} - Data Point Check External Id Availability'

    def access_data_series(self) -> DataSeries:
        _data_series = self.data_series_memo(())
        if _data_series is None:
            raise NotFound('dataseries not found')
        else:
            return _data_series

    def get_queryset(self) -> QuerySet[Any]:
        # check permission
        self.access_data_series()
        return self.storage_view_adapter().get_empty_queryset()

    def storage_view_adapter(self) -> StorageViewAdapter:
        if self._storage_view_adapter is None:
            self._storage_view_adapter = storage_view_adapter(self.access_data_series().get_backend_type())
        return self._storage_view_adapter

    def get_serializer_class(self) -> Any:
        return EmptySerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if 'external_ids' not in request.data:
            raise ValidationError('external_ids was not in request')
        return Response(
            self.storage_view_adapter().check_external_ids(self, request.data['external_ids']),
            status=status.HTTP_200_OK
        )
