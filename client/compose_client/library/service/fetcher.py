import datetime
import re
from dataclasses import replace
from typing import TypeVar, Generic, Iterable, Dict, Optional, Any, List
from urllib.parse import quote

from compose_client.library.utils.exception import ComposeClientException
from compose_client.library.service.url import replace_domain

from compose_client.library.connection.client import APIClient
from compose_client.library.connection.read import read_paginated_all, read_list, read_paginated_generator
from compose_client.library.models.definition.index import Index
from compose_client.library.models.definition.consumer import Consumer
from compose_client.library.models.definition.data_series import DataSeries
from compose_client.library.models.definition.data_series_definition import DataSeriesDefinition, DataSeriesStructure, \
    DataSeriesGroupPermissions
from compose_client.library.models.definition.datapoint import DataPoint, FileTypeContent
from compose_client.library.models.definition.dimension import Dimension
from compose_client.library.models.definition.engine import EngineDefinition, Engine, EngineSecret, \
    EngineGroupPermissions
from compose_client.library.models.definition.facts import FloatFact, StringFact, TextFact, TimestampFact, ImageFact, \
    FileFact, JsonFact, \
    BooleanFact
from compose_client.library.models.definition.group import GroupDefinition, Group, GroupPermissions
from compose_client.library.models.definition.http_endpoint import HttpEndpointDefinition, HttpEndpoint, \
    HttpEndpointGroupPermissions
from compose_client.library.models.raw.consumer import ConsumerConverter
from compose_client.library.models.raw.index import IndexConverter, RawIndex
from compose_client.library.models.raw.data_series import RawDataSeriesAPIConverter, RawDataSeries, \
    RawDataSeriesPermissionsAPIConverter
from compose_client.library.models.raw.datapoint import RawDataPointAPIConverter, RawDataPoint
from compose_client.library.models.raw.dimension import DimensionConverter, RawDimension
from compose_client.library.models.raw.engine import RawEngineAPIConverter, RawEngine, RawEngineSecretAPIConverter, \
    RawEngineGroupPermissionsAPIConverter
from compose_client.library.models.raw.facts import raw_fact_api_converter, RawFloatFact, RawTimestampFact, \
    RawStringFact, RawTextFact, \
    RawImageFact, RawFileFact, RawJsonFact, RawBooleanFact
from compose_client.library.models.raw.group import RawGroup, RawGroupAPIConverter, RawGroupPermissionsAPIConverter
from compose_client.library.models.raw.http_endpoint import RawHttpEndpoint, RawHttpEndpointAPIConverter, \
    RawHttpEndpointGroupPermissionsAPIConverter
from compose_client.library.storage.file import FileStorageAdapter
from compose_client.library.utils.types import JSONType

import json

Location = TypeVar('Location')
T = TypeVar('T')

URL = str

class ComposeBaseFetcher:
    '''Fetches definitions from a compose instance specified by a client.

    Args:
        client(:obj:`APIClient`): The client that will specify the connection used by `fetch`.
    '''
    client: APIClient

    def __init__(self, client: APIClient):
        self.client = client


class FileStorageBaseFetcher:
    '''Fetches definitions from a file storage location specified by a path.

    Uses a storage adapter to abstract away the specifics of the storage type.

    Args:
        storage_adapter(:obj:`FileStorageAdapter`): The storage adapter that will be used by `fetch`.
        path(`str`): Location of the storage file where `fetch` will read from
    '''
    storage_adapter: FileStorageAdapter
    path: str

    def __init__(self, storage_adapter: FileStorageAdapter, path: str):
        self.storage_adapter = storage_adapter
        self.path = path


class FileStorageDataSeriesDefinitionFetcher(FileStorageBaseFetcher):
    def fetch(self, *, domain_aliases: Dict[str, str] = {}, regex_filter: Optional[str] = None, external_ids: Optional[List[str]] = None) -> Iterable[DataSeriesDefinition]:
        ret = []

        for elem in self.storage_adapter.read_json(self.path):
            _definition = DataSeriesDefinition.from_dict(elem)

            if external_ids is not None and _definition.data_series.external_id not in external_ids:
                continue

            if regex_filter is None or re.fullmatch(regex_filter, _definition.data_series.external_id):
                consumers = []

                for _consumer in _definition.consumers:
                    consumers.append(replace(_consumer, target=replace_domain(
                        _consumer.target,
                        domain_aliases=domain_aliases
                    )))

                ret.append(replace(_definition, consumers=consumers))
        return ret


