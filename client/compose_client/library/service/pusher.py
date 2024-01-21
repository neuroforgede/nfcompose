# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import itertools
import json
from typing import Generic, TypeVar, Iterable, List, Dict, Tuple, Any, cast, Generator, Callable, Optional
from urllib.parse import urlencode
import logging
import os
from datetime import datetime

from compose_client.library.connection.client import APIClient
from compose_client.library.connection.read import read_paginated_all
from compose_client.library.models.definition.datapoint import DataPoint
from compose_client.library.models.diff.data_series import DataSeriesDefinitionDiff, DataSeriesStructureDiff
from compose_client.library.models.diff.engine import EngineDefinitionDiff
from compose_client.library.models.diff.group import GroupDefinitionDiff
from compose_client.library.models.diff.http_endpoint import HttpEndpointDefinitionDiff
from compose_client.library.models.operation.create_data_series_view import DataSeriesCreateViewOperation
from compose_client.library.models.operation.general import ExternalIdOperation, OperationType
from compose_client.library.models.raw.data_series import RawDataSeries, RawDataSeriesAPIConverter
from compose_client.library.models.raw.engine import RawEngine, RawEngineAPIConverter
from compose_client.library.models.raw.group import RawGroup, RawGroupAPIConverter
from compose_client.library.service.fetcher import get_single_data_series_definition
from compose_client.library.models.definition.data_series_definition import DataSeriesDefinition

logger = logging.getLogger('Pusher')

Location = TypeVar('Location')
T = TypeVar('T')

URL = str

_base_path_data_series_by_external_id = '/api/dataseries/by-external-id/dataseries/'

structure_type_to_path_elem: Dict[str, str] = {
    'float_facts': 'floatfact',
    'string_facts': 'stringfact',
    'text_facts': 'textfact',
    'timestamp_facts': 'timestampfact',
    'image_facts': 'imagefact',
    'file_facts': 'filefact',
    'json_facts': 'jsonfact',
    'boolean_facts': 'booleanfact',
    'dimensions': 'dimension'
}


class BasePusher:
    '''
    Pushes to a target location.

    The target location is always the base url of the APIClient passed during init. Supports pushing lists.
    '''
    client: APIClient

    def __init__(self, client: APIClient):
        self.client = client


REST_URL = str
EXTERNAL_ID = str


def guess_mime_type(path: str) -> Optional[str]:
    try:
        import mimetypes
        mime_type, encoding = mimetypes.guess_type(path)
        return mime_type
    except:
        return None


