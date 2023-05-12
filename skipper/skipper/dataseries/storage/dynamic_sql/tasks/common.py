# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.analytics import PostgresAnalyticsUser
from skipper.dataseries.raw_sql.permissions import grant_select_permissions
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB


def _get_queryset(klass: Any) -> Any:
    """
    Return a QuerySet or a Manager.
    Duck typing in action: any class with a `get()` method (for
    get_or_fail) or a `filter()` method (for get_list_or_404) might do
    the job.
    """
    # If it is a model class or anything else with ._default_manager
    if hasattr(klass, '_default_manager'):
        return klass._default_manager.all()
    return klass


def get_or_fail(klass: Any, *args: Any, **kwargs: Any) -> Any:
    queryset = _get_queryset(klass)
    if not hasattr(queryset, 'get'):
        klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            "First argument to get_or_fail() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    return queryset.get(*args, **kwargs)


def grant_permissions_for_global_analytics_users(
        tenant: Tenant,
        schema_escaped: str,
        table: str
) -> None:
    postgres_analytics_user: PostgresAnalyticsUser
    for postgres_analytics_user in PostgresAnalyticsUser.objects.filter(
        tenant=tenant,
        tenant_global_read=True
    ).all():
        grant_select_permissions(
            role=postgres_analytics_user.role,
            schema_escaped=schema_escaped,
            table=table,
            connection_name=DATA_SERIES_DYNAMIC_SQL_DB
        )
