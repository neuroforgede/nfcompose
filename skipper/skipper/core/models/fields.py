# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import logging
import uuid

import json

import datetime
import decimal
from django.core.validators import BaseValidator
from django.db.models.fields.json import JSONField  # type: ignore
from django.utils.functional import Promise, LazyObject
from typing import TypeVar, Type, Callable, Any, Optional, Union, Tuple, Dict, cast, List, NamedTuple

from django.db import models as _models
from django.utils.timezone import now
from django_multitenant.fields import TenantOneToOneField, TenantForeignKey  # type: ignore

from skipper.core.models.validation import external_id_validator_sql_safe, external_id_validator_url_safe
from skipper.core.storage.media import S3Boto3MediaStorage

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        # isoformat but with full precision
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, (decimal.Decimal, uuid.UUID, Promise)):
            return str(o)
        else:
            return super().default(o)


class FKey(TenantForeignKey):  # type: ignore

    def __init__(self, to: Union[Type[_models.Model], str],
                 on_delete: Callable[[Any, Any, Any, Any], Any] = _models.DO_NOTHING,
                 related_name: Optional[str] = None, related_query_name: Optional[str] = None,
                 limit_choices_to: Any = None, parent_link: bool = False, to_field: Optional[str] = None,
                 **kwargs: Any) -> None:
        kwargs['db_constraint'] = False
        kwargs['db_index'] = False
        if 'null' not in kwargs:
            kwargs['null'] = False
        if 'blank' not in kwargs:
            kwargs['blank'] = False
        assert on_delete == _models.DO_NOTHING
        super().__init__(
            to,
            on_delete=on_delete,
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
            parent_link=parent_link,
            to_field=to_field,
            **kwargs
        )

    def deconstruct(self) -> Tuple[Optional[str], str, List[str], Dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        if "db_constraint" in kwargs:
            del kwargs['db_constraint']
        if "db_index" in kwargs:
            del kwargs['db_index']
        return name, path, args, kwargs


class UniqueFKey(TenantOneToOneField):  # type: ignore
    """
    A UniqueFKey is essentially the same as a OneToOneField from django, but with extra settings
    """

    def __init__(self, to: Union[Type[_models.Model], str],
                 on_delete: Callable[[Any, Any, Any, Any], Any] = _models.DO_NOTHING,
                 to_field: Optional[str] = None, **kwargs: Any) -> None:
        kwargs['db_constraint'] = False
        kwargs['db_index'] = False
        if not 'null' in kwargs:
            kwargs['null'] = False
        if not 'blank' in kwargs:
            kwargs['blank'] = False
        assert on_delete == _models.DO_NOTHING
        super().__init__(to, on_delete=on_delete, to_field=to_field, **kwargs)

    def deconstruct(self) -> Tuple[Optional[str], str, List[str], Dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        if "db_constraint" in kwargs:
            del kwargs['db_constraint']
        if "db_index" in kwargs:
            del kwargs['db_index']
        return name, path, args, kwargs


T = TypeVar('T')


class EmptyDictNotBlankJSONField(JSONField):  # type: ignore
    empty_values: List[Any] = [None, "", [], ()]

    def formfield(self, **kwargs: Any) -> Any:  # type: ignore
        from ..forms import EmptyDictNotBlankJSONField

        return super().formfield(**{
            "form_class": EmptyDictNotBlankJSONField,
            **kwargs
        })


# helpers to convince mypy of the correct type when assigning...
def empty_dict_not_blank_json_field(validators: Optional[List[BaseValidator]] = None) -> Dict[str, Any]:
    if validators is None:
        validators = []
    return cast(Dict[str, Any], EmptyDictNotBlankJSONField(null=False, validators=validators))


def optional_empty_dict_not_blank_json_field(validators: List[BaseValidator]) -> 'Dict[str, Any]':
    return cast(Dict[str, Any], EmptyDictNotBlankJSONField(
        null=True,
        blank=True,
        validators=validators
    ))


def id_field(default: Any = uuid.uuid4) -> '_models.UUIDField[uuid.UUID, uuid.UUID]':
    if default is None:
        return _models.UUIDField(primary_key=True, editable=False)
    else:
        return _models.UUIDField(primary_key=True, default=default, editable=False)

def foreign_id_field() -> '_models.UUIDField[uuid.UUID, uuid.UUID]':
    return _models.UUIDField(primary_key=False, default=None, editable=False)

def int_field() -> int:
    return cast(int, _models.IntegerField(editable=False, primary_key=False, blank=False))

def external_id_field_sql_safe(null: bool = False) -> '_models.CharField[str, str]':
    # high max_length to have the db field be big, validation enforces smaller value
    return _models.CharField(max_length=256, blank=False, null=null, validators=[external_id_validator_sql_safe])


def external_id_field_url_safe(null: bool = False) -> '_models.CharField[str, str]':
    return _models.CharField(max_length=256, blank=False, null=null, validators=[external_id_validator_url_safe])


# FIXME: blank is not really used 100% correctly in this file, as it is only what is used in Django Forms
# same goes for usage of "default"

def string_field(max_length: int, null: bool = False, pk: bool = False) -> str:
    return cast(str, _models.CharField(max_length=max_length, blank=False, null=null, default=None, primary_key=pk))


def text(null: bool = False, blank: bool = False) -> str:
    return cast(str, _models.TextField(null=null, blank=blank))


def json_field(null: bool = False, default: Any = dict, validators: Optional[List[BaseValidator]] = None) -> Dict[str, Any]:
    if validators is None:
        return cast(Dict[str, Any], cast(Any, EmptyDictNotBlankJSONField)(null=null, default=default))
    else:
        return cast(Dict[str, Any], cast(Any, EmptyDictNotBlankJSONField)(
            null=null,
            default=default,
            validators=validators
        ))


class _S3BaseFileMixin(object):
    storage: Any

    def generate_filename(self, instance: Optional[_models.Model], filename: Any) -> str:
        # explicitly only ask the storage remove validate_filename since we always store to S3 with this
        return self.storage.generate_filename(filename)  # type: ignore


class _S3ImageField(_S3BaseFileMixin, _models.ImageField):
    pass


class _S3FileField(_S3BaseFileMixin, _models.FileField):
    pass


class DefaultS3MediaStorage(LazyObject):
    def _setup(self) -> None:
        self._wrapped = S3Boto3MediaStorage()


default_media_storage: S3Boto3MediaStorage = cast(S3Boto3MediaStorage, DefaultS3MediaStorage())


def s3_image_field(null: bool = False) -> _models.ImageField:
    # up the default a bit, we are prefixing things
    return _S3ImageField(null=null, blank=True, max_length=1024, storage=default_media_storage)


def s3_file_field(null: bool = False) -> _models.FileField:
    # up the default a bit, we are prefixing things
    return _S3FileField(null=null, blank=True, max_length=1024, storage=default_media_storage)


def image_field(null: bool = False) -> _models.ImageField:
    # up the default a bit, we are prefixing things
    return _models.ImageField(null=null, blank=True, max_length=1024)


def file_field(null: bool = False) -> _models.FileField:
    # up the default a bit, we are prefixing things
    return _models.FileField(null=null, blank=True, max_length=1024)


def float_field(null: bool = False, validators: List[Callable[..., Any]] = []) -> float:
    return cast(float, _models.FloatField(null=null, blank=False, validators=validators))


def boolean_field(null: bool = False) -> bool:
    return cast(bool, _models.BooleanField(null=null, blank=False))


def fkey(clazz: Type[T], related_name: Optional[str] = None) -> T:
    # hack, we actually do not really care about the internal type here,
    # we want to treat this as T
    return cast(T, FKey(clazz.__name__, related_name=related_name))


def unique_fkey(clazz: Type[T]) -> T:
    # hack, we actually do not really care about the internal type here,
    # we want to treat this as T
    return cast(T, UniqueFKey(clazz.__name__))


def time_stamp(null: bool = False) -> '_models.DateTimeField[Any, Any]':
    return _models.DateTimeField(null=null)


def time_stamp_default_now() -> '_models.DateTimeField[Any, Any]':
    return _models.DateTimeField(default=now)


def time_stamp_point_in_time(auto_now_add: bool = True) -> '_models.DateTimeField[Any, Any]':
    return _models.DateTimeField(auto_now_add=auto_now_add, db_index=True)


def time_stamp_last_modified_at(auto_now: bool = True) -> '_models.DateTimeField[Any, Any]':
    return _models.DateTimeField(auto_now=auto_now, db_index=False)
