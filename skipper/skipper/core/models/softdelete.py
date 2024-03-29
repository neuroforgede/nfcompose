# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Tuple, Dict, TypeVar, Any, cast, Optional

from django.db import models
from django.utils import timezone
from django_multitenant.mixins import TenantManagerMixin, TenantModelMixin
from django_multitenant.utils import get_current_tenant_value

T = TypeVar('T', bound=models.Model, covariant=True)
_Row = TypeVar('_Row', covariant=True)


class SoftDeletionQuerySet(models.QuerySet):
    def delete(self) -> Tuple[int, Dict[str, int]]:
        super().filter(deleted_at__isnull=True).update(deleted_at=timezone.now())
        return 0, dict()

    def hard_delete(self) -> Tuple[int, Dict[str, int]]:
        return super().delete()

    def alive(self: 'SoftDeletionQuerySet[T, T]') -> 'SoftDeletionQuerySet[T, _Row]':
        return cast('SoftDeletionQuerySet[T, _Row]', self.filter(deleted_at=None))

    def dead(self: 'SoftDeletionQuerySet[T, T]') -> 'SoftDeletionQuerySet[T, _Row]':
        return cast('SoftDeletionQuerySet[T, _Row]', self.exclude(deleted_at=None))


class SoftDeletionManager(models.Manager):
    use_in_migrations = True
    alive_only: bool

    def __init__(self, *args: Any, **kwargs: Any):
        # default to alive only so that deleted objects are not visible by default
        self.alive_only = cast(bool, kwargs.pop('alive_only', True))
        super().__init__(*args, **kwargs)

    def get_queryset(self: 'SoftDeletionManager[T]') -> 'SoftDeletionQuerySet[T, T]':
        qs = super().get_queryset()
        qs.__class__ = SoftDeletionQuerySet

        _qs = cast('SoftDeletionQuerySet[T, T]', qs)
        _qs = self.prefilter_queryset(qs=_qs)
        return _qs

    def prefilter_queryset(self, qs: 'SoftDeletionQuerySet[T, T]') -> 'SoftDeletionQuerySet[T, T]':
        if self.alive_only:
            return cast('SoftDeletionQuerySet[T, T]', qs.filter(deleted_at=None))
        return qs

    def filter(self: 'SoftDeletionManager[T]', *args: Any, **kwargs: Any) -> 'SoftDeletionManager[T]':
        return cast('SoftDeletionManager[T]', super().filter(*args, **kwargs))

    def first(self) -> Optional[T]:
        return super().first()


class SoftDeletionTenantManager(TenantManagerMixin, models.Manager):
    use_in_migrations = True
    alive_only: bool

    def __init__(self, *args: Any, **kwargs: Any):
        # default to alive only so that deleted objects are not visible by default
        self.alive_only = cast(bool, kwargs.pop('alive_only', True))
        super().__init__(*args, **kwargs)

    def get_queryset(self: 'SoftDeletionManager[T]') -> 'SoftDeletionQuerySet[T, T]':
        qs = super().get_queryset()
        qs.__class__ = SoftDeletionQuerySet
        if self.alive_only:
            return cast('SoftDeletionQuerySet[T, T]', qs.filter(deleted_at=None))
        return cast('SoftDeletionQuerySet[T, T]', qs)

    def filter(self: 'SoftDeletionManager[T]', *args: Any, **kwargs: Any) -> 'SoftDeletionManager[T]':
        return cast('SoftDeletionManager[T]', super().filter(*args, **kwargs))

    def first(self) -> Optional[T]:
        return super().first()


class SoftDeletionModel(models.Model):
    # blank = True so that we can undelete stuff in admin
    deleted_at: models.DateTimeField = models.DateTimeField(blank=True, null=True, db_index=True)

    # all objects is the default, so that we can find everything properly in admin
    all_objects: SoftDeletionManager = SoftDeletionManager(alive_only=False)
    objects: SoftDeletionManager = SoftDeletionManager()

    class Meta:
        abstract = True

    def delete(self, using: Any = None, keep_parents: bool = False) -> Tuple[int, Dict[str, int]]:
        assert using is None
        assert keep_parents is False
        if self.deleted_at is None:
            # was already deleted, dont change the timestamp
            self.deleted_at = timezone.now()
            self.save()
        return 0, dict()

    def hard_delete(self) -> None:
        super().delete()


class SoftDeletionTenantModel(TenantModelMixin, SoftDeletionModel):
    # all objects is the default, so that we can find everything properly in admin
    all_objects: SoftDeletionManager = SoftDeletionTenantManager(alive_only=False)
    objects: SoftDeletionManager = SoftDeletionTenantManager()

    @property
    def tenant_field(self) -> str:
        return 'tenant_id'

    def save(self, *args, **kwargs):
        tenant_value = get_current_tenant_value()
        if self._state.adding and tenant_value and not isinstance(tenant_value, list):
            setattr(self, self.tenant_field, tenant_value)

        return super().save(*args, **kwargs)

    class Meta:
        abstract = True

