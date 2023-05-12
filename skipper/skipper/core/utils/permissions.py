# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Union, Set, List

from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, User, Group
from django.db.models import Model
from guardian.shortcuts import get_perms, get_user_perms, get_group_perms  # type: ignore


def get_permissions_of_user(user: Union[User, AnonymousUser]) -> List[str]:
    _permissions = set()

    # We go over each AUTHENTICATION_BACKEND and try to fetch
    # a list of permissions
    for backend in auth.get_backends():
        if hasattr(backend, "get_all_permissions"):
            _permissions.update(backend.get_all_permissions(user))

    return list(_permissions)


def get_possible_permissions() -> List[str]:
    tmp_superuser = get_user_model()(
      is_active=True,
      is_superuser=True
    )
    return get_permissions_of_user(tmp_superuser)


def get_assignable_permissions(user: Union[User, AnonymousUser], relevant_perms: Set[str]) -> Set[str]:
    if user.is_anonymous:
        raise AssertionError()
    _perms_of_user = get_permissions_of_user(user)
    _assignable_permissions = {
        perm
        for perm in _perms_of_user
        if perm in relevant_perms
    }
    return _assignable_permissions


def get_directly_assigned_user_permissions(user: Union[User, AnonymousUser], relevant_perms: Set[str]) -> Set[str]:
    return {
        f'{str(perm.content_type.app_label)}.{str(perm.codename)}'
        for perm in user.user_permissions.all().select_related('content_type')  # type: ignore
        if f'{str(perm.content_type.app_label)}.{str(perm.codename)}' in relevant_perms
    }


def get_directly_assigned_group_permissions(group: Group, relevant_perms: Set[str]) -> Set[str]:
    return {
        f'{str(perm.content_type.app_label)}.{str(perm.codename)}'
        for perm in group.permissions.all().select_related('content_type')  # type: ignore
        if f'{str(perm.content_type.app_label)}.{str(perm.codename)}' in relevant_perms
    }


def perms_for_user(prefix: str, user: Union[User, AnonymousUser], model_obj: Model, relevant_perms_without_prefix: Set[str]) -> Set[str]:
    return {
        f'{prefix}.{elem}' for elem in set(get_perms(user, model_obj)).intersection(relevant_perms_without_prefix)
    }


def directly_assigned_perms_for_user(prefix: str, user: Union[User, AnonymousUser], model_obj: Model, relevant_perms_without_prefix: Set[str]) -> Set[str]:
    return {
        f'{prefix}.{elem}' for elem in set(get_user_perms(user, model_obj)).intersection(relevant_perms_without_prefix)
    }


def directly_assigned_perms_for_group(prefix: str, group: Group, model_obj: Model, relevant_perms_without_prefix: Set[str]) -> Set[str]:
    return {
        f'{prefix}.{elem}' for elem in set(get_group_perms(group, model_obj)).intersection(relevant_perms_without_prefix)
    }
