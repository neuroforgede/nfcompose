# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.core.files.storage import default_storage
from django.db import connections, transaction
from django_multitenant.utils import set_current_tenant  # type: ignore
from typing import Type, cast, Any, List, Tuple

from skipper.core.models.tenant import Tenant
from skipper.core.celery import task
from skipper.dataseries.models import hard_delete_consumer, BulkInsertTaskData
from skipper.dataseries.models.metamodel.base_fact import BaseDataSeriesFactRelation
from skipper.dataseries.models.metamodel.boolean_fact import DataSeries_BooleanFact
from skipper.dataseries.models.metamodel.consumer import DataSeries_Consumer
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
from skipper.dataseries.models.metamodel.file_fact import DataSeries_FileFact
from skipper.dataseries.models.metamodel.float_fact import DataSeries_FloatFact
from skipper.dataseries.models.metamodel.image_fact import DataSeries_ImageFact
from skipper.dataseries.models.metamodel.index import DataSeries_UserDefinedIndex
from skipper.dataseries.models.metamodel.json_fact import DataSeries_JsonFact
from skipper.dataseries.models.metamodel.string_fact import DataSeries_StringFact
from skipper.dataseries.models.metamodel.text_fact import DataSeries_TextFact
from skipper.dataseries.models.metamodel.timestamp_fact import DataSeries_TimestampFact
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.dataseries.storage.contract import StorageBackendType, FactType, file_registry
from skipper.dataseries.storage.contract.file_registry import HistoryDataPointIdentifier
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name, \
    materialized_flat_history_table_name
from skipper.dataseries.storage.dynamic_sql.tasks.common import get_or_fail
from skipper.dataseries.storage.dynamic_sql.tasks.ddl import fact as fact_ddl
from skipper.dataseries.storage.dynamic_sql.tasks.ddl import dimension as dim_ddl
from skipper.dataseries.storage.dynamic_sql.tasks.ddl import user_defined_index as index_ddl
from skipper.dataseries.storage.static_ds_information import dead_facts
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor


def generate_prune_query_for_dp_relations(
        fact_or_dim_id_column: str,
        data_point_id_column: str,
        table_name: str,
        returning_deleted_identifier: bool = False
) -> str:
    query =  f"""
    DELETE FROM {escape.escape(table_name)} to_delete
    USING {escape.escape(table_name)} as tbl
    LEFT OUTER JOIN "_3_data_point" dp ON (
            dp.point_in_time = tbl.point_in_time
        AND            dp.id = tbl.data_point_id
    )
    WHERE (
        -- query only for the actual dimension or fact in question
            to_delete.{fact_or_dim_id_column} = %(ds_fact_dim_id)s
        AND       tbl.{fact_or_dim_id_column} = %(ds_fact_dim_id)s AND
        -- map between tbl and to_delete by the complex primary key
                      to_delete.point_in_time = tbl.point_in_time
        AND  to_delete.{data_point_id_column} = tbl.{data_point_id_column}
        -- delete all those that have no dp attached anymore
        AND dp.id is NULL
    )
    """
    if returning_deleted_identifier:
        query = f"""
        {query}
        RETURNING to_delete.data_point_id, to_delete.point_in_time, to_delete.sub_clock
        """
    return query


def generate_prune_query(
        data_series_fact_or_dim_id_column: str,
        data_point_id_column: str,
        table_name: str
) -> str:
    # doing the deletion with older_than in the where statement since we dont want
    # to mess up the join
    return f"""
    DELETE FROM {escape.escape(table_name)} to_delete
    USING {escape.escape(table_name)} as tbl
    LEFT OUTER JOIN {escape.escape(table_name)} tbl2 ON (
        tbl.{data_series_fact_or_dim_id_column} = tbl2.{data_series_fact_or_dim_id_column} AND
        tbl.{data_point_id_column} = tbl2.{data_point_id_column} AND
        (tbl.point_in_time, tbl.sub_clock) < (tbl2.point_in_time, tbl2.sub_clock)
    )
    WHERE 
        (
            -- query only for the actual dimension or fact in question
            to_delete.{data_series_fact_or_dim_id_column} = %(ds_fact_dim_id)s AND
            tbl.{data_series_fact_or_dim_id_column} = %(ds_fact_dim_id)s AND
            -- map between tbl and to_delete by the complex primary key
            to_delete.point_in_time = tbl.point_in_time AND
            to_delete.{data_point_id_column} = tbl.{data_point_id_column} AND
            -- older than the given point in time
            to_delete.point_in_time < %(older_than)s AND
            tbl.point_in_time < %(older_than)s
        ) AND ((
                -- delete either when there is at least one newer entry
                tbl2.{data_point_id_column} IS NOT NULL
            ) OR (
                -- or we are deleted anyways
                to_delete.deleted = true
            )
        )
    """


