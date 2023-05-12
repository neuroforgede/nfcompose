# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Tuple, Dict, TypeVar, Any

from django.db import models

T = TypeVar('T', bound=models.Model, covariant=True)
_Row = TypeVar('_Row', covariant=True)

class SoftDeletionQuerySet(models.QuerySet[T]):
    def alive(self: 'SoftDeletionQuerySet[T]') -> 'SoftDeletionQuerySet[T]': ...

    def dead(self: 'SoftDeletionQuerySet[T]') -> 'SoftDeletionQuerySet[T]': ...

    def hard_delete(self) -> None: ...

class SoftDeletionManager(models.Manager[T]):
    def __init__(self, *args: Any, **kwargs: Any): ...

class SoftDeletionTenantManager(models.Manager[T]):
    def __init__(self, *args: Any, **kwargs: Any): ...

class SoftDeletionModel(models.Model):
    deleted_at: models.DateTimeField[Any, Any]

    def hard_delete(self) -> None: ...
    def delete(self, using: Any = None, keep_parents: bool = False) -> Tuple[int, Dict[str, int]]: ...

class SoftDeletionTenantModel(SoftDeletionModel):
    ...