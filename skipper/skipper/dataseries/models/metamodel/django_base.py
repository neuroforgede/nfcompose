# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from contextlib import contextmanager

import datetime
from threading import local

from django.db.models import Q, UniqueConstraint, ForeignKey, DO_NOTHING, Model, IntegerField
from typing import Any, cast, Type, List, Generator, TypeVar

from skipper.core import models
from skipper.core.models import fields
from skipper.core.models import softdelete
from skipper.core.models.tenant import get_tenant_model
from skipper.dataseries.models.common import calc_db_table

_thread_locals = local()

T = TypeVar('T', bound=Model, covariant=True)


class MetaModelSoftDeletionManager(softdelete.SoftDeletionTenantManager):  # type: ignore
    alive_only: bool

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs['alive_only'] = True
        super().__init__(*args, **kwargs)  # type: ignore

    def prefilter_queryset(self,
                           qs: 'softdelete.SoftDeletionQuerySet[T]') -> 'softdelete.SoftDeletionQuerySet[T]':
        timetravel_point: datetime.datetime = get_time_travel_point()
        if self.alive_only:
            if timetravel_point is None:
                return qs.filter(
                    deleted_at=None
                )
            else:
                return qs.filter(
                    # either not deleted, or deleted after the point in time
                    Q(deleted_at=None) | Q(deleted_at__gt=timetravel_point),
                    # created before the timetravel point
                    point_in_time__lte=timetravel_point
                )
        else:
            raise NotImplementedError()


class MetaModelSoftDeletionModel(softdelete.SoftDeletionTenantModel):
    point_in_time = fields.time_stamp_point_in_time()

    # all objects is the default, so that we can find everything properly in admin
    all_objects: softdelete.SoftDeletionManager = softdelete.SoftDeletionTenantManager(alive_only=False)  # type: ignore
    objects: softdelete.SoftDeletionManager = MetaModelSoftDeletionManager()  # type: ignore

    class Meta:
        abstract = True


class DataSeriesModelBase(models.base.ModelBase):

    def __new__(mcs: Type[Any], name: Any, bases: Any, attrs: Any, **kwargs: Any) -> Any:
        if name != "DataSeriesModel":
            _existing_meta: Type[Any] = object
            if "Meta" in attrs:
                _existing_meta = attrs["Meta"]

            _db_table: str
            if not hasattr(_existing_meta, 'db_table'):
                _db_table = calc_db_table(name)

                class MetaB(_existing_meta):  # type: ignore
                    db_table = _db_table

                attrs["Meta"] = MetaB
                _existing_meta = MetaB
            else:
                _db_table = _existing_meta.db_table

            _existing_constraints: List[Any] = []
            if hasattr(_existing_meta, 'constraints'):
                _existing_constraints = _existing_meta.constraints

            base_tenant_id_id_constraint_name = f'{_db_table}_tenant_id_id'
            assert len(base_tenant_id_id_constraint_name) <= 61
            _final_constraints = _existing_constraints + [
                UniqueConstraint(fields=['tenant_id', 'id'], name=f'{base_tenant_id_id_constraint_name}_0')
            ]

            class MetaC(_existing_meta):  # type: ignore
                constraints = _final_constraints

            attrs["Meta"] = MetaC
            _existing_meta = MetaC

        r = super().__new__(mcs, name, bases, attrs, **kwargs)  # type: ignore
        return r


class DataSeriesMetaModel(MetaModelSoftDeletionModel, metaclass=DataSeriesModelBase):
    id = fields.id_field()
    point_in_time = fields.time_stamp_point_in_time()
    last_modified_at = fields.time_stamp_last_modified_at()
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING)
    deleted_at: models.DateTimeField  # type: ignore
    metamodel_version = IntegerField(null=False, default=4)

    class Meta:
        abstract = True


class DataSeriesChildRelationModelBase(DataSeriesModelBase):

    def __new__(mcs: Type[Any], name: Any, bases: Any, attrs: Any, **kwargs: Any) -> Any:
        if name != "DataSeriesChildRelationModelBase":
            _existing_meta: Type[Any] = object
            if "Meta" in attrs:
                _existing_meta = attrs["Meta"]

            _existing_constraints: List[Any] = []
            if hasattr(_existing_meta, 'constraints'):
                _existing_constraints = _existing_meta.constraints


            db_table = calc_db_table(name)
            base_external_id_constraint_name = f'{db_table}_external_id'
            assert len(base_external_id_constraint_name) <= 61

            class MetaB(_existing_meta):  # type: ignore
                constraints = _existing_constraints + [
                    UniqueConstraint(fields=['tenant_id', 'data_series', 'external_id'],
                                     name=f'{base_external_id_constraint_name}_1',
                                     condition=Q(deleted_at__isnull=True)),
                    UniqueConstraint(fields=['tenant_id', 'data_series', 'external_id', 'deleted_at'],
                                     name=f'{base_external_id_constraint_name}_2',
                                     condition=Q(deleted_at__isnull=False))
                ]
                default_permissions: List[str] = []

            attrs["Meta"] = MetaB

        r = super().__new__(mcs, name, bases, attrs, **kwargs)
        return r


class DataSeriesChildRelationModel(DataSeriesMetaModel, metaclass=DataSeriesChildRelationModelBase):
    external_id = fields.external_id_field_sql_safe()

    class Meta:
        abstract = True


@contextmanager
def timetravel(point_in_time: datetime.datetime) -> Generator[None, None, None]:
    old_point_in_time_value = get_time_travel_point()
    try:
        set_time_travel_point(point_in_time)
        yield None
    except:
        set_time_travel_point(old_point_in_time_value)
        raise
    else:
        set_time_travel_point(old_point_in_time_value)


def get_time_travel_point() -> datetime.datetime:
    return cast(datetime.datetime, getattr(_thread_locals, 'point_in_time', None))


def set_time_travel_point(point_in_time: datetime.datetime) -> None:
    setattr(_thread_locals, 'point_in_time', point_in_time)