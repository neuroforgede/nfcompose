# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

"""
This module is intended as a central place where backends can keep track of
any files they have stored. Any files they store should be registered
"""
import uuid
from opentelemetry import trace  # type: ignore

import datetime
from dataclasses import dataclass
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction, connections
from django_multitenant.fields import TenantForeignKey  # type: ignore
from django_multitenant.mixins import TenantModelMixin  # type: ignore
from django_multitenant.models import TenantManager  # type: ignore
from typing import List, Optional, Union, Protocol, Any

from skipper.dataseries.models import FileLookup
from skipper.dataseries.raw_sql import dbtime
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.testing import SKIPPER_CELERY_TESTING
from skipper.core.lint import sql_cursor


class DeleteStorage(Protocol):
    def delete(self, name: str) -> Any: ...


class SaveStorage(Protocol):
    def save(self, name: str, file: Any) -> None: ...


@dataclass
class HistoryDataPointIdentifier:
    data_point_id: str
    point_in_time: datetime.datetime
    sub_clock: int


@dataclass
class HistoryDataPointIdentifierBulkElem:
    fact_id: Union[str, uuid.UUID]
    history_data_point_identifier: HistoryDataPointIdentifier
    file_name: str


def save(
    storage: SaveStorage,
    tenant_id: Union[str, uuid.UUID],
    data_series_id: Union[str, uuid.UUID],
    fact_id: Union[str, uuid.UUID],
    history_data_point_identifier: HistoryDataPointIdentifier,
    file: InMemoryUploadedFile
) -> None:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span('skipper.dataseries.storage.contract.save', attributes={
        "skipper.func.param.tenant_id": str(data_series_id),
        "skipper.func.param.data_series_id": str(data_series_id),
        "skipper.func.param.param-fact_id": str(fact_id),
        "skipper.func.param.history_data_point_identifier.data_point_id": history_data_point_identifier.data_point_id,
        "skipper.func.param.history_data_point_identifier.point_in_time": history_data_point_identifier.point_in_time.isoformat(),
        "skipper.func.param.history_data_point_identifier.sub_clock": history_data_point_identifier.sub_clock,
        "skipper.func.param.file": file.name
    }):
        register(
            tenant_id=tenant_id,
            data_series_id=data_series_id,
            fact_id=fact_id,
            history_data_point_identifier=history_data_point_identifier,
            file_name=file.name
        )
        if SKIPPER_CELERY_TESTING:
            storage.save(
                file.name,
                file
            )
        else:
            # to prevent data loss, we actually dont want
            # to run this in on commit, but instead immediately
            # This might cause some issues with possibly
            # orphaned data, but this is better than losing data
            storage.save(
                file.name,
                file
            )


def register(
        tenant_id: Union[str, uuid.UUID],
        data_series_id: Union[str, uuid.UUID],
        fact_id: Union[str, uuid.UUID],
        history_data_point_identifier: HistoryDataPointIdentifier,
        file_name: str
) -> None:
    FileLookup.objects.create(
        tenant_id=tenant_id,
        data_series_id=data_series_id,
        fact_id=fact_id,
        data_point_id=history_data_point_identifier.data_point_id,
        point_in_time=history_data_point_identifier.point_in_time,
        sub_clock=history_data_point_identifier.sub_clock,
        file_name=file_name
    )


def register_bulk(
        tenant_id: Union[str, uuid.UUID],
        data_series_id: Union[str, uuid.UUID],
        bulk: List[HistoryDataPointIdentifierBulkElem]
) -> None:
    FileLookup.objects.bulk_create([
        FileLookup(
            tenant_id=tenant_id,
            data_series_id=data_series_id,
            fact_id=elem.fact_id,
            data_point_id=elem.history_data_point_identifier.data_point_id,
            point_in_time=elem.history_data_point_identifier.point_in_time,
            sub_clock=elem.history_data_point_identifier.sub_clock,
            file_name=elem.file_name
        ) for elem in bulk
    ])


def file_exists(
        tenant_id: Optional[Union[str, Any]],
        file_name: str
) -> bool:
    """
    Parameters:
    
    tenant_id - if set to None, check in all Tenants
    """
    if tenant_id is None:
        return FileLookup.objects.filter(
            file_name=file_name
        ).exists()
    return FileLookup.objects.filter(
        tenant_id=tenant_id,
        file_name=file_name
    ).exists()


def truncate_data_series_data(
        tenant_id: Union[str, uuid.UUID],
        data_series_id: Union[str, uuid.UUID],
) -> None:
    query_str = f"""
        UPDATE "_3_file_lookup"
        SET "deleted_at" = %(deleted_at)s
        WHERE
            "tenant_id" = %(tenant_id)s AND
            "data_series_id" = %(data_series_id)s AND
            "deleted_at" IS NULL
    """

    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            query_str,
            {
                'tenant_id': tenant_id,
                'data_series_id': data_series_id,
                'deleted_at': dbtime.now()
            }
        )


