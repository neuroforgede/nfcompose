# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import datetime
from typing import Any, cast, Dict, Iterable, List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Model
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django_multitenant.utils import get_current_tenant  # type: ignore
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.generics import get_object_or_404

from skipper.core.models.validation import validate_external_id_sql_safe
from skipper.core.serializers.base import BaseSerializer
from skipper.core.feature_flags import get_feature_flag
from skipper.dataseries import constants
from skipper.dataseries.models import DEFAULT_PERMISSIONS_ON_DATASERIES_CREATE, PERMISSION_HTTP_VERBS, \
    get_permission_string_for_action_and_http_verb
from skipper.dataseries.models.metamodel.base_fact import BaseDataSeriesFactRelation
from skipper.dataseries.models.metamodel.data_series import DataSeries, extra_config_validators, default_extra_config
from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
from skipper.dataseries.models.metamodel.index import DataSeries_UserDefinedIndex
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.serializers.metamodel.base import _named_serializer_fields, DataSeriesBaseSerializer
from skipper.dataseries.storage import actions as storage_actions
from skipper.dataseries.storage.contract import backend_is_deprecated, StorageBackendType, \
    selectable_storage_backend_types, default_backend

def get_sub_views() -> List[Dict[str, str]]:
    sub_views: List[Dict[str, str]] = [
        {
            'sub_path': 'dimensions',
            'view_name': constants.data_series_dimension_base_name + '-list'
        },
        {
            'sub_path': 'float_facts',
            'view_name': constants.data_series_float_fact_base_name + '-list'
        },
        {
            'sub_path': 'string_facts',
            'view_name': constants.data_series_string_fact_base_name + '-list'
        },
        {
            'sub_path': 'text_facts',
            'view_name': constants.data_series_text_fact_base_name + '-list'
        },
        {
            'sub_path': 'timestamp_facts',
            'view_name': constants.data_series_timestamp_fact_base_name + '-list'
        },
        {
            'sub_path': 'image_facts',
            'view_name': constants.data_series_image_fact_base_name + '-list'
        },
        {
            'sub_path': 'file_facts',
            'view_name': constants.data_series_file_fact_base_name + '-list'
        },
        {
            'sub_path': 'json_facts',
            'view_name': constants.data_series_json_fact_base_name + '-list'
        },
        {
            'sub_path': 'boolean_facts',
            'view_name': constants.data_series_boolean_fact_base_name + '-list'
        },
        {
            'sub_path': 'consumers',
            'view_name': constants.data_series_consumer_base_name + '-list'
        },
        {
            'sub_path': 'data_points',
            'view_name': constants.data_series_data_point_base_name + '-list'
        },
        {
            'sub_path': 'history_data_points',
            'view_name': constants.data_series_history_data_point_base_name + '-list'
        },
        {
            'sub_path': 'data_points_bulk',
            'view_name': constants.data_series_data_point_base_name + '-create-bulk'
        },
        {
            'sub_path': 'data_point_validate_external_ids',
            'view_name': constants.data_series_data_point_base_name + '-check-external-ids'
        },
        {
            'sub_path': 'cube_sql',
            'view_name': constants.data_series_base_name + '-cubesql'
        },
        {
            'sub_path': 'create_view',
            'view_name': constants.data_series_base_name + '-createview'
        },
        {
            'sub_path': 'prune_history',
            'view_name': constants.data_series_base_name + '-prune-history'
        },
        {
            'sub_path': 'prune_meta_model',
            'view_name': constants.data_series_base_name + '-prune-metamodel'
        },
        {
            'sub_path': 'truncate',
            'view_name': constants.data_series_base_name + '-truncate'
        },
        {
            'sub_path': 'permission_user',
            'view_name': constants.data_series_permission_user_base_name + '-list'
        },
        {
            'sub_path': 'permission_group',
            'view_name': constants.data_series_permission_group_base_name + '-list'
        }
    ]
    if get_feature_flag("compose.structure.indexes"):
        sub_views.append({
            'sub_path': 'indexes',
            'view_name': constants.data_series_index_base_name + '-list'
        })
    return sub_views


class DataSeriesCubeSQLSerializer(BaseSerializer):
    class Meta:
        model = DataSeries
        fields: List[str] = []