class DataSeriesDefinitionDiffPusher(BasePusher):
    def _delete_structure_elements(
        self,
        structure_diff: DataSeriesStructureDiff,
        ds_external_id: str
    ) -> None:
        elem: ExternalIdOperation
        structure_ops_by_operation_type: Dict[OperationType, List[Tuple[str, ExternalIdOperation]]] = {
            OperationType.DELETE: [],
            OperationType.CREATE: [],
            OperationType.UPDATE: []
        }

        for key, elems in structure_diff.__dict__.items():
            for elem in elems:
                structure_ops_by_operation_type[elem.operation_type].append((key, elem))

        delete_ops = structure_ops_by_operation_type[OperationType.DELETE]
        for _type, del_op in delete_ops:
            _structure_path_elem = structure_type_to_path_elem[_type]
            self.client.delete(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{ds_external_id}/{_structure_path_elem}/{del_op.external_id}/')
            )

    def _delete_consumers(self, ds_external_id: str, data: Iterable[ExternalIdOperation]) -> None:
        return self._simple_child_migrate_delete(
            ds_external_id=ds_external_id,
            child_type='consumer',
            data=data
        )

    def _delete_indexes(self, ds_external_id: str, data: Iterable[ExternalIdOperation]) -> None:
        ds_json = self.client.get(
            url=self.client.url(f'{_base_path_data_series_by_external_id}{ds_external_id}/')
        )
        if 'indexes' in ds_json:
            return self._simple_child_migrate_delete(
                ds_external_id=ds_external_id,
                child_type='index',
                data=data
            )
        else:
            logger.info(f'Target DataSeries {ds_external_id} has no index endpoint - skipping delete application for indexes')

    def _create_update_structure_elements(
        self,
        structure_diff: DataSeriesStructureDiff,
        ds_external_id: str,
        ds_url_by_external_id: Dict[EXTERNAL_ID, REST_URL]
    ) -> None:
        elem: ExternalIdOperation
        structure_ops_by_operation_type: Dict[OperationType, List[Tuple[str, ExternalIdOperation]]] = {
            OperationType.DELETE: [],
            OperationType.CREATE: [],
            OperationType.UPDATE: []
        }

        for key, elems in structure_diff.__dict__.items():
            for elem in elems:
                structure_ops_by_operation_type[elem.operation_type].append((key, elem))

        for _type, create_op in structure_ops_by_operation_type[OperationType.CREATE]:
            _structure_path_elem = structure_type_to_path_elem[_type]
            _payload = create_op.payload
            if _type == 'dimensions':
                _payload['reference'] = ds_url_by_external_id[_payload['reference']]

            self.client.post(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{ds_external_id}/{_structure_path_elem}/'),
                data=create_op.payload
            )
        
        for _type, update_op in structure_ops_by_operation_type[OperationType.UPDATE]:
            _structure_path_elem = structure_type_to_path_elem[_type]           
            _payload = update_op.payload
            if _type == 'dimensions':
                _payload['reference'] = ds_url_by_external_id[_payload['reference']]

            self.client.patch(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{ds_external_id}/{_structure_path_elem}/{update_op.external_id}/'),
                data=update_op.payload
            )

    def _create_update_consumers(self, ds_external_id: str, data: Iterable[ExternalIdOperation]) -> None:
        return self._simple_child_migrate_create_update(
            ds_external_id=ds_external_id,
            child_type='consumer',
            data=data
        )

    def _create_update_indexes(self, ds_external_id: str, data: Iterable[ExternalIdOperation]) -> None:
        ds_json = self.client.get(
            url=self.client.url(f'{_base_path_data_series_by_external_id}{ds_external_id}/')
        )
        if 'indexes' in ds_json:
            return self._simple_child_migrate_create_update(
                ds_external_id=ds_external_id,
                child_type='index',
                data=data
            )
        else:
            logger.info(f'Target DataSeries {ds_external_id} has no index endpoint - skipping create/update application for indexes')

    def _migrate_bare_data_series(
            self,
            diffs: Iterable[DataSeriesDefinitionDiff]
    ) -> Dict[EXTERNAL_ID, REST_URL]:
        external_id_to_rest_url = {}

        ds_ops_by_operation_type: Dict[OperationType, List[ExternalIdOperation]] = {
            OperationType.DELETE: [],
            OperationType.CREATE: [],
            OperationType.UPDATE: []
        }
        for elem in diffs:
            if elem.data_series is not None:
                ds_ops_by_operation_type[
                    elem.data_series.operation_type
                ].append(elem.data_series)

        for del_op in ds_ops_by_operation_type[OperationType.DELETE]:
            self.client.delete(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{del_op.external_id}/')
            )

        for create_op in ds_ops_by_operation_type[OperationType.CREATE]:
            res_json = self.client.post(
                url=self.client.url(f'/api/dataseries/dataseries/'),
                data=create_op.payload
            )
            data_series = RawDataSeries.from_dict(res_json)
            external_id_to_rest_url[data_series.external_id] = data_series.url

        for update_op in ds_ops_by_operation_type[OperationType.UPDATE]:
            res_json = self.client.patch(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{update_op.external_id}/'),
                data=update_op.payload
            )
            data_series = RawDataSeries.from_dict(res_json)
            external_id_to_rest_url[data_series.external_id] = data_series.url

        return external_id_to_rest_url

    def _simple_child_migrate_delete(
            self,
            ds_external_id: str,
            child_type: str,
            data: Iterable[ExternalIdOperation]
    ) -> None:
        structure_ops_by_operation_type: Dict[OperationType, List[ExternalIdOperation]] = {
            OperationType.DELETE: [],
            OperationType.CREATE: [],
            OperationType.UPDATE: []
        }

        for elem in data:
            structure_ops_by_operation_type[elem.operation_type].append(elem)

        for del_op in structure_ops_by_operation_type[OperationType.DELETE]:
            self.client.delete(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{ds_external_id}/{child_type}/{del_op.external_id}/')
            )

    def _simple_child_migrate_create_update(
            self,
            ds_external_id: str,
            child_type: str,
            data: Iterable[ExternalIdOperation]
    ) -> None:
        structure_ops_by_operation_type: Dict[OperationType, List[ExternalIdOperation]] = {
            OperationType.DELETE: [],
            OperationType.CREATE: [],
            OperationType.UPDATE: []
        }

        for elem in data:
            structure_ops_by_operation_type[elem.operation_type].append(elem)

        for create_op in structure_ops_by_operation_type[OperationType.CREATE]:
            self.client.post(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{ds_external_id}/{child_type}/'),
                data=create_op.payload
            )

        for update_op in structure_ops_by_operation_type[OperationType.UPDATE]:
            self.client.patch(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{ds_external_id}/{child_type}/{update_op.external_id}/'),
                data=update_op.payload
            )

    def push(self, data: Iterable[DataSeriesDefinitionDiff]) -> None:
        # deletions
        for diff in data:
            # Created dataseries are not allowed to have deletions in them
            if diff.data_series is None or not diff.data_series.operation_type == OperationType.CREATE:
                # always delete indexes before fact delete
                self._delete_indexes(
                    ds_external_id=diff.external_id, 
                    data=diff.indexes
                )
                self._delete_structure_elements(
                    structure_diff=diff.structure, 
                    ds_external_id=diff.external_id
                )
                self._delete_consumers(
                    ds_external_id=diff.external_id, 
                    data=diff.consumers
                )

        self._migrate_bare_data_series(data)
        
        all_raw_data_series: Iterable[RawDataSeries] = read_paginated_all(
            self.client,
            url=self.client.url('/api/dataseries/dataseries/'),
            converter=RawDataSeriesAPIConverter()
        )
        ds_url_by_external_id: Dict[EXTERNAL_ID, REST_URL] = {}
        for ds in all_raw_data_series:
            ds_url_by_external_id[ds.external_id] = ds.url

        for diff in data:
            # no ops on deleted ds
            if diff.data_series is None or not diff.data_series.operation_type == OperationType.DELETE:
                self._create_update_structure_elements(
                    structure_diff=diff.structure, 
                    ds_external_id=diff.external_id, 
                    ds_url_by_external_id=ds_url_by_external_id
                )
                self._create_update_consumers(
                    ds_external_id=diff.external_id, 
                    data=diff.consumers
                )
                # always create/update indexes after fact create/update
                self._create_update_indexes(
                    ds_external_id=diff.external_id, 
                    data=diff.indexes
                )

        all_groups: Iterable[RawGroup] = read_paginated_all(
            self.client,
            url=self.client.url('/api/common/auth/group/'),
            converter=RawGroupAPIConverter()
        )
        group_id_by_name = {}
        for group in all_groups:
            group_id_by_name[group.name] = group.id

        for diff in data:
            for permission_change in diff.group_permissions:
                if permission_change.operation_type == OperationType.DELETE:
                    # deleting does not make sense, we can only ever run put, so we always have an update
                    pass
                if permission_change.operation_type == OperationType.CREATE:
                    # we cant really create, but the dataseries was not there to begin with
                    self.client.put(
                        url=self.client.url(
                            f'{_base_path_data_series_by_external_id}{diff.external_id}/permission/group/{group_id_by_name[permission_change.name]}/'),
                        data=permission_change.payload
                    )
                if permission_change.operation_type == OperationType.UPDATE:
                    self.client.put(
                        url=self.client.url(
                            f'{_base_path_data_series_by_external_id}{diff.external_id}/permission/group/{group_id_by_name[permission_change.name]}/'),
                        data=permission_change.payload
                    )