def generate_prune_query_flat_history(
    schema_name: str,
    escaped_table_name: str,
    flat_history_table_name: str,
    columns_to_return: List[str],
    should_return: bool
) -> str:
    base_sql = f"""
    DELETE 
    FROM {schema_name}.{flat_history_table_name} to_delete
    USING {schema_name}.{flat_history_table_name} historical_data
    LEFT OUTER JOIN {schema_name}.{escaped_table_name} data on data.id = historical_data.id
    WHERE (
        (
            -- delete either when there is at least one newer entry
            (historical_data.point_in_time, historical_data.sub_clock) < (data.point_in_time, data.sub_clock)
            OR
            -- or the data was deleted
            data.id IS NULL
        ) AND (
            historical_data.point_in_time < %(older_than)s
        ) AND (
            (historical_data.id, historical_data.point_in_time, historical_data.sub_clock) =
                (to_delete.id, to_delete.point_in_time, to_delete.sub_clock)
        )
    )
    """
    if should_return:
        return f"""
        {base_sql}
        RETURNING {','.join(map(lambda x: f'to_delete.{x}', columns_to_return))}
        """
    else:
        return base_sql


@task(name="_3_dynamic_sql_nuke_data_series")  # type: ignore
def nuke_data_series(
        tenant_id: str,
        data_series_id: str,
        older_than: str
) -> None:
    # simply prune the meta_model and then just nuke the data_series itself
    # if we delete a data_series we implicitly also delete all relations to meta_model objects
    # so we can simply go ahead and reuse the prune history job and delete the Data_Series afterwards
    with transaction.atomic():
        _data_series_obj: DataSeries = get_or_fail(DataSeries.all_objects.filter(id=data_series_id))

        assert _data_series_obj.deleted_at is not None

        prune_meta_model(
            tenant_id=tenant_id,
            data_series_id=data_series_id,
            older_than=older_than
        )

        if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value or\
                _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            _materialized_table_name = materialized_table_name(
                id=data_series_id,
                external_id=_data_series_obj.external_id
            )
            schema_name = escaped_tenant_schema(_data_series_obj.tenant.name)
            with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                cursor.execute(
                    f"""
                    DROP TABLE IF EXISTS {schema_name}.{escape.escape(_materialized_table_name)};
                    """
                )

        if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            _materialized_flat_history_table_name = materialized_flat_history_table_name(
                id=data_series_id,
                external_id=_data_series_obj.external_id
            )
            schema_name = escaped_tenant_schema(_data_series_obj.tenant.name)
            with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                cursor.execute(
                    f"""
                    DROP TABLE IF EXISTS {schema_name}.{escape.escape(_materialized_flat_history_table_name)};
                    """
                )

        BulkInsertTaskData.objects.filter(
            data_series=_data_series_obj
        ).delete()

        _data_series_obj.hard_delete()


