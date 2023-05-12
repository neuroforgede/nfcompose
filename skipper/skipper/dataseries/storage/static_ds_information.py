# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import dataclasses
import uuid
from uuid import UUID

import datetime
from dataclasses import dataclass
from django.db.models import CharField, Value, QuerySet, IntegerField
from typing import NamedTuple, Dict, List, Tuple, Union, cast, Any, TypedDict, Protocol

from skipper.core.models.softdelete import SoftDeletionQuerySet
from skipper.dataseries.models.metamodel.base_fact import BaseDataSeriesFactRelation
from skipper.dataseries.models.metamodel.boolean_fact import DataSeries_BooleanFact
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
from skipper.dataseries.models.metamodel.file_fact import DataSeries_FileFact
from skipper.dataseries.models.metamodel.float_fact import DataSeries_FloatFact
from skipper.dataseries.models.metamodel.image_fact import DataSeries_ImageFact
from skipper.dataseries.models.metamodel.json_fact import DataSeries_JsonFact
from skipper.dataseries.models.metamodel.string_fact import DataSeries_StringFact
from skipper.dataseries.models.metamodel.text_fact import DataSeries_TextFact
from skipper.dataseries.models.metamodel.timestamp_fact import DataSeries_TimestampFact
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.dataseries.storage.contract import FactType, StorageBackendType
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name, materialized_column_name, \
    materialized_flat_history_table_name


class ReadOnlyFact(NamedTuple):
    id: UUID
    name: str
    optional: bool


class ReadOnlyBaseDataSeriesFactRelation(NamedTuple):
    id: str
    external_id: str
    fact: ReadOnlyFact
    point_in_time: datetime.datetime


class ReadOnlyDataSeries(NamedTuple):
    id: UUID
    schema_name: str
    main_query_table_name: str
    main_alive_filter: str
    materialized_flat_history_table_name: str
    backend: str
    locked: bool


class ReadOnlyDimension(NamedTuple):
    id: UUID
    name: str
    optional: bool
    reference: ReadOnlyDataSeries


class ReadOnlyDataSeries_Dimension(NamedTuple):
    id: str
    external_id: str
    dimension: ReadOnlyDimension
    point_in_time: datetime.datetime


class DataSeriesFactQueryInfo(NamedTuple):
    id: str
    unescaped_display_id: str
    value_column: str
    fact: ReadOnlyFact
    dataseries_fact: ReadOnlyBaseDataSeriesFactRelation


class DataSeriesDimensionQueryInfo(NamedTuple):
    id: str
    unescaped_display_id: str
    value_column: str
    dimension: ReadOnlyDimension
    dataseries_dimension: ReadOnlyDataSeries_Dimension


class BasicDataSeriesQueryInfoProtocol(Protocol):
    data_series_id: Union[str, uuid.UUID]
    schema_name: str
    main_query_table_name: str
    materialized_flat_history_table_name: str

    backend: str
    locked: bool


@dataclass(frozen=True)
class BasicDataSeriesQueryInfo:
    data_series_id: Union[str, uuid.UUID]
    schema_name: str
    main_query_table_name: str
    """
    the main table name, for backends that have a materialized
    table that holds the data we should use for querying.
    For most backends this is the data with the current live data.
    This can however be different based on the usage and may
    contain other table names that have a similar structure.
    """
    materialized_flat_history_table_name: str

    backend: str
    locked: bool

    main_alive_filter: str
    """
    base sql string to define the aliveness filter for the main query table in sql queries
    """


@dataclass(frozen=True)
class DataSeriesQueryInfo(BasicDataSeriesQueryInfo):
    data_series_id: Union[str, uuid.UUID]
    schema_name: str
    main_query_table_name: str
    """
    the main table name, for backends that have a materialized
    table that holds the data we should use for querying.
    For most backends this is the data with the current live data.
    This can however be different based on the usage and may
    contain other table names that have a similar structure.
    """

    backend: str
    locked: bool

    main_alive_filter: str
    """
    base sql string to define the aliveness filter for the main query table in sql queries
    """

    main_extra_fields: List[str]
    """
    additional fields to include in the query. Don't use this for complex functions.
    These will be prefixed with a table alias before usage
    """

    float_facts: Dict[str, DataSeriesFactQueryInfo]
    string_facts: Dict[str, DataSeriesFactQueryInfo]
    text_facts: Dict[str, DataSeriesFactQueryInfo]
    timestamp_facts: Dict[str, DataSeriesFactQueryInfo]
    image_facts: Dict[str, DataSeriesFactQueryInfo]
    json_facts: Dict[str, DataSeriesFactQueryInfo]
    boolean_facts: Dict[str, DataSeriesFactQueryInfo]
    dimensions: Dict[str, DataSeriesDimensionQueryInfo]
    file_facts: Dict[str, DataSeriesFactQueryInfo]