class DataSeriesViewCreationSerializer(BaseSerializer):
    view_name = serializers.CharField(max_length=50)
    # removed for now, not really making sense with the new backends
    # materialize = serializers.BooleanField(default=False)
    overwrite = serializers.BooleanField(default=False)
    # refresh_if_exists = serializers.BooleanField(default=False)
    cascade_if_delete = serializers.BooleanField(default=False)
    identify_dimensions_by_external_id = serializers.BooleanField(default=False)
    full_history = serializers.BooleanField(default=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = cast(Dict[str, Any], super().validate(attrs))  # type: ignore

        view = self.context.get('view')
        data_series = view.get_object()

        if validated_data['full_history'] and data_series.backend != StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            raise ValidationError({
                'error': f'full_history is not supported on backend {data_series.backend}'
            })
        return validated_data

    class Meta:
        model = DataSeries
        fields = ['view_name', 'overwrite', 'cascade_if_delete', 'identify_dimensions_by_external_id', 'full_history']


class DataSeriesPruneHistorySerializer(BaseSerializer):
    older_than = serializers.DateTimeField(allow_null=True, required=False, default=None)

    def validate_older_than(self, older_than: datetime.datetime) -> datetime.datetime:
        if older_than is None:
            older_than = dbtime.now() - timezone.timedelta(days=30)
        return older_than

    class Meta:
        model = DataSeries
        fields: List[str] = ['older_than']


class DataSeriesPruneMetaModelSerializer(BaseSerializer):
    older_than = serializers.DateTimeField(allow_null=True, required=False, default=None)

    def validate_older_than(self, older_than: datetime.datetime) -> datetime.datetime:
        if older_than is None:
            older_than = dbtime.now() - timezone.timedelta(days=30)
        return older_than

    class Meta:
        model = DataSeries
        fields: List[str] = ['older_than']


class DataSeriesTruncateSerializer(BaseSerializer):
    class Meta:
        model = DataSeries
        fields: List[str] = []


class DataSeriesSerializer(DataSeriesBaseSerializer):
    name = serializers.CharField(max_length=256)
    backend = serializers.ChoiceField(choices=selectable_storage_backend_types, default=default_backend.name)
    url = serializers.HyperlinkedIdentityField(view_name=constants.data_series_base_name + '-detail')
    extra_config = serializers.JSONField(
        initial=lambda: default_extra_config(),
        default=lambda: default_extra_config(),
        validators=extra_config_validators
    )
    locked = serializers.BooleanField(read_only=True)
    sub_views = get_sub_views()
    did_lock_data_series: Optional[bool] = None

    
    def create(self, validated_data: Any) -> Any:
        with transaction.atomic():
            created = cast(DataSeries, super().create(validated_data))

            # add permissions to the user
            # users that created a dataseries automatically get all permissions
            # on them. Only if they have the appropriate global permissions,
            # they are allowed to act on these permissions
            user = None
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                user = request.user

            assert user is not None

            if not user.is_anonymous:
                for action in DEFAULT_PERMISSIONS_ON_DATASERIES_CREATE:
                    for http_verb in PERMISSION_HTTP_VERBS:
                        assign_perm(
                            get_permission_string_for_action_and_http_verb(
                                action=action,
                                http_verb=http_verb
                            ),
                            user,
                            obj=created
                        )

            # FIXME: implement primary groups / groups to share data with?
            #  Users in the same group should have access to these dataseries objects as well?

            storage_actions.handle_create_data_series(
                created.id,
                created.external_id,
                tenant_name=get_current_tenant().name,
                external_id=created.external_id,
                backend=created.backend,
                tenant_id=str(get_current_tenant().id)
            )
            return created

    def update(self, instance: Model, validated_data: Dict[str, Any]) -> Any:

        if 'backend' in validated_data:
            data_series: DataSeries = cast(DataSeries, instance)
            backend = validated_data['backend']
            original_backend = data_series.backend

            if original_backend != backend:
                if (original_backend == StorageBackendType.DYNAMIC_SQL_V1.value and
                    backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value) or \
                    (original_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value and
                     backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value) or \
                    (original_backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value and
                    backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value) or \
                    (original_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value and
                    backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value):
                    # lock data_series before setting locked to True so we dont unlock too early
                    # transactions that started before the lock might still write data
                    # so it is advised to use some kind of maintenance mode for nfcompose
                    # this is just a best effort to lock out writes to the dataseries
                    # (writes are not lost, but not in the materialized table)
                    with transaction.atomic():
                        returned = super(DataSeriesSerializer, self).update(data_series, validated_data)
                        self.did_lock_data_series = True
                        _locked_data_series: DataSeries = DataSeries.objects.select_for_update().get(id=returned.id)
                        _locked_data_series.locked = True
                        _locked_data_series.save()
                    # outside of transaction spawn migration task
                    storage_actions.handle_migrate_data_series_backend(
                        data_series=data_series,
                        tenant_id=get_current_tenant().id,
                        tenant_name=get_current_tenant().name,
                        old_backend=original_backend,
                        new_backend=backend
                    )
                    return returned
                else:
                    raise APIException(f'unexpected change from backend {original_backend} to {backend}')
            else:
                return super(DataSeriesSerializer, self).update(instance, validated_data)
        else:
            return super(DataSeriesSerializer, self).update(instance, validated_data)

    def _add_dimensions_to_mock_datapoint_structure(
            self, datapoint_structure_aggregate: Dict[str, Dict[str, str]],
            base_field_name: str,
            name: str,
            dataseries_dimension_set: Iterable[DataSeries_Dimension]
    ) -> None:
        for _dataseries_dimension in dataseries_dimension_set:
            _dimension = _dataseries_dimension.dimension
            datapoint_structure_aggregate[f'{base_field_name}'][str(_dataseries_dimension.external_id)] = \
                f'required: value for {name} with id {str(_dataseries_dimension.external_id)} (\'{_dimension.name}\')'

    def _add_fact_to_mock_datapoint_structure(
            self, datapoint_structure_aggregate: Dict[str, Dict[str, str]],
            base_field_name: str,
            name: str,
            dataseries_fact_set: Iterable[BaseDataSeriesFactRelation]
    ) -> None:
        for _dataseries_fact in dataseries_fact_set:
            _fact = _dataseries_fact.fact
            if not _fact.optional:
                _str = f'required: value for {name} with id {str(_dataseries_fact.external_id)} (\'{_fact.name}\')'
            else:
                _str = f'optional: value for {name} with id {str(_dataseries_fact.external_id)} (\'{_fact.name}\')'
            datapoint_structure_aggregate[base_field_name][str(_dataseries_fact.external_id)] = _str

    def validate_external_id(self, external_id: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore
        if 'pk' not in kwargs:
            others_found = DataSeries.objects.filter(external_id=external_id).count()
            if others_found > 0:
                raise ValidationError('external_id already in use')
        else:
            original_db: DataSeries = get_object_or_404(
                DataSeries.objects.filter(id=kwargs['pk']))
            if original_db.external_id != external_id:
                raise ValidationError('changing of external_id for DataSeries is not supported!')
        if not validate_external_id_sql_safe(external_id):
            raise ValidationError("Only letters, numbers and '_' are allowed in external_ids of dataseries")
        return external_id

    def validate_backend(self, backend: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore
        if 'pk' not in kwargs:
            # new, make sure backend is not deprecated!
            if backend_is_deprecated(backend):
                raise ValidationError(f'backend {backend} is deprecated')
        else:
            original_db: DataSeries = get_object_or_404(
                DataSeries.objects.filter(id=kwargs['pk']))
            original_backend = original_db.backend
            if original_backend != backend:
                if original_backend == StorageBackendType.DYNAMIC_SQL_V1.value and \
                        backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value:
                    pass
                elif original_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value and \
                        backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
                    pass
                elif original_backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value and \
                        backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                    pass
                elif original_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value and \
                        backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
                    pass
                else:
                    raise ValidationError(f'can\'t migrate from {original_backend} to {backend}')
        return backend

    def to_representation(self, data_series: DataSeries) -> Any:
        _representation = super().to_representation(data_series)

        _representation['extra_config'] = data_series.get_extra_config_value()

        _datapoint_structure: Dict[str, Any] = {}

        if self.did_lock_data_series is not None:
            # even if running synchronously, we need to be proper here
            # so set it manually to locked on the immediate response
            _representation['locked'] = self.did_lock_data_series

        _datapoint_structure['external_id'] = 'required: external_id'
        _datapoint_structure['payload'] = {}

        self._add_dimensions_to_mock_datapoint_structure(_datapoint_structure,
                                                         'payload',
                                                         'dimension',
                                                         data_series.dataseries_dimension_set.all())

        self._add_fact_to_mock_datapoint_structure(_datapoint_structure,
                                                   'payload',
                                                   'float fact',
                                                   data_series.dataseries_floatfact_set.all())
        self._add_fact_to_mock_datapoint_structure(_datapoint_structure,
                                                   'payload',
                                                   'string fact',
                                                   data_series.dataseries_stringfact_set.all())
        self._add_fact_to_mock_datapoint_structure(_datapoint_structure,
                                                   'payload',
                                                   'text fact',
                                                   data_series.dataseries_textfact_set.all())
        self._add_fact_to_mock_datapoint_structure(_datapoint_structure,
                                                   'payload',
                                                   'timestamp fact',
                                                   data_series.dataseries_timestampfact_set.all())
        self._add_fact_to_mock_datapoint_structure(_datapoint_structure,
                                                   'payload',
                                                   'image fact',
                                                   data_series.dataseries_imagefact_set.all())
        self._add_fact_to_mock_datapoint_structure(_datapoint_structure,
                                                   'payload',
                                                   'file fact',
                                                   data_series.dataseries_filefact_set.all())
        self._add_fact_to_mock_datapoint_structure(_datapoint_structure,
                                                   'payload',
                                                   'json fact',
                                                   data_series.dataseries_jsonfact_set.all())
        self._add_fact_to_mock_datapoint_structure(_datapoint_structure,
                                                   'payload',
                                                   'boolean fact',
                                                   data_series.dataseries_booleanfact_set.all())

        _representation['data_point_structure'] = _datapoint_structure

        return _representation

    class Meta:
        model = DataSeries
        fields = _named_serializer_fields(('locked', 'backend', 'extra_config', 'allow_extra_fields',))
