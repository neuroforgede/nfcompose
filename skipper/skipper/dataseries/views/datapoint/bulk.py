# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import csv

from django.db import transaction
from django.db.models import QuerySet
from formencode.variabledecode import variable_decode  # type:ignore
from rest_framework import status, parsers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import JSONParser, BaseParser
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from typing import Any, Optional, List, Dict, IO

from skipper.core.utils.memoize import Memoize
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_DATA_POINT_BULK
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.parsers.multipart import DataPointMultipartFormencodeParser
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage.contract.view import EmptySerializer, \
    StorageViewAdapter
from skipper.dataseries.storage.views import storage_view_adapter
from skipper.dataseries.views.common import get_dataseries_permissions_class
from skipper.dataseries.views.contract import get_data_series_object
from skipper.core.renderers import CustomizableBrowsableAPIRendererObjectMixin, \
    CustomizableBrowsableAPIRenderer
from skipper.dataseries.views.metamodel.permissions import metamodel_base_line_permissions


class BatchCSVParser(BaseParser):
    """
    parser that uses variable_decode to read the csv header
    and puts the resulting csv into the batch object
    """
    media_type = 'text/csv-json-formencode'

    def dictreader(self, lines: List[str]) -> csv.DictReader:  # type: ignore
        return csv.DictReader(lines)

    def parse(self, stream: IO[Any], media_type: Any = None, parser_context: Any = None) -> parsers.DataAndFiles:  # type: ignore
        lines = [line.decode('utf-8') for line in stream]
        result = list(self.dictreader(lines))

        actual_result = list(map(variable_decode, result))

        parser_context['__FILES_SUPPORTED__'] = False
        parser_context['__JSON_AS_STRING__'] = False

        return parsers.DataAndFiles({
            "batch": actual_result
        }, {})


class BatchCSVParserSemicolon(BatchCSVParser):
    media_type = 'text/csv-semicolon-json-formencode'

    def dictreader(self, lines: List[str]) -> csv.DictReader:  # type: ignore
        return csv.DictReader(lines, delimiter=';')


class DataSeriesBulkCreateView(CustomizableBrowsableAPIRendererObjectMixin,
                               GenericAPIView,  # type: ignore
    ):
    """
    For application/json, accepts a list of regular data points wrapped in an object { "batch": [...] }

    For multipart/formdata, the whole request has to be mapped into formencode compliant data,
    e.g.:

    batch-0.external_id = "1"
    batch-0.payload.some_field = 2
    batch-0.payload.some_other_field = "test"
    batch-0.payload.some_json_field = "{ \"some_json_key\": 1 }"
    batch-1.external_id = "2"

    For text/csv-json-formencode, 'batch' has to be dropped. If you want async handling, \
    you have to set the Header X-BULK-DATA-POINT-ASYNC to 'true'.
    In this setting, json fields only have limited support and can not be uploaded directly, but instead have to \
    be mapped into columns. This also means that this method of uploading data
    won't work if you json object uses either of "-", "." (as these are used to represent lists and dictionaries \
    respectively)
    Columns in text/csv-form-encode can not be set to null if they are included in the header.

    Async mode does not have the same guarantees as synchronous mode and should only be used either when doing an initial
    sync that is monitored closely or when durability is not 100% needed - e.g. when listening to sensor data or storing
    events.
    """

    permission_classes = [
        *metamodel_base_line_permissions,
        get_dataseries_permissions_class(DATASERIES_PERMISSION_KEY_DATA_POINT_BULK)
    ]

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]
    parser_classes = [JSONParser, DataPointMultipartFormencodeParser, BatchCSVParser, BatchCSVParserSemicolon]

    _storage_view_adapter: Optional[StorageViewAdapter] = None

    data_series_memo: Memoize[Any, Optional[DataSeries]]

    def __init__(self, **kwargs: Any):
        super().__init__()

        def _access_data_series(data: Any) -> Optional[DataSeries]:
            return get_data_series_object(self.kwargs, DATASERIES_PERMISSION_KEY_DATA_POINT_BULK, self.request)

        self.data_series_memo = Memoize(_access_data_series)

    def get_name_string(self) -> str:
        return f'{self.access_data_series().name} - Data Point Bulk Create'

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

    @transaction.non_atomic_requests
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Accepts a list of regular data points wrapped in an object { "batch": [...] }
        """
        data = request.data

        if 'batch' not in data:
            raise ValidationError('batch was not in request data. If you are using CSV,'
                                  'check if it is formatted correctly')

        if not isinstance(data['batch'], list):
            raise ValidationError('expected batch to be a list')

        batch: List[Dict[str, Any]] = data['batch']

        _async_in_request: bool = False

        if 'HTTP_X_BULK_DATA_POINT_ASYNC' in request.META:
            _async_in_request = request.META.get('HTTP_X_BULK_DATA_POINT_ASYNC') == 'true'
        if 'async' in data:
            # async in data has precedence
            _async_in_request = bool(data['async'])

        had_files = len(request.FILES) > 0 or 'SKIPPER_REQUEST_HAD_FILES' in request.META and request.META['SKIPPER_REQUEST_HAD_FILES']

        # only allow async if files are empty
        asynchronous: bool = _async_in_request and not had_files

        created_external_ids = self.storage_view_adapter().create_bulk(
            view=self,
            point_in_time_timestamp=dbtime.now().timestamp(),
            user_id=str(self.request.user.id),
            record_source='REST API (bulk)',
            batch=batch,
            asynchronous=asynchronous,
            sub_clock=dbtime.dp_sub_clock(tenant=self.access_data_series().tenant)
        )

        return Response({
            'created_external_ids': created_external_ids
        }, status=status.HTTP_201_CREATED)