def all_facts(data_series: DataSeries) -> 'SoftDeletionQuerySet[BaseDataSeriesFactRelation]':
    big_query: 'SoftDeletionQuerySet[BaseDataSeriesFactRelation]' = cast(
        'SoftDeletionQuerySet[BaseDataSeriesFactRelation]',
        DataSeries_FloatFact.objects.none()
    )
    for __type, __type_enum, _fact_qs in [
        ('float', FactType.Float,
         DataSeries_FloatFact.all_objects
                 .filter(
             data_series=data_series
         )
                 .select_related('fact').all()),
        ('string', FactType.String,
         DataSeries_StringFact.all_objects
                 .filter(
             data_series=data_series
         )
                 .select_related('fact').all()
         ),
        ('text', FactType.Text,
         DataSeries_TextFact.all_objects
                 .filter(
             data_series=data_series
         )
                 .select_related('fact').all()),
        ('timestamp', FactType.Timestamp,
         DataSeries_TimestampFact.all_objects
                 .filter(
             data_series=data_series
         )
                 .select_related('fact').all()
         ),
        ('image', FactType.Image,
         DataSeries_ImageFact.all_objects
                 .filter(
             data_series=data_series
         )
                 .select_related('fact').all()
         ),
        ('json', FactType.JSON,
         DataSeries_JsonFact.all_objects
                 .filter(
             data_series=data_series
         )
                 .select_related('fact').all()
         ),
        ('boolean', FactType.Boolean,
         DataSeries_BooleanFact.all_objects
                 .filter(
             data_series=data_series
         )
                 .select_related('fact').all()
         ),
        ('file', FactType.File,
         DataSeries_FileFact.all_objects
                 .filter(
             data_series=data_series
         )
                 .select_related('fact').all()
         )
    ]:
        fact_qs: QuerySet = _fact_qs  # type: ignore
        big_query = big_query.union(
            fact_qs.annotate(type=Value(__type, CharField()))
                .annotate(type_enum=Value(__type_enum.value, CharField())), all=True)

    return big_query


def dead_facts(data_series: DataSeries,
               older_than: Union[str, datetime.datetime]) -> 'List[BaseDataSeriesFactRelation]':
    # TODO: return type is not proper, we have data annotated inside
    ret: 'List[BaseDataSeriesFactRelation]' = []
    for __type, __type_enum, _fact_qs in [
        ('float', FactType.Float,
         DataSeries_FloatFact.all_objects
                 .filter(
             data_series=data_series,
             deleted_at__lt=older_than
         )
                 .select_related('fact').all()),
        ('string', FactType.String,
         DataSeries_StringFact.all_objects
                 .filter(
             data_series=data_series,
             deleted_at__lt=older_than
         )
                 .select_related('fact').all()
         ),
        ('text', FactType.Text,
         DataSeries_TextFact.all_objects
                 .filter(
             data_series=data_series,
             deleted_at__lt=older_than
         )
                 .select_related('fact').all()),
        ('timestamp', FactType.Timestamp,
         DataSeries_TimestampFact.all_objects
                 .filter(
             data_series=data_series,
             deleted_at__lt=older_than
         )
                 .select_related('fact').all()
         ),
        ('image', FactType.Image,
         DataSeries_ImageFact.all_objects
                 .filter(
             data_series=data_series,
             deleted_at__lt=older_than
         )
                 .select_related('fact').all()
         ),
        ('json', FactType.JSON,
         DataSeries_JsonFact.all_objects
                 .filter(
             data_series=data_series,
             deleted_at__lt=older_than
         )
                 .select_related('fact').all()
         ),
        ('boolean', FactType.Boolean,
         DataSeries_BooleanFact.all_objects
                 .filter(
             data_series=data_series,
             deleted_at__lt=older_than
         )
                 .select_related('fact').all()
         ),
        ('file', FactType.File,
         DataSeries_FileFact.all_objects
                 .filter(
             data_series=data_series,
             deleted_at__lt=older_than
         )
                 .select_related('fact').all()
         )
    ]:
        fact_qs: QuerySet = _fact_qs  # type: ignore
        ret.extend(
            cast(List[BaseDataSeriesFactRelation],
                 list(fact_qs.annotate(
                     type=Value(__type, CharField())
                 ).annotate(
                     type_enum=Value(__type_enum.value, CharField())
                 )))
        )

    return ret


