# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.db.models import BooleanField, Q, UniqueConstraint, QuerySet, CharField
from enum import Enum
from typing import Any, Dict, List
from typing import TYPE_CHECKING

from skipper.core.models import fields, softdelete
from skipper.core.models.softdelete import SoftDeletionQuerySet
from skipper.core.models.tenant import SoftDeleteTenantValidateExternalIdMixin
from skipper.core.utils import snippet
from skipper.core.validators import JSONSchemaData, JSONSchemaValidator
from skipper.dataseries.models.permissions import gen_permissions, DATASERIES_PERMISSION_KEY_DATA_SERIES, \
    DATASERIES_PERMISSION_KEY_DATA_POINT, DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT, \
    DATASERIES_PERMISSION_KEY_CREATE_VIEW, DATASERIES_PERMISSION_KEY_CUBE_SQL, \
    DATASERIES_PERMISSION_KEY_DATA_POINT_BULK, DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS, \
    DATASERIES_PERMISSION_KEY_PRUNE_HISTORY, DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES, \
    DATASERIES_PERMISSION_KEY_PERMISSION, DATASERIES_PERMISSION_KEY_CONSUMER, \
    DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT, DATASERIES_PERMISSION_KEY_PRUNE_METAMODEL
from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel
from skipper.dataseries.storage.contract import StorageBackendType, default_backend
from skipper.modules import Module

if TYPE_CHECKING:
    from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
    from skipper.dataseries.models.metamodel.json_fact import DataSeries_JsonFact
    from skipper.dataseries.models.metamodel.text_fact import DataSeries_TextFact
    from skipper.dataseries.models.metamodel.timestamp_fact import DataSeries_TimestampFact
    from skipper.dataseries.models.metamodel.string_fact import DataSeries_StringFact
    from skipper.dataseries.models.metamodel.image_fact import DataSeries_ImageFact
    from skipper.dataseries.models.metamodel.float_fact import DataSeries_FloatFact
    from skipper.dataseries.models.metamodel.boolean_fact import DataSeries_BooleanFact
    from skipper.dataseries.models.metamodel.file_fact import DataSeries_FileFact
    from skipper.dataseries.models.metamodel.consumer import DataSeries_Consumer
    from skipper.dataseries.models.metamodel.index import DataSeries_UserDefinedIndex


class ExtraConfigParameters(Enum):
    auto_clean_history_after_days = {
        'key': 'auto_clean_history_after_days',
        'default': -1,
        'type': 'integer'
    }
    auto_clean_meta_model_after_days = {
        'key': 'auto_clean_meta_model_after_days',
        'default': -1,
        'type': 'integer'
    }


def default_extra_config() -> Dict[str, Any]:
    ret: Dict[str, Any] = {}
    for _, member in ExtraConfigParameters.__members__.items():
        ret[str(member.value['key'])] = member.value['default']
    return ret


extra_config_validators: List[BaseValidator] = [
    JSONSchemaValidator(
        json_schema_data=JSONSchemaData(
            schema={
                "$schema": "http://json-schema.org/draft-07/schema",
                "$id": "data_series.extra_config",
                "type": "object",
                "required": [],
                "properties": {
                    f"{ExtraConfigParameters.auto_clean_history_after_days.value['key']}": {
                        "$id": f"#/properties/{ExtraConfigParameters.auto_clean_history_after_days.value['key']}",
                        "type": ExtraConfigParameters.auto_clean_history_after_days.value['type'],
                        "default": ExtraConfigParameters.auto_clean_history_after_days.value['default']
                    },
                    f"{ExtraConfigParameters.auto_clean_meta_model_after_days.value['key']}": {
                        "$id": f"#/properties/{ExtraConfigParameters.auto_clean_meta_model_after_days.value['key']}",
                        "type": ExtraConfigParameters.auto_clean_meta_model_after_days.value['type'],
                        "default": ExtraConfigParameters.auto_clean_meta_model_after_days.value['default']
                    }
                },
                "additionalProperties": False
            },
            definitions=None
        ))
]