class EngineDefinitionDiffPusher(BasePusher):
    def _get_engine(self, external_id: str) -> Dict[str, Any]:
        return cast(Dict[str, Any], self.client.get(self.client.url(path=f'/api/flow/engine/?{urlencode({"external_id": external_id})}'))['results'][0])

    def push(self, data: Iterable[EngineDefinitionDiff]) -> None:
        all_groups: Iterable[RawGroup] = read_paginated_all(
            self.client,
            url=self.client.url('/api/common/auth/group/'),
            converter=RawGroupAPIConverter()
        )
        group_id_by_name = {}
        for group in all_groups:
            group_id_by_name[group.name] = group.id

        for elem in data:
            # first delete all secret
            # (not really needed as of implementation detail of the api, but better safe than sorry as it is
            # a different REST resource from the API standpoint)
            if elem.secret is not None:
                if elem.secret.operation_type == OperationType.DELETE:
                    self.client.delete(self._get_engine(elem.external_id)['secret'])

            _engine_deleted = False

            # migrate all engines
            if elem.engine is not None:
                if elem.engine.operation_type == OperationType.DELETE:
                    self.client.delete(self._get_engine(elem.external_id)['url'] + '?cascade_delete')
                    _engine_deleted = True

                if elem.engine.operation_type == OperationType.CREATE:
                    self.client.post(url=self.client.url('/api/flow/engine/'), data=elem.engine.payload)

                if elem.engine.operation_type == OperationType.UPDATE:
                    self.client.patch(url=self._get_engine(elem.external_id)['url'], data=elem.engine.payload)

            # migrate all secrets
            if elem.secret is not None:
                if elem.secret.operation_type == OperationType.CREATE:
                    # secret endpoint only supports put, because there will always be a secret
                    self.client.put(self._get_engine(elem.external_id)['secret'], data=elem.secret.payload)

                if elem.secret.operation_type == OperationType.UPDATE:
                    self.client.put(self._get_engine(elem.external_id)['secret'], data=elem.secret.payload)

            if not _engine_deleted:
                _url = self._get_engine(elem.external_id)['url']
                for permission_change in elem.group_permissions:
                    if permission_change.operation_type == OperationType.DELETE:
                        # deleting does not make sense, the only way we can ever delete is by running delete on the engine
                        # but then the data is already gone
                        pass
                    if permission_change.operation_type == OperationType.CREATE:
                        # we cant really create, but the engine was not there to begin with
                        self.client.put(
                            url=f'{_url}permission/group/{group_id_by_name[permission_change.name]}/',
                            data=permission_change.payload
                        )
                    if permission_change.operation_type == OperationType.UPDATE:
                        self.client.put(
                            url=f'{_url}permission/group/{group_id_by_name[permission_change.name]}/',
                            data=permission_change.payload
                        )


