# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db.models import Model, CharField, DateTimeField, UUIDField
from typing import Type, Any, List

from skipper.core import models
from skipper.dataseries.models import calc_db_table


class BaseDataPointRelationMetaClass(models.base.ModelBase):

    def __new__(mcs: Type[Any], name: Any, bases: Any, attrs: Any, **kwargs: Any) -> Any:
        if name != "BaseDataPointFactRelation":
            _existing_meta: Type[Any] = object
            if "Meta" in attrs:
                _existing_meta = attrs["Meta"]

            abstract = False
            if hasattr(_existing_meta, "abstract"):
                abstract = _existing_meta.abstract

            if not abstract:
                _custom_meta: Type[Any] = attrs["MyMeta"]

                if not hasattr(_custom_meta, 'base_entity_name'):
                    raise NotImplementedError('base_entity_name was not set in meta class')

                base_entity_name = _custom_meta.base_entity_name
                is_view = False
                if hasattr(_custom_meta, 'is_view'):
                    is_view = _custom_meta.is_view

                if is_view:
                    class MetaA(_existing_meta):  # type: ignore
                        managed = False
                        db_table = calc_db_table('View' + base_entity_name)
                        default_permissions: List[str] = []

                    _existing_meta = MetaA
                else:
                    class MetaB(_existing_meta):  # type: ignore
                        managed = False
                        db_table = calc_db_table(base_entity_name)
                        default_permissions: List[str] = []

                    _existing_meta = MetaB

                attrs["Meta"] = _existing_meta

        r = super().__new__(mcs, name, bases, attrs, **kwargs)  # type: ignore
        return r


class BaseDataPointFactRelation(Model, metaclass=BaseDataPointRelationMetaClass):
    # data_point_id is the id here as well
    data_point_id = CharField(max_length=512, blank=False, null=False, default=None, primary_key=True, db_index=False)
    point_in_time = DateTimeField(auto_now=False, db_index=False)
    fact_id = UUIDField(null=False)
    value: Any
    user_id = models.string_field(max_length=512, null=True)
    record_source = models.string_field(max_length=512, null=True)
    sub_clock = models.BigIntegerField(null=True, blank=False)

    class Meta:
        abstract = True