def truncate_fact_data(
        tenant_id: Union[str, uuid.UUID],
        data_series_id: Union[str, uuid.UUID],
        fact_id: Union[str, uuid.UUID]
) -> None:
    query_str = f"""
        UPDATE "_3_file_lookup"
        SET "deleted_at" = %(deleted_at)s
        WHERE
            "tenant_id" = %(tenant_id)s AND
            "data_series_id" = %(data_series_id)s AND
            "fact_id" = %(fact_id)s AND
            "deleted_at" IS NULL
    """

    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            query_str,
            {
                'tenant_id': tenant_id,
                'data_series_id': data_series_id,
                'fact_id': fact_id,
                'deleted_at': dbtime.now()
            }
        )


def delete_all_for_datapoint(
        tenant_id: Union[str, uuid.UUID],
        data_series_id: Union[str, uuid.UUID],
        fact_id: Union[str, uuid.UUID],
        data_point_id: str
) -> None:
    query_str = f"""
        UPDATE "_3_file_lookup"
        SET "deleted_at" = %(deleted_at)s
        WHERE
            "tenant_id" = %(tenant_id)s AND
            "data_series_id" = %(data_series_id)s AND
            "fact_id" = %(fact_id)s AND
            "data_point_id" = %(data_point_id)s AND
            "deleted_at" IS NULL
    """

    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            query_str,
            {
                'tenant_id': tenant_id,
                'data_series_id': data_series_id,
                'fact_id': fact_id,
                'data_point_id': data_point_id,
                'deleted_at': dbtime.now()
            }
        )


def delete_all_but_latest_for_datapoints(
    tenant_id: Union[str, uuid.UUID],
    data_series_id: Union[str, uuid.UUID],
    data_point_ids: List[str],
    point_in_time: datetime.datetime
) -> None:
    query_str = f"""
        WITH "to_mark" as (
            SELECT tbl.id
            FROM "_3_file_lookup" as tbl
            LEFT OUTER JOIN "_3_file_lookup" tbl2 ON (
                tbl.tenant_id = tbl2.tenant_id AND
                tbl.data_series_id = tbl2.data_series_id AND
                tbl.fact_id = tbl2.fact_id AND
                tbl.data_point_id = tbl2.data_point_id AND
                (tbl.point_in_time, tbl.sub_clock) < (tbl2.point_in_time, tbl2.sub_clock)
            )
            WHERE 
                (
                    -- only those that were part of this query
                    tbl.data_point_id = ANY(%(data_point_id)s) AND

                    -- only those that are not already deleted
                    tbl.deleted_at IS NULL AND

                    -- query only for the actual tenant 
                    tbl.tenant_id = %(tenant_id)s AND

                    -- query only for the actual dataseries 
                    tbl.data_series_id = %(data_series_id)s AND

                    -- delete only if there is at least one newer entry
                    tbl2.data_point_id IS NOT NULL
                )
        )
        UPDATE
            "_3_file_lookup" AS "to_update"
        SET
            "deleted_at" = %(deleted_at)s
        WHERE 
            "to_update".id IN (SELECT * FROM "to_mark")
    """
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            query_str,
            {
                'tenant_id': tenant_id,
                'data_series_id': data_series_id,
                'data_point_id': data_point_ids,
                'deleted_at': point_in_time
            }
        )

def delete_all_matching(
        tenant_id: Union[str, uuid.UUID],
        data_series_id: Union[str, uuid.UUID],
        fact_id: Union[str, uuid.UUID],
        history_data_point_identifiers: List[HistoryDataPointIdentifier],
) -> None:
    query_str = f"""
        UPDATE "_3_file_lookup"
        SET "deleted_at" = %(deleted_at)s
        WHERE
            "tenant_id" = %(tenant_id)s AND
            "data_series_id" = %(data_series_id)s AND
            "fact_id" = %(fact_id)s AND
            ("data_point_id", "point_in_time", "sub_clock") IN %(data_point_identifiers)s AND
            "deleted_at" IS NULL
    """

    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            query_str,
            {
                'tenant_id': tenant_id,
                'data_series_id': data_series_id,
                'fact_id': fact_id,
                'data_point_identifiers': tuple(
                    (elem.data_point_id, elem.point_in_time, elem.sub_clock) for elem in history_data_point_identifiers
                ),
                'deleted_at': dbtime.now()
            }
        )


# this might get out of hand if too much data is expected to be garbage collected
# if this happens, we have to do this in chunks
def garbage_collect(
    storage: DeleteStorage,
    older_than: datetime.datetime
) -> None:
    query_str = f"""
        DELETE 
        FROM "_3_file_lookup"
        WHERE
            "deleted_at" < %(older_than)s
        RETURNING "file_name"
    """

    garbage_files = set()

    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            query_str,
            {
                'older_than': older_than
            }
        )

        for deleted_file in cursor:
            # TODO: do this in chunks this might be slow otherwise
            # the file is not used by anyone else, we can delete it
            if not file_exists(tenant_id=None, file_name=deleted_file[0]):
                garbage_files.add(deleted_file[0])

    if SKIPPER_CELERY_TESTING:
        for __file in garbage_files:
            storage.delete(__file)
    else:
        # only delete if the commit went through, anything else
        # would mean lost data
        transaction.on_commit(lambda: [storage.delete(
            _file
        ) for _file in garbage_files])