class DataSeries(SoftDeleteTenantValidateExternalIdMixin, DataSeriesMetaModel):  # type: ignore
    id = fields.id_field()
    external_id = fields.external_id_field_sql_safe(null=False)
    name = fields.string_field(max_length=256)
    allow_extra_fields = BooleanField(null=False, default=False)
    backend = CharField(max_length=255, choices=StorageBackendType.choices(),
                        default=default_backend.value)
    extra_config = fields.json_field(validators=extra_config_validators)
    locked = BooleanField(null=False, default=False)

    dataseries_floatfact_set: 'SoftDeletionQuerySet[DataSeries_FloatFact]'
    dataseries_stringfact_set: 'SoftDeletionQuerySet[DataSeries_StringFact]'
    dataseries_timestampfact_set: 'SoftDeletionQuerySet[DataSeries_TimestampFact]'
    dataseries_textfact_set: 'SoftDeletionQuerySet[DataSeries_TextFact]'
    dataseries_imagefact_set: 'SoftDeletionQuerySet[DataSeries_ImageFact]'
    dataseries_filefact_set: 'SoftDeletionQuerySet[DataSeries_FileFact]'
    dataseries_jsonfact_set: 'SoftDeletionQuerySet[DataSeries_JsonFact]'
    dataseries_booleanfact_set: 'SoftDeletionQuerySet[DataSeries_BooleanFact]'

    dataseries_dimension_set: 'SoftDeletionQuerySet[DataSeries_Dimension]'

    dataseries_consumer_set: 'QuerySet[DataSeries_Consumer]'
    dataseries_userdefinedindex_set: 'QuerySet[DataSeries_UserDefinedIndex]'

    objects: 'softdelete.SoftDeletionManager[DataSeries]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries]'  # type: ignore

    def get_backend_type(self) -> StorageBackendType:
        return StorageBackendType.from_string(self.backend)

    def get_extra_config_property_value(self, config: ExtraConfigParameters) -> Any:
        ret: Any
        if config.value['key'] in self.extra_config:
            ret = self.extra_config[str(config.value['key'])]
        else:
            ret = config.value['default']
        if ret is None:
            ret = config.value['default']
        return ret

    def get_extra_config_value(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}
        for _, member in ExtraConfigParameters.__members__.items():
            ret[str(member.value['key'])] = self.get_extra_config_property_value(member)
        return ret

    class Meta:
        base_constraint_name = '_' + str(Module.DATA_SERIES.value) + "_" + snippet.underscore('DataSeries')
        constraints = [
            UniqueConstraint(fields=['tenant_id', 'external_id'], name=f'{base_constraint_name}_1',
                             condition=Q(deleted_at__isnull=True)),
            UniqueConstraint(fields=['tenant_id', 'external_id', 'deleted_at'], name=f'{base_constraint_name}_2',
                             condition=Q(deleted_at__isnull=False))
        ]
        # explicitly do not remove default permissions here, or admin page won't work properly
        # the default permissions also determine which user can administer dataseries changes in the api
        # FIXME: identify these and delete the rest
        # default_permissions = []
        permissions = [
            *gen_permissions(DATASERIES_PERMISSION_KEY_DATA_SERIES),
            *gen_permissions(DATASERIES_PERMISSION_KEY_DATA_POINT),
            *gen_permissions(DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT),
            *gen_permissions(DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT),
            *gen_permissions(DATASERIES_PERMISSION_KEY_CREATE_VIEW),
            *gen_permissions(DATASERIES_PERMISSION_KEY_PRUNE_HISTORY),
            *gen_permissions(DATASERIES_PERMISSION_KEY_PRUNE_METAMODEL),
            *gen_permissions(DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES),
            *gen_permissions(DATASERIES_PERMISSION_KEY_CUBE_SQL),
            *gen_permissions(DATASERIES_PERMISSION_KEY_DATA_POINT_BULK),
            *gen_permissions(DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS),
            *gen_permissions(DATASERIES_PERMISSION_KEY_PERMISSION),
            *gen_permissions(DATASERIES_PERMISSION_KEY_CONSUMER)
        ]

    def __str__(self) -> str:
        return f'DataSeries "{self.name}" ({str(self.external_id)},{str(self.id)})'


