# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import datetime
from abc import ABCMeta, abstractmethod
from django.db.models import QuerySet
from django.http import HttpRequest
from typing import Any, Dict, Optional, List, Type, Iterable, Protocol

from rest_framework.serializers import ModelSerializer

from skipper.dataseries.storage.contract.models import DisplayDataPoint
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.storage.contract.base import BaseDataPointModificationSerializer, BaseDataPointSerializer


class EmptySerializer(ModelSerializer[Any]):
    class Meta:
        # hack, but works
        model: Any = DisplayDataPoint
        fields: Any = []


class BaseDataSeries_DataPointViewSetBulk(Protocol):
    def get_serializer_context(self) -> Dict[str, Any]: ...
    def access_data_series(self) -> DataSeries: ...

class BaseDataSeries_DataPointViewSetWithSerialization(Protocol):
    def get_serializer(self, *args: Any, **kwargs: Any) -> Any: ...

class BaseDataSeries_DataPointViewSetCheckExternalIds(Protocol):
    def access_data_series(self) -> DataSeries: ...
   
# this should be a Protocol, but mypy doesn't support that yet
class BaseDataSeries_DataPointViewSet(Protocol):
    action: str
    skipper_base_name: str

    def access_data_series(self) -> DataSeries: ...

    def get_external_ids(self) -> Optional[List[str]]: ...

    def get_filter_value(self) -> Dict[str, Any]: ...

    def external_id_as_dimension_identifier(self) -> bool: ...

    def get_point_in_time(self) -> Optional[datetime.datetime]: ...

    def get_changes_since(self) -> Optional[datetime.datetime]: ...

    def should_include_versions(self) -> bool: ...

    def get_include_in_payload(self) -> Optional[List[str]]: ...


class StorageViewAdapter(metaclass=ABCMeta):
    """
    Contract definition that a Storage implementation needs to support in order to
    allow for the REST API to properly store data in the storage backend

    Methods may throw errors from rest_framework/exceptions.py
    to signal a HTTP Error, i.e. NotFound, MethodNotSupported, etc.
    """

    @abstractmethod
    def access_object(
            self,
            view: BaseDataSeries_DataPointViewSet,
            data_point_id: str,
            stub_enough: bool
    ) -> Any:
        """
        :param data_point_id: the id of the data_point
        :param view: the actual Django RESTframework view that this adapter is registered to
        :param stub_enough whether a stub is enough (e.g. for deletes or for checking if the datapoint exists)
        :return: the object that was found in the database or None
        """
        raise NotImplementedError()

    @abstractmethod
    def destroy_object(
            self,
            user_id: str,
            data_series_id: str,
            data_series_external_id: str,
            data_series_backend: str,
            record_source: str,
            instance: Any,
            view: BaseDataSeries_DataPointViewSet
    ) -> None:
        """
        :param user_id: the user that is deleting the object
        :param data_series_id the data_series we are deleting from
        :param data_series_backend the actual data_series backend of the data_series
                (useful if a backend implements sub-types)
        :param data_series_external_id: the external_id of the data_series
        :param record_source the record source to use for the delete operation (is a string that identifies
                where the record is coming from, e.g. 'REST API PUT')
        :param instance: the database object to delete
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def get_empty_queryset(self) -> 'QuerySet[Any]':
        """
        accesses the queryset to use for the given view (and therefore the request).
        #FIXME: improve this to use some storage agnostic way, right now we rely on the backend to do nothing nasty here
        :return: the empty queryset to use for the given viewset
        """
        raise NotImplementedError()

    @abstractmethod
    def get_serializer_class_for_update(
            self,
            should_include_versions: bool,
            point_in_time: Optional[datetime.datetime],
            data_series: DataSeries,
            partial: bool
    ) -> Type[BaseDataPointModificationSerializer]:
        raise NotImplementedError()

    @abstractmethod
    def get_serializer_class_for_display(
            self,
            should_include_versions: bool,
            data_series: DataSeries
    ) -> Type[BaseDataPointSerializer]:
        raise NotImplementedError()

    @abstractmethod
    def get_serializer_class(
            self,
            should_include_versions: bool,
            point_in_time: Optional[datetime.datetime],
            data_series: DataSeries
    ) -> Type[BaseDataPointModificationSerializer]:
        """
        returns the serializer class to use for the given view/request. This method is not always called,
        only in cases where we need an actual serializer to be present

        i.e. calling code may decide to use the following logic:

        if self.action == 'destroy':
            if self.action == 'DELETE':
                return None  # type: ignore
        if self.action == 'create_bulk':
            return None  # type: ignore
        :return: the serializer class to use for the given viewset
        """
        raise NotImplementedError()

    # pagination
    @abstractmethod
    def encode_last_id_for_pagination(
            self,
            view: BaseDataSeries_DataPointViewSet,
            db_object: Any
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_next_page_query_for_pagination(
            self,
            view: BaseDataSeries_DataPointViewSet,
            last_query: str,
            limit: int,
            request: HttpRequest
    ) -> Iterable[Any]:
        raise NotImplementedError()

    @abstractmethod
    def get_prev_page_query_for_pagination(
            self,
            view: BaseDataSeries_DataPointViewSet,
            last_query: str,
            limit: int,
            request: HttpRequest
    ) -> Optional[Iterable[Any]]:
        raise NotImplementedError()

    @abstractmethod
    def data_point_count(self, view: BaseDataSeries_DataPointViewSet) -> int:
        raise NotImplementedError()

    # custom methods
    @abstractmethod
    def create_bulk(
            self,
            view: BaseDataSeries_DataPointViewSetBulk,
            point_in_time_timestamp: float,
            user_id: str,
            record_source: str,
            batch: List[Dict[str, Any]],
            asynchronous: bool,
            sub_clock: int
    ) -> List[str]:
        raise NotImplementedError()

    @abstractmethod
    def check_external_ids(self, view: BaseDataSeries_DataPointViewSetCheckExternalIds, external_ids: List[str]) -> List[str]:
        raise NotImplementedError()

    def serialize_list(self, view: BaseDataSeries_DataPointViewSetWithSerialization, page: Any) -> List[
        Dict[str, Any]]:
        """
        transforms a given page into a json compatible format
        """
        serializer = view.get_serializer(page, many=True)
        return serializer.data  # type: ignore