def alive_facts(data_series: DataSeries) -> 'SoftDeletionQuerySet[BaseDataSeriesFactRelation]':
    """
    data returned from this is not compatible with deleting since the actual model is not the correct one
    due to the usage of QuerySet.union
    """
    big_query: 'SoftDeletionQuerySet[BaseDataSeriesFactRelation]' = cast(
        'SoftDeletionQuerySet[BaseDataSeriesFactRelation]',
        DataSeries_FloatFact.objects.none()
    )
    for __type, __type_enum, _fact_qs in [
        ('float', FactType.Float, data_series.dataseries_floatfact_set.select_related('fact').all()),
        ('string', FactType.String, data_series.dataseries_stringfact_set.select_related('fact').all()),
        ('text', FactType.Text, data_series.dataseries_textfact_set.select_related('fact').all()),
        ('timestamp', FactType.Timestamp, data_series.dataseries_timestampfact_set.select_related('fact').all()),
        ('image', FactType.Image, data_series.dataseries_imagefact_set.select_related('fact').all()),
        ('json', FactType.JSON, data_series.dataseries_jsonfact_set.select_related('fact').all()),
        ('boolean', FactType.Boolean, data_series.dataseries_booleanfact_set.select_related('fact').all()),
        ('file', FactType.File, data_series.dataseries_filefact_set.select_related('fact').all())
    ]:
        fact_qs: QuerySet = _fact_qs  # type: ignore
        big_query = big_query.union(
            fact_qs.annotate(type=Value(__type, CharField()))
                .annotate(type_enum=Value(__type_enum.value, CharField())), all=True)

    return big_query


def compute_basic_data_series_query_info(
        data_series: DataSeries
) -> BasicDataSeriesQueryInfo:
    schema_name = escaped_tenant_schema(data_series.tenant.name)
    table_name = escape.escape(materialized_table_name(str(data_series.id), data_series.external_id))
    hist_table_name = escape.escape(materialized_flat_history_table_name(str(data_series.id), data_series.external_id))

    return BasicDataSeriesQueryInfo(
        data_series_id=data_series.id,
        schema_name=schema_name,
        main_query_table_name=table_name,
        backend=data_series.backend,
        locked=data_series.locked,
        materialized_flat_history_table_name=hist_table_name,
        main_alive_filter='ds_dp.deleted_at IS NULL',
    )


def data_series_query_info_for_full_history(
        base_data_series_query_info: DataSeriesQueryInfo
) -> DataSeriesQueryInfo:
    if base_data_series_query_info.backend != StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        raise NotImplementedError()
    return dataclasses.replace(
            base_data_series_query_info,
            main_query_table_name=base_data_series_query_info.materialized_flat_history_table_name,
            main_alive_filter='1=1',
            main_extra_fields=['sub_clock', 'deleted'],
        )