# FIXME: this should really be outside of the dynamic_sql backend
@task(name="_3_dynamic_sql_prune_metamodel")  # type: ignore
def prune_meta_model(
        tenant_id: str,
        data_series_id: str,
        older_than: str
) -> None:
    tenant_obj: Tenant = get_or_fail(Tenant.objects.filter(id=tenant_id))
    _escaped_tenant_schema = escaped_tenant_schema(tenant_obj.name)

    set_current_tenant(tenant_obj)

    _data_series_obj: DataSeries = get_or_fail(DataSeries.all_objects.filter(id=data_series_id))

    index_rel: DataSeries_UserDefinedIndex
    for index_rel in list(DataSeries_UserDefinedIndex.all_objects.filter(
            deleted_at__lt=older_than,
            data_series=_data_series_obj
    ).select_related('user_defined_index').all()):
        assert index_rel.deleted_at is not None
        
        backend = _data_series_obj.backend

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            index_ddl.handle_drop_user_defined_index_flat_history(
                index_id=index_rel.user_defined_index.id, 
                escaped_schema_name=_escaped_tenant_schema
            )

        if backend in (
            StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value,
            StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value
        ):
            index_ddl.handle_drop_user_defined_index_materialized(
                index_id=index_rel.user_defined_index.id, 
                escaped_schema_name=_escaped_tenant_schema
            )

        index_rel.user_defined_index.hard_delete()
        index_rel.hard_delete()

    fact_info: BaseDataSeriesFactRelation
    for fact_rel in list(dead_facts(_data_series_obj, older_than=older_than)):
        assert fact_rel.deleted_at is not None

        _type: str = cast(Any, fact_rel).type
        _type_enum: FactType = FactType(cast(Any, fact_rel).type_enum)
        backend = _data_series_obj.backend

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value or \
                backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
            schema_name = escaped_tenant_schema(tenant_obj.name)
            mat_table_name = materialized_table_name(data_series_id, _data_series_obj.external_id)
            fact_ddl.handle_drop_fact_in_materialized_table(
                escaped_table_name=escape.escape(mat_table_name),
                escaped_schema_name=schema_name,
                fact_id=fact_rel.fact.id,
                external_id=fact_rel.external_id
            )

        if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            _materialized_flat_history_table_name = materialized_flat_history_table_name(
                id=data_series_id,
                external_id=_data_series_obj.external_id
            )
            schema_name = escaped_tenant_schema(tenant_obj.name)
            fact_ddl.handle_drop_fact_in_materialized_flat_history_table(
                escaped_table_name=escape.escape(_materialized_flat_history_table_name),
                escaped_schema_name=schema_name,
                fact_id=fact_rel.fact.id,
                external_id=fact_rel.external_id
            )

        file_registry.truncate_fact_data(
            tenant_id=tenant_obj.id,
            data_series_id=data_series_id,
            fact_id=str(fact_rel.fact.id)
        )

        fact_rel.fact.hard_delete()
        fact_rel.hard_delete()

    dim_rel: DataSeries_Dimension
    for dim_rel in list(DataSeries_Dimension.all_objects.filter(
            deleted_at__lt=older_than,
            data_series=_data_series_obj
    ).select_related('dimension').all()):
        assert dim_rel.deleted_at is not None

        backend = _data_series_obj.backend

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value or \
                backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
            schema_name = escaped_tenant_schema(tenant_obj.name)
            mat_table_name = materialized_table_name(data_series_id, _data_series_obj.external_id)
            dim_ddl.handle_drop_dimension_in_materialized_table(
                escaped_table_name=escape.escape(mat_table_name),
                escaped_schema_name=schema_name,
                dimension_id=dim_rel.dimension.id,
                external_id=dim_rel.external_id
            )

        if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            _materialized_flat_history_table_name = materialized_flat_history_table_name(
                id=data_series_id,
                external_id=_data_series_obj.external_id
            )
            schema_name = escaped_tenant_schema(tenant_obj.name)
            dim_ddl.handle_drop_dimension_in_materialized_flat_history_table(
                escaped_table_name=escape.escape(_materialized_flat_history_table_name),
                escaped_schema_name=schema_name,
                dimension_id=dim_rel.dimension.id,
                external_id=dim_rel.external_id
            )

        dim_rel.dimension.hard_delete()
        dim_rel.hard_delete()

    for consumer_rel in list(DataSeries_Consumer.all_objects.filter(
            deleted_at__lt=older_than,
            data_series=_data_series_obj
    ).select_related('consumer').all()):
        assert consumer_rel.deleted_at is not None

        hard_delete_consumer(consumer=consumer_rel.consumer)


