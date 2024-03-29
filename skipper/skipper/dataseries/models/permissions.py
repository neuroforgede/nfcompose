# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG



from django.db.models import Model
from typing import List, Tuple


class DataSeriesPermissions(Model):
    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model
        default_permissions: List[str] = []
        permissions = (
            ('node_red_etl', 'Allowed to use the node red ETL interface (node_red_etl)'),
            ('storage_backend_data', 'Allowed to view metadata of the backends (storage_backend_data)'),
            ('prune_data_series', 'Allowed to prune old data_series (prune_data_series)')
        )


DATASERIES_PERMISSION_KEY_DATA_SERIES = 'data_series'
DATASERIES_PERMISSION_KEY_DATA_POINT = 'data_point'
DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT = 'history_data_point'
DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT = 'structure_element'
DATASERIES_PERMISSION_KEY_CREATE_VIEW = 'create_view'
DATASERIES_PERMISSION_KEY_PRUNE_HISTORY = 'prune_history'
DATASERIES_PERMISSION_KEY_PRUNE_METAMODEL = 'prune_metamodel'
DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES = 'truncate_data_series'
DATASERIES_PERMISSION_KEY_CUBE_SQL = 'cube_sql'
DATASERIES_PERMISSION_KEY_DATA_POINT_BULK = 'data_point_bulk'
DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS = 'check_external_ids'
DATASERIES_PERMISSION_KEY_PERMISSION = 'permission'
DATASERIES_PERMISSION_KEY_CONSUMER = 'consumer'


def ds_permission_for_rest_method(method: str, action: str) -> str:
    # ds == dataseries
    # FIXME: rename this to dataseries_ ? (or alias it?)
    return f'ds_{method.lower()}_{action}'


def get_permission_string_for_action_and_http_verb(action: str, http_verb: str) -> str:
    return f'dataseries.{ds_permission_for_rest_method(http_verb, action)}'


def gen_permissions(action: str) -> List[Tuple[str, str]]:
    return [
        (ds_permission_for_rest_method('GET', action), f'Can run GET on entity dataseries on action {action}'),
        (ds_permission_for_rest_method('OPTIONS', action), f'Can run OPTIONS on entity dataseries on action {action}'),
        (ds_permission_for_rest_method('HEAD', action), f'Can run HEAD on entity dataseries on action {action}'),
        (ds_permission_for_rest_method('POST', action), f'Can run POST on entity dataseries on action {action}'),
        (ds_permission_for_rest_method('PUT', action), f'Can run PUT on entity dataseries on action {action}'),
        (ds_permission_for_rest_method('PATCH', action), f'Can run PATCH on entity dataseries on action {action}'),
        (ds_permission_for_rest_method('DELETE', action), f'Can run DELETE on entity dataseries on action {action}'),
    ]


PERMISSION_HTTP_VERBS: List[str] = ['GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']
DEFAULT_PERMISSIONS_ON_DATASERIES_CREATE = [
    DATASERIES_PERMISSION_KEY_DATA_SERIES,
    DATASERIES_PERMISSION_KEY_DATA_POINT,
    DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
    DATASERIES_PERMISSION_KEY_DATA_POINT_BULK,
    DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS,
    DATASERIES_PERMISSION_KEY_PERMISSION
]
ALL_AVAILABLE_PERMISSIONS_DATA_SERIES = [
    DATASERIES_PERMISSION_KEY_DATA_SERIES,
    DATASERIES_PERMISSION_KEY_DATA_POINT,
    DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
    DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
    DATASERIES_PERMISSION_KEY_CREATE_VIEW,
    DATASERIES_PERMISSION_KEY_CUBE_SQL,
    DATASERIES_PERMISSION_KEY_DATA_POINT_BULK,
    DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS,
    DATASERIES_PERMISSION_KEY_PRUNE_HISTORY,
    DATASERIES_PERMISSION_KEY_PERMISSION,
    DATASERIES_PERMISSION_KEY_CONSUMER
]

DATA_POINT_RELEVANT_PERMISSIONS = [
    DATASERIES_PERMISSION_KEY_DATA_SERIES,
    DATASERIES_PERMISSION_KEY_DATA_POINT,
]


def read_only_permissions(actions: List[str]) -> List[str]:
    ret = []
    for method in ['GET', 'OPTIONS', 'HEAD']:
        for action in actions:
            ret.append('dataseries.' + ds_permission_for_rest_method(
                action=action,
                method=method
            ))
    return ret


DATA_SERIES_INSPECT_PERMISSIONS = read_only_permissions([
    DATASERIES_PERMISSION_KEY_DATA_SERIES,
    DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT
])

# short hand for all permissions that a user might need
# in order to crud data points
DATA_POINT_CRUD_PERMISSIONS = [
    DATASERIES_PERMISSION_KEY_DATA_POINT,
    DATASERIES_PERMISSION_KEY_DATA_POINT_BULK,
    DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS,
]
