# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG
# All rights reserved
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group
from skipper.core.models.tenant import Tenant
from skipper.core.models.tenant import Tenant_User, Tenant_Group
from skipper.core.models.preshared_token import PreSharedToken
from rest_framework.authtoken.models import Token
from django.contrib import auth
from guardian.shortcuts import assign_perm
from skipper.flow.models import HttpEndpoint

 

tenant_name='blaubeere'

users = [
    "admin"
]
groups = [
    "admin-group"
]

EMAIL_SUFFIX = '@localhost.de'

Tenant.objects.filter(name=tenant_name).exists() \
    or Tenant.objects.create(
        name=tenant_name
    )

tenant = Tenant.objects.get(name=tenant_name)

permissions = set()

# We create (but not persist) a temporary superuser and use it to game the
# system and pull all permissions easily.
tmp_superuser = get_user_model()(
    is_active=True,
    is_superuser=True
)


# We go over each AUTHENTICATION_BACKEND and try to fetch
# a list of permissions
for backend in auth.get_backends():
    if hasattr(backend, "get_all_permissions"):
        permissions.update(backend.get_all_permissions(tmp_superuser))

# Make an sorted list of permissions sorted by permission name.
sorted_list_of_permissions = sorted(list(permissions))


for group_name in groups:
    Group.objects.filter(name=tenant_name + '@@' + group_name).delete()
    Group.objects.create(name=tenant_name + '@@' + group_name)

    group = Group.objects.get(name=tenant_name + '@@' + group_name)

    for perm in sorted_list_of_permissions:
        assign_perm(perm, group)

    # no system group, we need this for scripting
    Tenant_Group.objects.create(group=group, tenant=tenant, system=False)

    # create global flows (bad form to do this here, but works and this script will be replaced by the sidecar soon)
    for http_verb in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        path = '.*'
        method = http_verb
        HttpEndpoint.objects.filter(external_id='all_' + http_verb).exists() \
            or HttpEndpoint.objects.create(
                external_id='all_' + http_verb,
                path=path,
                method=method,
                tenant=tenant,
                system=True
            )
        engine = HttpEndpoint.objects.get(external_id='all_' + http_verb)
        assign_perm('flow.use', group, engine)


for user_name in users:
    # make sure user exists
    User.objects.filter(username=user_name).delete()
    User.objects.create_superuser(user_name, user_name + EMAIL_SUFFIX, user_name)

    user = User.objects.get(username=user_name)
    user.set_password(user_name)
    user.save()

    # make sure user is part of tenant
    Tenant_User.objects.create(user=user, tenant=tenant, system=True)


admin_hardcoded_token = '8x8rypwvhfepienvtorm5adbay6wke6g'
Token.objects.filter(key=admin_hardcoded_token).exists() or Token.objects.create(key=admin_hardcoded_token, user=User.objects.get(username='admin'))