def _data_series_definition(client: APIClient, raw_ds_by_url: Optional[Dict[str, str]], raw_data_series: RawDataSeries,
                            domain_aliases: Dict[str, str], only_structure: bool=False) -> DataSeriesDefinition:
    raw_float_facts = read_list(client, raw_data_series.float_facts,
                                converter=raw_fact_api_converter(RawFloatFact))
    raw_string_facts = read_list(client, raw_data_series.string_facts,
                                 converter=raw_fact_api_converter(RawStringFact))
    raw_text_facts = read_list(client, raw_data_series.text_facts,
                               converter=raw_fact_api_converter(RawTextFact))
    raw_timestamp_facts = read_list(client, raw_data_series.timestamp_facts,
                                    converter=raw_fact_api_converter(RawTimestampFact))
    raw_image_facts = read_list(client, raw_data_series.image_facts,
                                converter=raw_fact_api_converter(RawImageFact))
    raw_file_facts = read_list(client, raw_data_series.file_facts,
                               converter=raw_fact_api_converter(RawFileFact))
    raw_json_facts = read_list(client, raw_data_series.json_facts,
                               converter=raw_fact_api_converter(RawJsonFact))
    raw_boolean_facts = read_list(client, raw_data_series.boolean_facts,
                                  converter=raw_fact_api_converter(RawBooleanFact))
    raw_dimensions = read_list(client, raw_data_series.dimensions,
                               converter=DimensionConverter())
    
    if only_structure:
        raw_consumers = []
    else:
        raw_consumers = read_list(client, raw_data_series.consumers,
                                ConsumerConverter())

    raw_indexes: Iterable[RawIndex] = []
    if raw_data_series.indexes is not None:
        raw_indexes = read_list(client, raw_data_series.indexes,
                                converter=IndexConverter())

    data_series = DataSeries.from_raw(raw_data_series)

    float_facts = map(FloatFact.from_raw, raw_float_facts)
    string_facts = map(StringFact.from_raw, raw_string_facts)
    text_facts = map(TextFact.from_raw, raw_text_facts)
    timestamp_facts = map(TimestampFact.from_raw, raw_timestamp_facts)
    image_facts = map(ImageFact.from_raw, raw_image_facts)
    file_facts = map(FileFact.from_raw, raw_file_facts)
    json_facts = map(JsonFact.from_raw, raw_json_facts)
    boolean_facts = map(BooleanFact.from_raw, raw_boolean_facts)

    _ds_by_url = raw_ds_by_url
    if _ds_by_url is None:
        # if we didnt get any lookup we generate it ourselves (faster for single data_series lookups)
        _ds_by_url = {}
        raw_dim: RawDimension
        converter: RawDataSeriesAPIConverter = RawDataSeriesAPIConverter()
        for raw_dim in raw_dimensions:
            if raw_dim.reference not in _ds_by_url:
                _raw_ds_json = client.get(url=raw_dim.reference)
                raw_ds = converter(_raw_ds_json)
                _ds_by_url[raw_dim.reference] = raw_ds.external_id

    dimensions = map(lambda x: Dimension.from_raw(x, _ds_by_url), raw_dimensions)
    consumers = map(lambda x: Consumer.from_raw(x, domain_aliases=domain_aliases), raw_consumers)
    indexes = map(Index.from_raw, raw_indexes)

    if only_structure:
        raw_group_permissions = []
    else:
        raw_group_permissions = read_paginated_all(client, raw_data_series.permission_group,
                                                converter=RawDataSeriesPermissionsAPIConverter())

    group_permissions = map(lambda x: DataSeriesGroupPermissions.from_raw(x), raw_group_permissions)

    data_series_definition = DataSeriesDefinition(
        data_series=data_series,
        structure=DataSeriesStructure(
            float_facts=list(float_facts),
            string_facts=list(string_facts),
            text_facts=list(text_facts),
            timestamp_facts=list(timestamp_facts),
            image_facts=list(image_facts),
            file_facts=list(file_facts),
            json_facts=list(json_facts),
            boolean_facts=list(boolean_facts),
            dimensions=list(dimensions)            
        ),
        consumers=list(consumers),
        group_permissions=list(group_permissions),
        indexes=list(indexes)
    )
    return data_series_definition


