# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import uuid
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpRequest
from rest_framework.exceptions import PermissionDenied, NotFound, ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from typing import Dict, Any, Union, cast, List, Optional, TYPE_CHECKING
from skipper.dataseries.storage.contract import backend_is_deprecated

from skipper.core.models.guardian import get_objects_for_user_custom
from skipper.dataseries.models import get_permission_string_for_action_and_http_verb, \
    DATASERIES_PERMISSION_KEY_DATA_SERIES
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.settings import MAINTENANCE_MODE, MAINTENANCE_USER_ID


def get_data_series_id(kwargs_object: Dict[str, Any]) -> str:
    if 'by_external_id' in kwargs_object:
        return str(get_object_or_404(DataSeries.objects.filter(
            external_id=kwargs_object['data_series']
        )).id)
    else:
        return cast(str, kwargs_object['data_series'])


if TYPE_CHECKING:
    from typing import Protocol


    class _RequestContract(Protocol):
        method: str
        user: User
else:
    _RequestContract = Request

RequestContract = Union[HttpRequest, Request, _RequestContract]


def _data_series_exists_for_user(request: RequestContract, data_series_queryset: QuerySet[Any]) -> bool:
    return len(list(get_objects_for_user_custom(
        request.user,
        [
            get_permission_string_for_action_and_http_verb(
                action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
                http_verb='GET'
            )
        ],
        data_series_queryset,
        True,
        app_label='dataseries'
    ))) == 1


def has_data_series_permission(
        kwargs_object: Dict[str, Any],
        action: str,
        request: RequestContract,
        method: Optional[str] = None
) -> bool:
    try:
        return get_data_series_object(
            kwargs_object=kwargs_object,
            action=action,
            request=request,
            method=method
        ) is not None
    except PermissionDenied as e:
        return False


def get_data_series_object(
        kwargs_object: Dict[str, Any],
        action: str,
        request: RequestContract,
        method: Optional[str] = None
) -> Optional[DataSeries]:
    """
    central method to query the data_series for
    dataseries children
    tries to find a matching dataseries object
    corresponding to the passed kwargs
    while properly doing permission checks
    """
    _method = method or request.method
    if _method is None:
        raise PermissionDenied('could not safely determine HTTP method')

    data_series_read_perm = get_permission_string_for_action_and_http_verb(
        action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
        http_verb='GET'
    )
    if not request.user.has_perm(data_series_read_perm):
        raise PermissionDenied('you are globally not allowed to GET on dataseries, ' +
                               'this is a required privilege for children')

    action_perm = get_permission_string_for_action_and_http_verb(
        action=action,
        http_verb=_method
    )
    if not request.user.has_perm(action_perm):
        raise PermissionDenied('you are globally not allowed to run '
                               + _method + ' for action ' + action)

    data_series_id: str = get_data_series_id(kwargs_object)

    try:
        data_series_id_uuid: uuid.UUID = uuid.UUID(str(data_series_id))
    except ValueError as e:
        raise NotFound(f'did not find dataseries with {data_series_id} as it is no valid UUID')

    data_series_queryset = (
        DataSeries.objects.all().filter(id=data_series_id_uuid)
    )

    if len(list(data_series_queryset)) == 0:
        # the dataseries does not exist at all
        # let the default behaviour handle it
        return None

    data_series_objs: List[DataSeries] = list(
        get_objects_for_user_custom(
            user=request.user,
            perms=[
                data_series_read_perm,
                action_perm
            ],
            queryset=data_series_queryset,
            with_staff=True,
            app_label='dataseries'
        ))

    if len(data_series_objs) == 0:
        data_series_visible_for_user = _data_series_exists_for_user(
            request=request,
            data_series_queryset=data_series_queryset
        )
        if data_series_visible_for_user:
            # the dataseries exists and is visible to the user, but the user does not have the
            # permissions to run the method on that specific dataseries
            raise PermissionDenied('you do not have the permissions to run method '
                                   + _method + ' on ' + action + ' for this dataseries')

        # the dataseries exists but was filtered out because it is not visible to the user
        raise PermissionDenied('dataseries not found, do you have the correct permissions?')

    ensure_http_method_globally_allowed(data_series_objs[0], request, _method)

    return data_series_objs[0]


def ensure_http_method_globally_allowed(
        data_series: DataSeries,
        request: Union[HttpRequest, Request, _RequestContract],
        method: Optional[str] = None
) -> None:
    _method = method or request.method
    if MAINTENANCE_MODE:
        if MAINTENANCE_USER_ID is None or request.user.id != MAINTENANCE_USER_ID:
            raise PermissionDenied('system is in maintenance mode, can\'t modify data')
    if backend_is_deprecated(data_series.backend) and _method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        raise PermissionDenied('dataseries backend is deprecated, can\'t modify data')
    if data_series.locked and _method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        raise PermissionDenied('dataseries is locked, can\'t modify data')