class HttpEndpointDefinitionDiffPusher(BasePusher):
    def _get_http_endpoint(self, external_id: str) -> Dict[str, Any]:
        return cast(Dict[str, Any], self.client.get(self.client.url(path=f'/api/flow/httpendpoint/?{urlencode({"external_id": external_id})}'))['results'][0])

    def push(self, data: Iterable[HttpEndpointDefinitionDiff]) -> None:
        all_groups: Iterable[RawGroup] = read_paginated_all(
            self.client,
            url=self.client.url('/api/common/auth/group/'),
            converter=RawGroupAPIConverter()
        )
        group_id_by_name = {}
        for group in all_groups:
            group_id_by_name[group.name] = group.id

        all_raw_engines: Iterable[RawEngine] = read_paginated_all(
            self.client,
            url=self.client.url('/api/flow/engine/'),
            converter=RawEngineAPIConverter()
        )
        engine_url_by_external_id: Dict[EXTERNAL_ID, REST_URL] = {}
        for engine in all_raw_engines:
            engine_url_by_external_id[engine.external_id] = engine.url

        for elem in data:
            _endpoint_deleted = False

            # migrate all http endpoints
            if elem.http_endpoint is not None:
                if elem.http_endpoint.operation_type == OperationType.DELETE:
                    self.client.delete(self._get_http_endpoint(elem.external_id)['url'])
                    _endpoint_deleted = True

                if elem.http_endpoint.operation_type == OperationType.CREATE:
                    _payload = elem.http_endpoint.payload
                    _payload['engine'] = engine_url_by_external_id[_payload['engine']]
                    self.client.post(url=self.client.url('/api/flow/httpendpoint/'), data=_payload)

                if elem.http_endpoint.operation_type == OperationType.UPDATE:
                    _payload = elem.http_endpoint.payload
                    _payload['engine'] = engine_url_by_external_id[_payload['engine']]
                    self.client.patch(url=self._get_http_endpoint(elem.external_id)['url'], data=_payload)

            if not _endpoint_deleted:
                _url = self._get_http_endpoint(elem.external_id)['url']

                for permission_change in elem.group_permissions:
                    if permission_change.operation_type == OperationType.DELETE:
                        # deleting does not make sense, the only way we can ever delete is by running delete on the httpendpoint
                        # but then the data is already gone
                        pass
                    if permission_change.operation_type == OperationType.CREATE:
                        # we cant really create, but the httpendpoint was not there to begin with
                        self.client.put(
                            url=f'{_url}permission/group/{group_id_by_name[permission_change.name]}/',
                            data=permission_change.payload
                        )
                    if permission_change.operation_type == OperationType.UPDATE:
                        self.client.put(
                            url=f'{_url}permission/group/{group_id_by_name[permission_change.name]}/',
                            data=permission_change.payload
                        )