class ComposeDataSeriesDefinitionFetcher(ComposeBaseFetcher):
    def fetch(self, *, domain_aliases: Dict[str, str] = {}, regex_filter: Optional[str] = None, external_ids: Optional[List[str]] = None) -> Iterable[DataSeriesDefinition]:
        ret = []

        all_raw_data_series: Iterable[RawDataSeries]
        if external_ids is not None:
            all_raw_data_series = []
            for external_id in external_ids:
                if external_id != '':
                    all_raw_data_series += list(read_paginated_all(
                        self.client,
                        url=self.client.url(f'/api/dataseries/dataseries/?external_id={quote(external_id, safe="")}'),
                        converter=RawDataSeriesAPIConverter()
                    ))
        else:
            all_raw_data_series = read_paginated_all(
                self.client,
                url=self.client.url('/api/dataseries/dataseries/'),
                converter=RawDataSeriesAPIConverter()
            )

        raw_ds_by_url: Dict[str, str] = {
            elem.url: elem.external_id
            for elem in all_raw_data_series
        }

        for raw_data_series in all_raw_data_series:
            if regex_filter is None or re.fullmatch(regex_filter, raw_data_series.external_id):
                data_series_definition = _data_series_definition(self.client, raw_ds_by_url, raw_data_series,
                                                                 domain_aliases)
                ret.append(data_series_definition)

        return ret


class FileStorageEngineDefinitionFetcher(FileStorageBaseFetcher):
    def fetch(self, *, domain_aliases: Dict[str, str] = {}) -> Iterable[EngineDefinition]:
        ret = []

        for elem in self.storage_adapter.read_json(self.path):
            _definition = EngineDefinition.from_dict(elem)
            _definition = replace(
                _definition,
                engine=replace(
                    _definition.engine,
                    upstream=replace_domain(
                        _definition.engine.upstream,
                        domain_aliases=domain_aliases
                    )
                )
            )
            ret.append(_definition)

        return ret


class ComposeEngineDefinitionFetcher(ComposeBaseFetcher):
    def fetch(self, *, domain_aliases: Dict[str, str] = {}) -> Iterable[EngineDefinition]:
        ret = []

        all_raw_engines: Iterable[RawEngine] = read_paginated_all(
            self.client,
            url=self.client.url('/api/flow/engine/'),
            converter=RawEngineAPIConverter()
        )

        secret_converter = RawEngineSecretAPIConverter()

        for raw_engine in all_raw_engines:
            raw_engine_secret = secret_converter(self.client.get(url=raw_engine.secret))
            raw_group_permissions = read_paginated_all(self.client, raw_engine.permission_group,
                                                       converter=RawEngineGroupPermissionsAPIConverter())
            group_permissions = map(lambda x: EngineGroupPermissions.from_raw(x), raw_group_permissions)
            engine_definition = EngineDefinition(
                engine=Engine.from_raw(raw_engine, domain_aliases),
                secret=EngineSecret.from_raw(raw_engine_secret),
                group_permissions=list(group_permissions)
            )
            ret.append(engine_definition)

        return ret


class FileStorageHttpEndpointDefinitionFetcher(FileStorageBaseFetcher):
    def fetch(self) -> Iterable[HttpEndpointDefinition]:
        ret = []
        for elem in self.storage_adapter.read_json(self.path):
            ret.append(HttpEndpointDefinition.from_dict(elem))
        return ret


class ComposeHttpEndpointDefinitionFetcher(ComposeBaseFetcher):
    def fetch(self) -> Iterable[HttpEndpointDefinition]:
        ret = []

        all_raw_engines: Iterable[RawEngine] = read_paginated_all(
            self.client,
            url=self.client.url('/api/flow/engine/'),
            converter=RawEngineAPIConverter()
        )
        engine_lookup = {elem.url: elem.external_id for elem in all_raw_engines}

        all_raw_endpoints: Iterable[RawHttpEndpoint] = read_paginated_all(
            self.client,
            url=self.client.url('/api/flow/httpendpoint/'),
            converter=RawHttpEndpointAPIConverter()
        )

        for raw_endpoint in all_raw_endpoints:
            raw_group_permissions = read_paginated_all(self.client, raw_endpoint.permission_group,
                                                       converter=RawHttpEndpointGroupPermissionsAPIConverter())
            group_permissions = map(lambda x: HttpEndpointGroupPermissions.from_raw(x), raw_group_permissions)
            endpoint = HttpEndpointDefinition(
                http_endpoint=HttpEndpoint.from_raw(raw_endpoint, engine_lookup),
                group_permissions=list(group_permissions)
            )
            ret.append(endpoint)

        return ret


