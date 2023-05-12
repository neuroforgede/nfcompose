# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend  # type: ignore
from guardian.shortcuts import get_objects_for_user  # type: ignore
from rest_framework.request import Request

PERM_FORMAT = '%(app_label)s.view_%(model_name)s'
SHORTCUT_KWARGS = {
    'accept_global_perms': False,
}

User = get_user_model()


def filter_queryset(
        user: User,  # type: ignore
        queryset: 'QuerySet[Any]'
) -> 'QuerySet[Any]':
    """
    Method that allows to filter a queryset for a given user.
    """
    permission = PERM_FORMAT % {
        'app_label': queryset.model._meta.app_label,
        'model_name': queryset.model._meta.model_name,
    }

    filtered: QuerySet[Any] = get_objects_for_user(
        user, permission, queryset,
        **SHORTCUT_KWARGS)

    return filtered


class ObjectPermissionsFilter(DjangoFilterBackend):  # type: ignore
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """

    def filter_queryset(self, request: Request, queryset: 'QuerySet[Any]', view: Any) -> 'QuerySet[Any]':
        queryset = super().filter_queryset(request, queryset, view)
        return filter_queryset(request.user, queryset)