def compute_data_series_query_info(
        data_series: DataSeries
) -> DataSeriesQueryInfo:
    def _dimension_ids(
            dataseries_dimension_set: 'SoftDeletionQuerySet[DataSeries_Dimension]'
    ) -> Dict[str, DataSeriesDimensionQueryInfo]:
        ret: Dict[str, DataSeriesDimensionQueryInfo] = {}
        for _dataseries_dimension in dataseries_dimension_set.all():
            _dimension = _dataseries_dimension.dimension

            ref_schema_name = escaped_tenant_schema(_dimension.reference.tenant.name)
            ref_table_name = escape.escape(
                materialized_table_name(str(_dimension.reference.id), _dimension.reference.external_id))
            ref_table_history_name = escape.escape(
                materialized_flat_history_table_name(str(_dimension.reference.id), _dimension.reference.external_id)
            )

            _read_only_dim = ReadOnlyDimension(
                id=_dimension.id,
                name=_dimension.name,
                optional=_dimension.optional,
                reference=ReadOnlyDataSeries(
                    id=_dimension.reference.id,
                    schema_name=ref_schema_name,
                    main_query_table_name=ref_table_name,
                    materialized_flat_history_table_name=ref_table_history_name,
                    backend=_dimension.reference.backend,
                    locked=_dimension.reference.locked,
                    main_alive_filter='ds_dp.deleted_at IS NULL',
                )
            )
            ret[_dataseries_dimension.external_id] = (DataSeriesDimensionQueryInfo(
                id=str(_dimension.id),
                unescaped_display_id=_dataseries_dimension.external_id,
                value_column=escape.escape(materialized_column_name(
                    _dataseries_dimension.dimension.id,
                    _dataseries_dimension.external_id
                )),
                dataseries_dimension=ReadOnlyDataSeries_Dimension(
                    id=str(_dataseries_dimension.id),
                    external_id=_dataseries_dimension.external_id,
                    point_in_time=_dataseries_dimension.point_in_time,
                    dimension=_read_only_dim
                ),
                dimension=_read_only_dim
            ))
        return ret

    def _fact_id(
            _dataseries_fact: BaseDataSeriesFactRelation
    ) -> DataSeriesFactQueryInfo:
        _fact = _dataseries_fact.fact
        _readonly_fact = ReadOnlyFact(
            id=_fact.id,
            name=_fact.name,
            optional=_fact.optional
        )
        return DataSeriesFactQueryInfo(
            id=str(_fact.id),
            unescaped_display_id=_dataseries_fact.external_id,
            value_column=escape.escape(materialized_column_name(
                _dataseries_fact.fact.id,
                _dataseries_fact.external_id
            )),
            dataseries_fact=ReadOnlyBaseDataSeriesFactRelation(
                id=str(_dataseries_fact.id),
                external_id=_dataseries_fact.external_id,
                point_in_time=_dataseries_fact.point_in_time,
                fact=_readonly_fact
            ),
            fact=_readonly_fact
        )

    schema_name = escaped_tenant_schema(data_series.tenant.name)
    table_name = escape.escape(materialized_table_name(str(data_series.id), data_series.external_id))
    hist_table_name = escape.escape(materialized_flat_history_table_name(str(data_series.id), data_series.external_id))

    big_query = alive_facts(data_series)

    ret = DataSeriesQueryInfo(
        data_series_id=data_series.id,
        schema_name=schema_name,
        main_query_table_name=table_name,
        main_extra_fields=[],
        materialized_flat_history_table_name=hist_table_name,
        backend=data_series.backend,
        locked=data_series.locked,
        float_facts={},
        string_facts={},
        text_facts={},
        timestamp_facts={},
        image_facts={},
        json_facts={},
        boolean_facts={},
        file_facts={},
        main_alive_filter='ds_dp.deleted_at IS NULL',
        dimensions=_dimension_ids(data_series.dataseries_dimension_set.select_related('dimension').all()),  # type: ignore
    )

    fact_info: BaseDataSeriesFactRelation
    for fact_info in big_query.all():
        _type: str = cast(Any, fact_info).type
        if _type == 'float':
            ret.float_facts[fact_info.external_id] = _fact_id(fact_info)
        elif _type == 'string':
            ret.string_facts[fact_info.external_id] = _fact_id(fact_info)
        elif _type == 'text':
            ret.text_facts[fact_info.external_id] = _fact_id(fact_info)
        elif _type == 'timestamp':
            ret.timestamp_facts[fact_info.external_id] = _fact_id(fact_info)
        elif _type == 'image':
            ret.image_facts[fact_info.external_id] = _fact_id(fact_info)
        elif _type == 'json':
            ret.json_facts[fact_info.external_id] = _fact_id(fact_info)
        elif _type == 'boolean':
            ret.boolean_facts[fact_info.external_id] = _fact_id(fact_info)
        elif _type == 'file':
            ret.file_facts[fact_info.external_id] = _fact_id(fact_info)
        else:
            raise AssertionError()

    return ret


UUID_str = str
ExternalID_str = str
class DataPointSerializationKeys(TypedDict):
    """
    serializable dictionary that contains the
    minimum of information about the dataseries
    required to write data to the underlying databases
    """
    float_facts: List[Tuple[UUID_str, ExternalID_str]]
    string_facts: List[Tuple[UUID_str, ExternalID_str]]
    text_facts: List[Tuple[UUID_str, ExternalID_str]]
    timestamp_facts: List[Tuple[UUID_str, ExternalID_str]]
    json_facts: List[Tuple[UUID_str, ExternalID_str]]
    image_facts: List[Tuple[UUID_str, ExternalID_str]]
    boolean_facts: List[Tuple[UUID_str, ExternalID_str]]
    file_facts: List[Tuple[UUID_str, ExternalID_str]]
    dimensions: List[Tuple[UUID_str, ExternalID_str]]


def data_point_serialization_keys(data_series_query_info: DataSeriesQueryInfo) -> DataPointSerializationKeys:
    def convert_fact_infos(fact_infos: Dict[str, DataSeriesFactQueryInfo]) -> List[Tuple[str, str]]:
        return [(external_id, str(fact_info.fact.id)) for external_id, fact_info in fact_infos.items()]

    return DataPointSerializationKeys(
        float_facts=convert_fact_infos(data_series_query_info.float_facts),
        text_facts=convert_fact_infos(data_series_query_info.text_facts),
        string_facts=convert_fact_infos(data_series_query_info.string_facts),
        timestamp_facts=convert_fact_infos(data_series_query_info.timestamp_facts),
        json_facts=convert_fact_infos(data_series_query_info.json_facts),
        image_facts=convert_fact_infos(data_series_query_info.image_facts),
        file_facts=convert_fact_infos(data_series_query_info.file_facts),
        boolean_facts=convert_fact_infos(data_series_query_info.boolean_facts),
        dimensions=[(external_id, str(dim_info.dimension.id)) for external_id, dim_info in
                    data_series_query_info.dimensions.items()]
    )