class GroupDefinitionDiffPusher(BasePusher):
    def _get_group(self, name: str) -> Dict[str, Any]:
        return cast(Dict[str, Any], self.client.get(self.client.url(path=f'/api/common/auth/group/?{urlencode({"name": name})}'))['results'][0])

    def push(self, data: Iterable[GroupDefinitionDiff]) -> None:
        for elem in data:
            # first delete all permissions by putting the empty list
            # (not really needed as of implementation detail of the api, but better safe than sorry as it is
            # a different REST resource from the API standpoint)
            if elem.group_permissions is not None:
                if elem.group_permissions.operation_type == OperationType.DELETE:
                    self.client.put(self._get_group(elem.name)['permissions'], data={
                        "group_permissions": []
                    })

            # migrate all groups
            if elem.group is not None:
                if elem.group.operation_type == OperationType.DELETE:
                    self.client.delete(self._get_group(elem.name)['url'])

                if elem.group.operation_type == OperationType.CREATE:
                    self.client.post(url=self.client.url('/api/common/auth/group/'), data=elem.group.payload)

                if elem.group.operation_type == OperationType.UPDATE:
                    self.client.put(url=self._get_group(elem.name)['url'], data=elem.group.payload)

            if elem.group_permissions is not None:
                if elem.group_permissions.operation_type == OperationType.CREATE:
                    self.client.put(self._get_group(elem.name)['permissions'], data=elem.group_permissions.payload)

                if elem.group_permissions.operation_type == OperationType.UPDATE:
                    self.client.put(self._get_group(elem.name)['permissions'], data=elem.group_permissions.payload)


class DataSeriesCreateViewOperationPusher(BasePusher):
    def push(self, data: Iterable[DataSeriesCreateViewOperation]) -> None:
        for op in data:
            self.client.post(
                url=self.client.url(f'{_base_path_data_series_by_external_id}{op.data_series_external_id}/createview/'),
                data=op.settings.to_dict()
            )

