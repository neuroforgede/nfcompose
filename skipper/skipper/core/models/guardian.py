# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from itertools import groupby
from typing import List, Any, cast

from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Count, Q
from django_multitenant.utils import get_current_tenant  # type: ignore
from guardian.utils import get_anonymous_user, get_user_obj_perms_model, get_group_obj_perms_model  # type: ignore

from skipper.core.models.tenant import is_tenant_manager  # type: ignore


def get_objects_for_user_custom(
        user: Any,
        perms: List[str],
        queryset: QuerySet[Any],
        with_staff: bool,
        app_label: str,
        use_groups: bool = True,
        any_perm: bool = False,
        with_superuser: bool = True,
        with_tenant_manager: bool = True,
        accept_global_perms: bool = False
) -> QuerySet[Any]:
    '''Replaces the get_objects_for_user function by django, as the original doesn't allow custom behavior like staff overrides'''
    codenames = set()

    for perm in perms:
        if '.' in perm:
            new_app_label, codename = perm.split('.', 1)
        else:
            codename = perm
        codenames.add(codename)

    # First check if user is superuser and if so, return queryset immediately
    if with_superuser and user.is_superuser:
        return queryset

    # Staff users can be made "sub-superusers" on demand so that we do not have to
    # set permissions manually. Also if they can access the admin page
    # they probably can also set the permissions themselves.
    if with_staff and user.is_staff:
        return queryset

    # Users marked as their tenant's manager may have access to all functionalities as long as they have the required
    # global permission (which is checked before this method is called)
    if with_tenant_manager and is_tenant_manager(user, get_current_tenant()):
        return queryset

    # Check if the user is anonymous. The
    # django.contrib.auth.models.AnonymousUser object doesn't work for queries
    # and it's nice to be able to pass in request.user blindly.
    if user.is_anonymous:
        user = get_anonymous_user()

    global_perms = set()
    has_global_perms = False
    # a superuser has by default assigned global perms for any
    if accept_global_perms and with_superuser:
        for code in codenames:
            if user.has_perm(app_label + '.' + code):
                global_perms.add(code)
        for code in global_perms:
            codenames.remove(code)
        # prerequisite: there must be elements in global_perms otherwise just follow the procedure for
        # object based permissions only AND
        # 1. codenames is empty, which means that permissions are ONLY set globally, therefore return the full queryset.
        # OR
        # 2. any_perm is True, then the global permission beats the object based permission anyway,
        # therefore return full queryset
        if len(global_perms) > 0 and (len(codenames) == 0 or any_perm):
            return queryset
        # if we have global perms and still some object based perms differing from global perms and any_perm is set
        # to false, then we have to flag that global perms exist in order to merge object based permissions by user
        # and by group correctly. Scenario: global perm change_xx and object based perm delete_xx on object A for user,
        # and object based permission delete_xx  on object B for group, to which user is assigned.
        # get_objects_for_user(user, [change_xx, delete_xx], use_groups=True, any_perm=False, accept_global_perms=True)
        # must retrieve object A and B.
        elif len(global_perms) > 0 and (len(codenames) > 0):
            has_global_perms = True

    # Now we should extract list of pk values for which we would filter
    # queryset
    user_model = get_user_obj_perms_model(queryset.model)
    user_obj_perms_queryset = (user_model.objects
                               .filter(user=user))
    if len(codenames):
        user_obj_perms_queryset = user_obj_perms_queryset.filter(
            permission__codename__in=codenames)
    direct_fields = ['content_object__pk', 'permission__codename']
    generic_fields = ['object_pk', 'permission__codename']
    if user_model.objects.is_generic():
        user_fields = generic_fields
    else:
        user_fields = direct_fields

    if use_groups:
        group_model = get_group_obj_perms_model(queryset.model)
        group_filters = {
            'group__%s' % cast(Any, get_user_model()).groups.field.related_query_name(): user,
        }
        if len(codenames):
            group_filters.update({
                'permission__codename__in': codenames,
            })
        groups_obj_perms_queryset = group_model.objects.filter(**group_filters)
        if group_model.objects.is_generic():
            group_fields = generic_fields
        else:
            group_fields = direct_fields
        if not any_perm and len(codenames) > 1 and not has_global_perms:
            user_obj_perms = user_obj_perms_queryset.values_list(*user_fields)
            groups_obj_perms = groups_obj_perms_queryset.values_list(*group_fields)
            data = list(user_obj_perms) + list(groups_obj_perms)
            # sorting/grouping by pk (first in result tuple)
            keyfunc = lambda t: t[0]
            data = sorted(data, key=keyfunc)
            pk_list = []
            for pk, group in groupby(data, keyfunc):
                obj_codenames = set((e[1] for e in group))
                if codenames.issubset(obj_codenames):
                    pk_list.append(pk)
            objects = queryset.filter(pk__in=pk_list)
            return objects

    if not any_perm and len(codenames) > 1:
        counts = user_obj_perms_queryset.values(
            user_fields[0]).annotate(object_pk_count=Count(user_fields[0]))
        user_obj_perms_queryset = counts.filter(
            object_pk_count__gte=len(codenames))

    values = user_obj_perms_queryset.values_list(user_fields[0], flat=True)
    if user_model.objects.is_generic():
        values = set(values)
    q = Q(pk__in=values)
    if use_groups:
        values = groups_obj_perms_queryset.values_list(group_fields[0], flat=True)
        if group_model.objects.is_generic():
            values = set(values)
        q |= Q(pk__in=values)

    return queryset.filter(q)