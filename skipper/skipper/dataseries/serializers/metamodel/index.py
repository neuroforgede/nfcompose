# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Dict, Any, List, cast
from uuid import UUID
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.generics import get_object_or_404
from django.db import IntegrityError, transaction
from django.db.models import Model, QuerySet
from django_multitenant.utils import get_current_tenant  # type: ignore

from skipper.dataseries import constants
from skipper.dataseries.models.metamodel.base_fact import BaseDataSeriesFactRelation
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
from skipper.dataseries.models.metamodel.django_base import DataSeriesChildRelationModel, DataSeriesMetaModel
from skipper.core.models.validation import validate_external_id_sql_safe
from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField
from skipper.dataseries.serializers.metamodel.base import _named_serializer_fields
from skipper.dataseries.serializers.metamodel.base_data_series_child import BaseDefaultDataSeriesChildSerializer

from skipper.dataseries.models.metamodel.index import UserDefinedIndex, DataSeries_UserDefinedIndex,\
    UserDefinedIndex_Target
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType, StorageBackendType
from skipper.dataseries.storage import actions as storage_actions


def get_indexable_child_or_fail(
    data_series: DataSeries, child_type: str, **kwargs: Dict[str, Any]
) -> DataSeriesChildRelationModel:
    '''you can pass an UUID with the kwarg 'id' or an external id with 'external_id' '''
    if 'id' in kwargs.keys():
        if child_type == IndexableDataSeriesChildType.DIMENSION.value:
            kwargs['dimension_id'] = kwargs['id']
        else:
            kwargs['fact_id'] = kwargs['id']
        kwargs.pop('id')

    ret: QuerySet[DataSeriesChildRelationModel]
    if child_type == IndexableDataSeriesChildType.FLOAT_FACT.value:
        ret = data_series.dataseries_floatfact_set.filter(**kwargs)
    elif child_type == IndexableDataSeriesChildType.IMAGE_FACT.value:
        ret = data_series.dataseries_imagefact_set.filter(**kwargs)
    elif child_type == IndexableDataSeriesChildType.BOOLEAN_FACT.value:
        ret = data_series.dataseries_booleanfact_set.filter(**kwargs)
    elif child_type == IndexableDataSeriesChildType.FILE_FACT.value:
        ret = data_series.dataseries_filefact_set.filter(**kwargs)
    elif child_type == IndexableDataSeriesChildType.JSON_FACT.value:
        ret = data_series.dataseries_jsonfact_set.filter(**kwargs)
    elif child_type == IndexableDataSeriesChildType.STRING_FACT.value:
        ret = data_series.dataseries_stringfact_set.filter(**kwargs)
    elif child_type == IndexableDataSeriesChildType.TEXT_FACT.value:
        ret = data_series.dataseries_textfact_set.filter(**kwargs)
    elif child_type == IndexableDataSeriesChildType.TIMESTAMP_FACT.value:
        ret = data_series.dataseries_timestampfact_set.filter(**kwargs)
    elif child_type == IndexableDataSeriesChildType.DIMENSION.value:
        if 'fact_id' in kwargs.keys():
            kwargs['dimension_id'] = kwargs['fact_id']
            kwargs.pop('fact_id')
        ret = data_series.dataseries_dimension_set.filter(**kwargs)
    else:
        raise ValidationError('Target Type not known!')

    if not ret.exists():
        if 'fact_id' in kwargs.keys():
            raise ValidationError(
                f'Target UUID ({str(kwargs["fact_id"])}) of given type ({child_type}) doesn\'t exist!'
            )
        elif 'dimension_id' in kwargs.keys():
            raise ValidationError(
                f'Target UUID ({str(kwargs["dimension_id"])}) of given type ({child_type}) doesn\'t exist!'
            )
        elif 'external_id' in kwargs.keys():
            raise ValidationError(
                f'Target external id ({str(kwargs["external_id"])}) of given type ({child_type}) doesn\'t exist!'
            )
        else:
            raise AssertionError('get_indexable_child_or_fail was called without expected arguments')
    if len(ret) > 1:
        raise IntegrityError('Multiple DataSeries children with the same id or external_id')
    return ret[0]