__T = TypeVar('__T')
__U = TypeVar('__U')


def identity(x: __T) -> __T:
    return x

def chunks(iterable: Iterable[__T], size: int = 10, map_fn: Callable[[__T], Any] = lambda x: x) \
        -> Generator[Generator[List[__U], None, None], None, None]:
    iterator = iter(iterable)
    for first in iterator:  # stops when iterator is depleted
        def chunk() -> Generator[List[__U], None, None]:  # construct generator for next chunk
            yield map_fn(first)  # yield element from for loop
            for more in itertools.islice(iterator, size - 1):
                yield map_fn(more)  # yield more elements from the iterator

        yield chunk()  # in outer generator, yield next chunk


class DataPointPusher(BasePusher):
    '''Pushes DataPoints to the bulk endpoint with batch size defined in init.'''
    batch_size: int
    _dataseries_definitions: Dict[str, DataSeriesDefinition] = dict()    # {<_data_series_external_id>: {<saved_definition>}}

    def __init__(self, client: APIClient, batch_size: int):
        super().__init__(client)
        self.batch_size = batch_size

    def reset_caches(self) -> None:
        self._dataseries_definitions = dict()

    def push(self, data: Iterable[DataPoint], *, data_series_external_id: str, asynchronous: bool = False, use_dataseries_definition_cache: bool = False) -> None:
        _data_series_external_id = data_series_external_id
        _async = asynchronous

        # domain aliases are not relevant
        if not use_dataseries_definition_cache:
            definition = get_single_data_series_definition(
                self.client,
                data_series_external_id=_data_series_external_id,
                domain_aliases={},
                only_structure=True
            )
        else:
            # local copy of the dict to not have race conditions with reset_caches
            __dataseries_definitions = self._dataseries_definitions
            if not _data_series_external_id in __dataseries_definitions:
                __dataseries_definitions[_data_series_external_id] = get_single_data_series_definition(
                    self.client,
                    data_series_external_id=_data_series_external_id,
                    domain_aliases={},
                    only_structure=True
                )
                definition = __dataseries_definitions[_data_series_external_id]
            else:
                definition = __dataseries_definitions[_data_series_external_id]

        file_like_facts = {elem.external_id for elem in [*definition.structure.file_facts, *definition.structure.image_facts]}
        json_facts = {elem.external_id for elem in definition.structure.json_facts}

        has_files = len(file_like_facts) > 0

        chunk: List[DataPoint]
        for chunk in chunks(data, size=self.batch_size):  # type: ignore
            as_batch_files: Dict[str, Any] = {}
            i = 0
            if has_files:
                for elem in chunk:
                    as_batch_files[f"batch-{i}.external_id"] = (None, elem.external_id)
                    # we never deal with canonical ids in dumps, see fetcher.py
                    as_batch_files[f"batch-{i}.identify_dimensions_by_external_id"] = (None, elem.identify_dimensions_by_external_id)
                    for key, value in elem.payload.items():
                        _value: Any
                        if key in file_like_facts:
                            if isinstance(value, str):
                                _value = (value, open(value, 'rb'), guess_mime_type(value))
                            else:
                                _value = value
                        elif key in json_facts:
                            _value = (None, json.dumps(value))
                        else:
                            _value = (None, str(value))
                        as_batch_files[f"batch-{i}.payload.{key}"] = _value
                    i += 1

                self.client.post_multipart(
                    url=self.client.url(f'{_base_path_data_series_by_external_id}{_data_series_external_id}/bulk/datapoint/'),
                    data=as_batch_files
                )
            else:
                self.client.post(
                    url=self.client.url(f'{_base_path_data_series_by_external_id}{_data_series_external_id}/bulk/datapoint/'),
                    data={
                        'batch': list(map(lambda x: x.to_dict(), chunk)),  # type: ignore
                        'async': _async
                    }
                )