@task(name="_3_dynamic_sql_prune_history")  # type: ignore
def prune_history(
        tenant_id: str,
        data_series_id: str,
        older_than: str
) -> None:
    tenant_obj: Tenant = get_or_fail(Tenant.objects.filter(id=tenant_id))

    set_current_tenant(tenant_obj)

    _data_series_obj: DataSeries = get_or_fail(DataSeries.all_objects.filter(id=data_series_id))

    prune_queries = [generate_prune_query(
        data_series_fact_or_dim_id_column='data_series_id',
        data_point_id_column='id',
        table_name='_3_data_point'
    )]
    ds_fact_dim_ids = [
        _data_series_obj.id
    ]

    prune_minio_queries: List[str] = []
    prune_minio_ds_fact_dim_ids = []
    materialized_prune_minio_ds_fact_dim_ids: List[Tuple[str, str, str]] = []

    def handle_dims() -> None:
        dimension_ids = [elem['dimension_id'] for elem in
                         DataSeries_Dimension.all_objects.filter(data_series_id=data_series_id).values('dimension_id')]  # type: ignore
        prune_queries.extend([generate_prune_query_for_dp_relations(
            fact_or_dim_id_column='dimension_id',
            data_point_id_column='data_point_id',
            table_name='_3_data_point_dimension'
        ) for _ in dimension_ids])
        ds_fact_dim_ids.extend(dimension_ids)

    handle_dims()

    def handle_facts(type: Type[BaseDataSeriesFactRelation], table_name: str) -> None:
        fact_ids = [elem['fact_id'] for elem in
                    type.all_objects.filter(data_series_id=data_series_id).values('fact_id')]  # type: ignore
        prune_queries.extend([generate_prune_query_for_dp_relations(
            fact_or_dim_id_column='fact_id',
            data_point_id_column='data_point_id',
            table_name=table_name
        ) for _ in fact_ids])
        ds_fact_dim_ids.extend(fact_ids)

    def handle_minio_facts(type: Type[BaseDataSeriesFactRelation], table_name: str, fact_type: str) -> None:
        fact_ids = [
            (elem['fact_id'], elem['external_id'])
            for elem in
            type.all_objects.filter(
                data_series_id=data_series_id  # type: ignore
            ).values(
                'fact_id',  # type: ignore
                'external_id'
            )
        ]  # type: ignore
        prune_minio_queries.extend([generate_prune_query_for_dp_relations(
            fact_or_dim_id_column='fact_id',
            data_point_id_column='data_point_id',
            table_name=table_name,
            returning_deleted_identifier=True
        ) for _ in fact_ids])
        prune_minio_ds_fact_dim_ids.extend([elem[0] for elem in fact_ids])
        materialized_prune_minio_ds_fact_dim_ids.extend(
            [(fact_type, _fact_id[0], _fact_id[1]) for _fact_id in fact_ids])

    handle_facts(
        type=DataSeries_BooleanFact,
        table_name='_3_data_point_boolean_fact'
    )
    handle_facts(
        type=DataSeries_FloatFact,
        table_name='_3_data_point_float_fact'
    )
    handle_minio_facts(
        type=DataSeries_ImageFact,
        table_name='_3_data_point_image_fact',
        fact_type='image'
    )
    handle_minio_facts(
        type=DataSeries_FileFact,
        table_name='_3_data_point_file_fact',
        fact_type='file'
    )
    handle_facts(
        type=DataSeries_JsonFact,
        table_name='_3_data_point_json_fact'
    )
    handle_facts(
        type=DataSeries_StringFact,
        table_name='_3_data_point_string_fact'
    )
    handle_facts(
        type=DataSeries_TextFact,
        table_name='_3_data_point_text_fact'
    )
    handle_facts(
        type=DataSeries_TimestampFact,
        table_name='_3_data_point_timestamp_fact'
    )

    with transaction.atomic():
        if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value or \
                _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                schema_name = escaped_tenant_schema(tenant_obj.name)
                mat_table_name = materialized_table_name(data_series_id, _data_series_obj.external_id)

                should_return = len(materialized_prune_minio_ds_fact_dim_ids) > 0

                cursor.execute(
                    f"""
                    DELETE FROM {schema_name}.{escape.escape(mat_table_name)}
                    WHERE deleted_at IS NOT NULL
                    AND deleted_at < %(older_than)s
                    {'RETURNING id, point_in_time, sub_clock' if should_return else ''};
                    """, {
                        'older_than': older_than
                    }
                )

                # we only need to do this for the no history backend
                # the others will do the purging via the history
                if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
                    if should_return:
                        for to_delete in cursor:
                            data_point_id, point_in_time, sub_clock = to_delete
                            for fact_type, fact_id, external_id in materialized_prune_minio_ds_fact_dim_ids:
                                # TODO: do this in batches
                                file_registry.delete_all_for_datapoint(
                                    tenant_id=tenant_id,
                                    data_series_id=data_series_id,
                                    fact_id=fact_id,
                                    data_point_id=data_point_id
                                )

        if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                should_return = len(materialized_prune_minio_ds_fact_dim_ids) > 0

                schema_name = escaped_tenant_schema(tenant_obj.name)
                mat_table_name = escape.escape(materialized_table_name(data_series_id, _data_series_obj.external_id))
                mat_flat_history_table_name = escape.escape(
                    materialized_flat_history_table_name(
                        data_series_id,
                        _data_series_obj.external_id
                    )
                )

                prune_sql = generate_prune_query_flat_history(
                    schema_name=schema_name,
                    escaped_table_name=mat_table_name,
                    flat_history_table_name=mat_flat_history_table_name,
                    columns_to_return=['id', 'point_in_time', 'sub_clock'],
                    should_return=should_return
                )

                cursor.execute(
                    prune_sql,
                    {
                        'older_than': older_than
                    }
                )
                if should_return:
                    for to_delete in cursor:
                        data_point_id, point_in_time, sub_clock = to_delete
                        for fact_id in prune_minio_ds_fact_dim_ids:
                            # TODO: do this in batches
                            file_registry.delete_all_matching(
                                tenant_id=tenant_id,
                                data_series_id=data_series_id,
                                fact_id=fact_id,
                                history_data_point_identifiers=[
                                    HistoryDataPointIdentifier(
                                        data_point_id=data_point_id,
                                        point_in_time=point_in_time,
                                        sub_clock=sub_clock
                                    )
                                ]
                            )

