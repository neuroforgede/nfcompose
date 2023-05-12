# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import List, Tuple, Type
from django.db.models import Model
from rest_framework import permissions


class FlowPermissions(Model):
    """
    global flow permissions, not really a model
    that stores any real data
    """
    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model
        default_permissions: List[str] = []
        permissions = (
            ('system.edit', 'Allowed to edit system flows'),
            ('impl', 'Allowed to access flow implementation endpoints')
        )


def flow_permission_for_rest_method(entity: str, method: str, action: str) -> str:
    return f'{entity}_{method.lower()}_{action}'


def read_only_permissions(entity: str, actions: List[str]) -> List[str]:
    ret = []
    for method in ['GET', 'OPTIONS', 'HEAD']:
        for action in actions:
            ret.append(get_permission_string_for_action_and_http_verb(
                entity=entity,
                action=action,
                http_verb=method
            ))
    return ret


def get_permission_string_for_action_and_http_verb(entity: str, action: str, http_verb: str) -> str:
    return f'flow.{flow_permission_for_rest_method(entity, http_verb, action)}'


def gen_permissions(entity: str, action: str) -> List[Tuple[str, str]]:
    return [
        (flow_permission_for_rest_method(
            entity, 'GET', action
        ), f'Can run GET on entity {entity} and action {action}'),
        (flow_permission_for_rest_method(
            entity, 'OPTIONS', action
        ), f'Can run OPTIONS on entity {entity} on action {action}'),
        (flow_permission_for_rest_method(
            entity, 'HEAD', action
        ), f'Can run HEAD on entity {entity} on action {action}'),
        (flow_permission_for_rest_method(
            entity, 'POST', action
        ), f'Can run POST on entity {entity} on action {action}'),
        (flow_permission_for_rest_method(
            entity, 'PUT', action
        ), f'Can run PUT on entity {entity} on action {action}'),
        (flow_permission_for_rest_method(
            entity, 'PATCH', action
        ), f'Can run PATCH on entity {entity} on action {action}'),
        (flow_permission_for_rest_method(
            entity, 'DELETE', action
        ), f'Can run DELETE on entity {entity} on action {action}'),
    ]


PERMISSION_HTTP_VERBS: List[str] = ['GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']


def get_permissions_class(entity: str, action: str) -> Type[permissions.DjangoModelPermissions]:
    """Generate permission strings for flow.entity_*_action
    
    entity is the parent object that is being altered, action is the child field (or the entire parent again). 
    
    Example:
    
        * changing user: entity=user, action=user
        * changing user's permission field: entity=user, action=user-permission
        
    """
    class Permission(permissions.DjangoModelPermissions):
        perms_map = {
            'GET': [f'flow.{flow_permission_for_rest_method(entity, "GET", action)}'],
            'OPTIONS': [f'flow.{flow_permission_for_rest_method(entity, "OPTIONS", action)}'],
            'HEAD': [f'flow.{flow_permission_for_rest_method(entity, "HEAD", action)}'],
            'POST': [f'flow.{flow_permission_for_rest_method(entity, "POST", action)}'],
            'PUT': [f'flow.{flow_permission_for_rest_method(entity, "PUT", action)}'],
            'PATCH': [f'flow.{flow_permission_for_rest_method(entity, "PATCH", action)}'],
            'DELETE': [f'flow.{flow_permission_for_rest_method(entity, "DELETE", action)}'],
        }
    return Permission
