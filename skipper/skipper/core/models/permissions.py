# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import List, Tuple, Type
from django.db.models import Model
from rest_framework import permissions


class GlobalPermissions(Model):
    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model
        default_permissions: List[str] = []
        permissions = (
            ('browse_api', 'Browse API'),
        )


def core_permission_for_rest_method(entity: str, method: str, action: str) -> str:
    return f'{entity}_{method.lower()}_{action}'


def get_permission_string_for_action_and_http_verb(entity: str, action: str, http_verb: str) -> str:
    return f'core.{core_permission_for_rest_method(entity, http_verb, action)}'


def gen_permissions(entity: str, action: str) -> List[Tuple[str, str]]:
    return [
        (core_permission_for_rest_method(
            entity, 'GET', action
        ), f'Can run GET on entity {entity} and action {action}'),
        (core_permission_for_rest_method(
            entity, 'OPTIONS', action
        ), f'Can run OPTIONS on entity {entity} on action {action}'),
        (core_permission_for_rest_method(
            entity, 'HEAD', action
        ), f'Can run HEAD on entity {entity} on action {action}'),
        (core_permission_for_rest_method(
            entity, 'POST', action
        ), f'Can run POST on entity {entity} on action {action}'),
        (core_permission_for_rest_method(
            entity, 'PUT', action
        ), f'Can run PUT on entity {entity} on action {action}'),
        (core_permission_for_rest_method(
            entity, 'PATCH', action
        ), f'Can run PATCH on entity {entity} on action {action}'),
        (core_permission_for_rest_method(
            entity, 'DELETE', action
        ), f'Can run DELETE on entity {entity} on action {action}'),
    ]


PERMISSION_HTTP_VERBS: List[str] = ['GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']


def get_permissions_class(entity: str, action: str) -> Type[permissions.DjangoModelPermissions]:
    """Generate permission strings for core.entity_*_action
    
    entity is the parent object that is being altered, action is the child field (or the entire parent again). 
    
    Example:
    
        * changing core/user: entity=user, action=user
        * changing core/user's permission field: entity=user, action=user-permission
        
    """
    class Permission(permissions.DjangoModelPermissions):
        perms_map = {
            'GET': [f'core.{core_permission_for_rest_method(entity, "GET", action)}'],
            'OPTIONS': [f'core.{core_permission_for_rest_method(entity, "OPTIONS", action)}'],
            'HEAD': [f'core.{core_permission_for_rest_method(entity, "HEAD", action)}'],
            'POST': [f'core.{core_permission_for_rest_method(entity, "POST", action)}'],
            'PUT': [f'core.{core_permission_for_rest_method(entity, "PUT", action)}'],
            'PATCH': [f'core.{core_permission_for_rest_method(entity, "PATCH", action)}'],
            'DELETE': [f'core.{core_permission_for_rest_method(entity, "DELETE", action)}'],
        }
    return Permission


# FIXME [ticket 7107]
# TODO This is only a hack-solution until we have a custom user model
class CoreUserPermissions(Model):
    """
    global flow permissions, not really a model
    that stores any real data
    """
    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model
        default_permissions: List[str] = []
        permissions = (
            gen_permissions(entity='user', action='user')
        )


# TODO This is only a hack-solution until we have a custom user model
class CoreUserPermissionsPermissions(Model):
    """
    global flow permissions, not really a model
    that stores any real data
    """
    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model
        default_permissions: List[str] = []
        permissions = (
            gen_permissions(entity='user', action='user-permission')
        )