class FileStorageGroupDefinitionFetcher(FileStorageBaseFetcher):
    def fetch(self) -> Iterable[GroupDefinition]:
        ret = []
        for elem in self.storage_adapter.read_json(self.path):
            ret.append(GroupDefinition.from_dict(elem))
        return ret


class ComposeGroupDefinitionFetcher(ComposeBaseFetcher):
    def fetch(self) -> Iterable[GroupDefinition]:
        ret = []

        all_raw_groups: Iterable[RawGroup] = read_paginated_all(
            self.client,
            url=self.client.url('/api/common/auth/group/'),
            converter=RawGroupAPIConverter()
        )

        group_permissions_converter = RawGroupPermissionsAPIConverter()

        for raw_group in all_raw_groups:
            raw_group_permissions = group_permissions_converter(self.client.get(url=raw_group.permissions))

            engine_definition = GroupDefinition(
                group=Group.from_raw(raw_group),
                group_permissions=GroupPermissions.from_raw(raw_group_permissions)
            )
            ret.append(engine_definition)

        return ret


def get_single_data_series_definition(client: APIClient, data_series_external_id: str,
                                      domain_aliases: Dict[str, str], only_structure: bool=False) -> DataSeriesDefinition:
    all_raw_data_series: Iterable[RawDataSeries] = read_paginated_all(
        client,
        url=client.url(f'/api/dataseries/dataseries/?external_id={data_series_external_id}'),
        converter=RawDataSeriesAPIConverter()
    )

    raw_ds: Optional[RawDataSeries] = None
    for _elem in all_raw_data_series:
        if data_series_external_id == _elem.external_id:
            raw_ds = _elem

    if raw_ds is None:
        raise ComposeClientException(f'did not find DataSeries with external_id {data_series_external_id}')

    definition = _data_series_definition(client, None, raw_ds, domain_aliases, only_structure=only_structure)

    return definition


class ComposeDataPointFetcher(ComposeBaseFetcher):
    '''Fetches DataPoints from a single DataSeries with additional options.

    Args:
        client(:obj:`APIClient`): The client that will specify the connection used by `fetch`.
        data_series_external_id(`str`): The external id that specifies from which DataSeries the DataPoints should be
            fetched.
        pagesize(`int`): Size of the pages requested in the GET requests. Higher number means faster fetching, but may 
            reduce stability.
        filter(`Dict`, optional): Additional filters that will be sent as query parameters.
        external_ids(`List`, optional): If set, only DataPoints having one of the specified external IDs will be 
            fetched.
        changes_since(:obj:`datetime`, optional): If set, only DataPoints changed after the specified time are fetched.
    '''
    data_series_external_id: str
    pagesize: int
    filter: Optional[Dict[str, Any]]
    external_ids: Optional[List[str]]
    changes_since: Optional[datetime.datetime]

    def __init__(
            self,
            client: APIClient,
            data_series_external_id: str,
            pagesize: int,
            filter: Optional[Dict[str, Any]],
            external_ids: Optional[List[str]],
            changes_since: Optional[datetime.datetime]
    ):
        super().__init__(client)
        self.data_series_external_id = data_series_external_id
        self.pagesize = pagesize
        self.filter = filter
        self.external_ids = external_ids
        self.changes_since = changes_since

    def fetch(self) -> Iterable[DataPoint]:
        # domain aliases are not relevant here
        definition = get_single_data_series_definition(self.client,
                                                       data_series_external_id=self.data_series_external_id,
                                                       domain_aliases={},
                                                       only_structure=True)

        _extra_query_params_str = ''
        if self.filter is not None:
            _extra_query_params_str = f'&filter={json.dumps(self.filter)}'

        if self.changes_since is not None:
            _extra_query_params_str = f'{_extra_query_params_str}&changes_since={self.changes_since.isoformat()}'

        if self.external_ids is not None:
            _external_id_filter_str = '&'.join(map(lambda x: f'external_id={quote(x, safe="")}', self.external_ids))
            if _external_id_filter_str == '':
                # empty list was passed, dont return anything
                return
            _extra_query_params_str = f'{_extra_query_params_str}&{_external_id_filter_str}'

        all_data_points: Iterable[RawDataPoint] = read_paginated_generator(
            self.client,
            url=self.client.url(f'/api/dataseries/by-external-id/dataseries/{self.data_series_external_id}'
                                f'/datapoint/?identify_dimensions_by_external_id&pagesize={self.pagesize}'
                                f'{_extra_query_params_str}'),
            converter=RawDataPointAPIConverter(),
            data_key='data'
        )

        for elem in all_data_points:
            yield DataPoint.from_raw(elem, definition)
