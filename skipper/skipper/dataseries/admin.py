# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.core.exceptions import ValidationError
from django.db.models import Model, QuerySet
from django.http.request import HttpRequest
from typing import Any, Dict, Optional, cast

from skipper.core.admin import TenantAwareAdminForm, TenantAwareAdmin
from skipper.dataseries.models import ConsumerEvent, BulkInsertTaskData, MetaModelTaskData
from skipper.dataseries.models.metamodel.consumer import Consumer
from skipper.dataseries.models.metamodel.data_series import DataSeries


# only superusers are allowed to change things as this
# is a critical path!
from skipper.dataseries.storage.dynamic_sql.tasks.persist_data_point import async_persist_data_point_chunk


class PostgresAnalyticsUserAdmin(TenantAwareAdmin):
    prepopulated_fields: Dict[str, Any] = {}
    list_display = ('id', 'role', 'tenant', 'deleted_at')
    search_fields = ('tenant__name', 'role')
    list_filter = ('tenant', 'deleted_at')
    ordering = ('role',)

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser


class DataSeriesAdminForm(TenantAwareAdminForm):
    def validate_impl(self, instance: Model) -> None:
        if self.instance._state.adding:
            raise ValidationError('adding dataseries via admin is not supported yet')

    class Meta:
        exclude = ['id']
        model = DataSeries

# no hard delete support here as we would end up forgetting a lot of cleanup!

class DataSeriesAdmin(TenantAwareAdmin):
    form = DataSeriesAdminForm
    prepopulated_fields: Dict[str, Any] = {}
    list_display = ('id', 'tenant', 'name', 'external_id', 'deleted_at')
    search_fields = ('tenant__name', 'name', 'external_id')
    list_filter = ('tenant', 'name', 'external_id', 'deleted_at')
    readonly_fields = ['tenant', 'external_id', 'backend']
    ordering = ('external_id',)
    date_hierarchy = 'point_in_time'

    def has_add_permission(self, request: Any, obj: Any = None) -> bool:
        return False


class ConsumerAdmin(TenantAwareAdmin):
    prepopulated_fields: Dict[str, Any] = {}
    list_display = ('id', 'tenant', 'dataseries___external_id', 'external_id', 'name', 'health', 'target', 'deleted_at')
    search_fields = ('dataseries_consumer__external_id',)
    list_filter = (
        'tenant',
        'name',
        'health',
        'dataseries_consumer__data_series__external_id',
        'dataseries_consumer__external_id'
    )
    readonly_fields = ['tenant']
    ordering = ('tenant__name', 'dataseries_consumer__external_id')
    date_hierarchy = None

    def has_add_permission(self, request: Any, obj: Any = None) -> bool:
        return False

    def external_id(self, obj: Consumer) -> str:
        return obj.dataseries_consumer.external_id

    def dataseries___external_id(self, obj: Consumer) -> str:
        return obj.dataseries_consumer.data_series.external_id


class ConsumerEventAdmin(TenantAwareAdmin):
    prepopulated_fields: Dict[str, Any] = {}
    list_display = (
        'id',
        'tenant',
        'dataseries___external_id',
        'consumer___external_id',
        'consumer___name',
        'point_in_time',
        'state',
        'event_type'
    )
    search_fields = ('consumer__dataseries_consumer__external_id',)
    list_filter = (
        'state',
        'tenant',
        'consumer__name',
        'consumer__dataseries_consumer__data_series__external_id',
        'consumer__dataseries_consumer__external_id'
    )
    readonly_fields = ['tenant']
    ordering = ('tenant__name', 'point_in_time', 'id')
    date_hierarchy = None
    actions = ['bulk_delete']

    def bulk_delete(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        queryset.delete()

    def has_bulk_delete_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: Any, obj: Any = None) -> bool:
        return False

    def dataseries___external_id(self, obj: ConsumerEvent) -> Any:
        return obj.consumer.dataseries_consumer.data_series.external_id

    def consumer___name(self, obj: ConsumerEvent) -> Any:
        return obj.consumer.name

    def consumer___external_id(self, obj: ConsumerEvent) -> Any:
        return obj.consumer.dataseries_consumer.external_id


class BulkInsertTaskDataAdmin(TenantAwareAdmin):
    prepopulated_fields: Dict[str, Any] = {}
    list_display = ('id', 'data_series', 'tenant', 'point_in_time')
    search_fields = ()
    list_filter = ('tenant', 'data_series', 'point_in_time')
    ordering = ('point_in_time',)
    actions = ['requeue']

    def requeue(self, request: HttpRequest, queryset: QuerySet[BulkInsertTaskData]) -> None:
        for elem in queryset:
            async_persist_data_point_chunk.delay(elem.id)

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


class MetaModelTaskDataAdmin(TenantAwareAdmin):
    prepopulated_fields: Dict[str, Any] = {}
    list_display = ('id', 'task', 'data_series', 'tenant', 'point_in_time')
    search_fields = ()
    list_filter = ('tenant', 'task', 'data_series', 'point_in_time')
    ordering = ('point_in_time',)
    actions = ['requeue']

    def requeue(self, request: HttpRequest, queryset: QuerySet[MetaModelTaskData]) -> None:
        from skipper.dataseries.tasks.metamodel import spawn_meta_model_task
        for elem in queryset:
            spawn_meta_model_task(elem.id)

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False