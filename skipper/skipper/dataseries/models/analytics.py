# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.core.exceptions import ValidationError
from django.db import transaction, connections, models
from django.db.models import CharField, BooleanField, DO_NOTHING, ForeignKey
from typing import Any, Optional, Collection, Dict, cast

from skipper import settings
from skipper.core.models import softdelete, fields
from skipper.core.models.tenant import get_tenant_model
from skipper.core.raw_sql.role import user_exists
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.permissions import grant_select_permissions, revoke_select_permissions
from skipper.dataseries.raw_sql.tenant import tenant_schema_unescaped
from skipper.dataseries.storage.dynamic_sql.backend_info import get_views_in_schema, get_tables_in_schema
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB


class PostgresAnalyticsUser(softdelete.SoftDeletionTenantModel):
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING)

    id = fields.id_field()

    deleted_at: models.DateTimeField  # type: ignore

    # this is allowed to be non unique since only superusers are allowed to change things here
    role = CharField(max_length=63, blank=False, null=False, primary_key=False, unique=False)
    # whether to automatically grant users select permissions by default when creating views
    tenant_global_read = BooleanField(null=False, blank=False)

    all_objects: softdelete.SoftDeletionManager = softdelete.SoftDeletionTenantManager(alive_only=False)  # type: ignore
    objects: softdelete.SoftDeletionManager = softdelete.SoftDeletionTenantManager()  # type: ignore

    @classmethod
    def from_db(cls, db: Optional[str], field_names: Collection[str], values: Collection[Any]) -> Any:
        instance: 'PostgresAnalyticsUser' = super().from_db(db, field_names, values)
        # save original values, when model is loaded from database,
        # in a separate attribute on the model
        cast(Any, instance)._loaded_values = dict(zip(field_names, values))
        return instance

    def clean(self) -> None:
        if not user_exists(role=self.role, connection_name='default'):
            raise ValidationError(f'role "{self.role}" does not exist on database')
        if self.role in settings.SYSTEM_POSTGRES_DATABASE_ROLES:
            raise ValidationError(f'role "{self.role}" can not be managed as it is a system database role')
        if hasattr(self, '_loaded_values'):
            loaded_values: Dict[str, Any] = self._loaded_values  # type: ignore
            if loaded_values is not None and 'tenant_id' in loaded_values:
                # django multitenant already should handle this, but we
                # want to make sure this wont happen with a better
                # validation error
                if str(self.tenant_id) != str(loaded_values['tenant_id']):
                    raise ValidationError(f'can\'t change tenant of a PostgresAnalyticsUser')
        super().clean()

    def delete(self, using: Any = None, keep_parents: bool = False) -> None:
        # not really good as this still results in a 500 error with no custom form,
        # but if everything is set up properly, we should not be able to add the user in the first place
        if self.role in settings.SYSTEM_POSTGRES_DATABASE_ROLES:
            raise ValidationError(f'role "{self.role}" can not be managed as it is a system database role')
        super().delete(using=using, keep_parents=keep_parents)

    def save(self, force_insert: bool = False, force_update: bool = False, using: Any = None, update_fields: Any = None) -> None:
        # for good measure so we dont do anything stupid by accident
        if not user_exists(role=self.role, connection_name='default'):
            raise ValidationError(f'role "{self.role}" does not exist on database')
        if self.role in settings.SYSTEM_POSTGRES_DATABASE_ROLES:
            raise ValidationError(f'role "{self.role}" can not be managed as it is a system database role')
        if hasattr(self, '_loaded_values'):
            loaded_values: Dict[str, Any] = self._loaded_values  # type: ignore
            if loaded_values is not None and 'tenant_id' in loaded_values:
                # django multitenant already should handle this, but we
                # want to make sure this wont happen with a better
                # validation error
                if str(self.tenant_id) != str(loaded_values['tenant_id']):
                    raise ValidationError(f'can\'t change tenant of a PostgresAnalyticsUser')
        with transaction.atomic():            
            super().save(force_insert, force_update, using, update_fields)

            # TODO: revoke permissions on old tenant if it has changed
            # or forbid changing tenants
            # TODO: views are tables in postgres
            if self.tenant_global_read:
                views_and_tables_in_schema = [*get_views_in_schema(
                    connection=connections[DATA_SERIES_DYNAMIC_SQL_DB],
                    schema=tenant_schema_unescaped(self.tenant.name)
                ), *get_tables_in_schema(
                    connection=connections[DATA_SERIES_DYNAMIC_SQL_DB],
                    schema=tenant_schema_unescaped(self.tenant.name)
                )]
                if self.deleted_at is None:
                    for view in views_and_tables_in_schema:
                        grant_select_permissions(
                            role=self.role,
                            table=view,
                            connection_name=DATA_SERIES_DYNAMIC_SQL_DB,
                            schema_escaped=escape.escape(tenant_schema_unescaped(self.tenant.name))
                        )
                else:
                    for view in views_and_tables_in_schema:
                        revoke_select_permissions(
                            role=self.role,
                            table=view,
                            connection_name=DATA_SERIES_DYNAMIC_SQL_DB,
                            schema_escaped=escape.escape(tenant_schema_unescaped(self.tenant.name))
                        )

    class Meta:
        db_table = '_3_PostgresAnalyticsUser'.lower()

    def __str__(self) -> str:
        return f'PostgresAnalyticsUser "{self.role}" on Tenant {self.tenant.name}'