class WriteIndexTargetSerializer(serializers.Serializer[UserDefinedIndex_Target]):
    target_id = serializers.UUIDField(required=False, allow_null=False)
    target_external_id = serializers.CharField(required=False, allow_null=False)
    target_type = serializers.ChoiceField(
        choices=IndexableDataSeriesChildType.choices(),
        required=True, allow_null=False, allow_blank=False
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # this comes as the last validation
        attrs = super().validate(attrs)  # type: ignore
        data_series: DataSeries = self.parent.parent._get_data_series()  # type: ignore

        # safety: id must belong to something
        if 'target_id' not in attrs.keys() and 'target_external_id' not in attrs.keys():
            raise ValidationError(
                'At least one of \'target_id\' and \'target_external_id\' must be specified for every target'
            )
        elif 'target_id' not in attrs.keys() and 'target_external_id' in attrs.keys():
            ret = get_indexable_child_or_fail(
                data_series=data_series,
                child_type=attrs['target_type'],
                external_id=attrs['target_external_id']
            )
            if isinstance(ret, DataSeries_Dimension):
                attrs['target_id'] = ret.dimension.id
            elif isinstance(ret, BaseDataSeriesFactRelation):
                attrs['target_id'] = ret.fact.id
        elif 'target_id' in attrs.keys() and 'target_external_id' not in attrs.keys():
            get_indexable_child_or_fail(
                data_series=data_series,
                child_type=attrs['target_type'],
                id=attrs['target_id']
            )
        elif 'target_id' in attrs.keys() and 'target_external_id' in attrs.keys():
            res_by_uuid = get_indexable_child_or_fail(
                data_series=data_series,
                child_type=attrs['target_type'],
                id=attrs['target_id']
            )
            res_by_external_id = get_indexable_child_or_fail(
                data_series=data_series,
                child_type=attrs['target_type'],
                external_id=attrs['target_external_id']
            )
            if res_by_uuid.id != res_by_external_id.id:
                raise ValidationError('Given external_id and id point to different targets')

        if 'target_id' not in attrs.keys():
            raise AssertionError('target_id should\'ve been filled in here, but that has not happened\n')
        return attrs


class ReadIndexTargetSerializer(serializers.ModelSerializer[UserDefinedIndex_Target]):
    target_id = serializers.UUIDField(required=True, allow_null=False)
    target_type = serializers.ChoiceField(
        choices=IndexableDataSeriesChildType.choices(),
        required=True, allow_null=False, allow_blank=False
    )

    def to_representation(self, obj: UserDefinedIndex_Target) -> Any:
        representation = super().to_representation(obj)
        data_series: DataSeries = self.parent.parent._get_data_series()  # type: ignore

        representation['target_external_id'] = get_indexable_child_or_fail(
            data_series=data_series,
            child_type=representation['target_type'],
            id=representation['target_id']
        ).external_id
        return representation

    class Meta:
        model = UserDefinedIndex_Target
        fields = ['target_id', 'target_type']


class IndexHyperlinkedIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(
        self, obj: Model, view_name: str, request: Request, format: str
    ) -> Dict[str, Any]:
        index = cast(UserDefinedIndex, obj)
        return {'data_series': index.dataseries_userdefinedindex.data_series.id}


class IndexSerializer(BaseDefaultDataSeriesChildSerializer):
    url = IndexHyperlinkedIdentityField(view_name=constants.data_series_index_base_name + '-detail')
    targets = WriteIndexTargetSerializer(many=True, write_only=True)

    child_column_name = 'user_defined_index'
    consumer_model = UserDefinedIndex
    child_model = UserDefinedIndex
    relation_model = DataSeries_UserDefinedIndex

    def to_representation(self, obj: UserDefinedIndex) -> Any:
        representation = super().to_representation(obj)

        targets_serializer = ReadIndexTargetSerializer(many=True, read_only=True)
        targets_serializer.parent = self  # type: ignore
        representation['targets'] = targets_serializer.to_representation(
            obj.userdefinedindex_target_set.order_by('target_position_in_index_order').all())  # type: ignore

        return representation

    def _access_existing_data_series(self: Any, pk: str) -> DataSeries:
        _dim: UserDefinedIndex = get_object_or_404(
            UserDefinedIndex.objects.filter(id=pk))
        return _dim.dataseries_userdefinedindex.data_series

    def _get_external_id(self: Any, child: UserDefinedIndex) -> str:
        return child.dataseries_userdefinedindex.external_id

    def create(self, validated_data: Dict[str, Any]) -> DataSeriesMetaModel:
        with transaction.atomic():
            data_copy_without_targets = validated_data.copy()
            del data_copy_without_targets['targets']
            created = cast(UserDefinedIndex, super().create(data_copy_without_targets))
            targets: List[Any] = validated_data['targets']
            for i, target in enumerate(targets):
                UserDefinedIndex_Target.objects.create(
                    user_defined_index=created,
                    target_id=target['target_id'],
                    target_type=target['target_type'],
                    target_position_in_index_order=i
                )

            data_series = self._get_data_series()
            storage_actions.handle_create_user_defined_index(
                data_series_id=data_series.id, data_series_external_id=data_series.external_id,
                tenant_name=get_current_tenant().name, tenant_id=str(get_current_tenant().id),
                targets=targets, backend=self._get_data_series().backend, index_id=created.id)
            return created

    def validate_targets(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        # target ids have been filled by validation in WriteIndexTargetSerializer already!
        for target in targets:
            if 'target_id' not in target.keys():
                raise AssertionError(
                    'target_id should\'ve been filled in here, but that has not happened\n' + str(target)
                )

        contains_duplicates: bool = False
        contained_ids: List[UUID] = []
        for target in targets:
            if target['target_id'] in contained_ids:
                contains_duplicates = True
                break
            else:
                contained_ids.append(target['target_id'])

        if contains_duplicates:
            raise ValidationError('Field contains at least one duplicate')

        kwargs = self.context.get('view').kwargs  # type: ignore

        if 'pk' not in kwargs:
            if not targets:
                raise ValidationError('Indexes must have at least one target')
        else:
            _id = kwargs['pk']
            _child: UserDefinedIndex = get_object_or_404(
                UserDefinedIndex.objects.filter(id=_id))
            read_serializer = ReadIndexTargetSerializer(many=True, read_only=True)
            read_serializer.parent = self  # type: ignore
            current_targets = read_serializer\
                .to_representation(
                    _child.userdefinedindex_target_set
                    .order_by('target_position_in_index_order').all()  # type: ignore
                )

            if not len(current_targets) == len(targets):
                raise ValidationError('Index targets can not be changed after creation')
            else:
                for i in range(len(current_targets)):
                    if str(targets[i]['target_id']) != str(current_targets[i]['target_id']):
                        raise ValidationError('Index targets can not be changed after creation')

        return targets

    def validate_external_id(self, external_id: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore
        data_series = self._get_data_series()

        if 'pk' not in kwargs:
            if data_series.dataseries_userdefinedindex_set.all().filter(external_id=external_id).exists():
                raise ValidationError(
                    f'external id \'{external_id}\' is already in use\
                     by another Index in this data series definition'
                )
        else:
            _id = kwargs['pk']
            _child: UserDefinedIndex = get_object_or_404(
                UserDefinedIndex.objects.filter(id=_id))
            if external_id != self._get_external_id(_child):
                raise ValidationError('changing of external_id is not supported!')

        if not validate_external_id_sql_safe(external_id):
            raise ValidationError(
                'Only letters, numbers and \'_\' are allowed in external_ids of structure elements, 1-50 chars'
            )

        return external_id

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self._get_data_series().backend in (StorageBackendType.DYNAMIC_SQL_V1.value, StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value):
            raise ValidationError(f'indexes are not allowed in {self._get_data_series().backend} backends')
        return super().validate(data) # type: ignore

    class Meta:
        model = UserDefinedIndex
        fields = _named_serializer_fields(('targets',))
