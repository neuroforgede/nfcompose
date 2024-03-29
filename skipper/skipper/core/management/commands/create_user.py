# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from getpass import getpass
from typing import Any, List

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from skipper.core.models.tenant import Tenant, Tenant_Group
from skipper.core.models.tenant import Tenant_User


class Command(BaseCommand):
    help = 'creates a new user'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--tenant',
            type=str,
            help='the name of the tenant to use for this user',
            required=True
        )
        parser.add_argument(
            '--username',
            type=str,
            help='username of the user',
            required=True
        )
        parser.add_argument(
            '--group',
            action='append',
            default=list(),
            dest='groups',
            help="groups list [,]"
        )
        parser.add_argument(
            '--password',
            type=str,
            help='password of the user',
            required=False
        )
        parser.add_argument(
            '--staff',
            help='whether the user will have the staff flag set (allowed to see the admin page)',
            action='store_true'
        )
        parser.add_argument(
            '--superuser',
            help='whether the user will be a superuser',
            action='store_true'
        )
        parser.add_argument(
            '--upsert',
            help='whether the user will be updated if it already exists',
            action='store_true'
        )

    def handle(self, tenant: str, username: str, groups: List[str], **options: Any) -> None:  # type: ignore
        with transaction.atomic():
            _password: str = options['password']
            if _password is None:
                self.stdout.write('No password specified, please input one')
                _password = getpass()

            if len(_password) == 0:
                raise ValueError('empty password specified, aborting...')

            _tenant = Tenant.objects.get(name=tenant)

            _groups = set()
            for group_str in set(groups):
                try:
                    _groups.add(Tenant_Group.objects.get(tenant=_tenant, group__name=group_str).group)
                except Tenant_Group.DoesNotExist:
                    raise ValueError(f'did not find group named {group_str} for tenant {tenant}')

            user: User
            if options['upsert']:
                if User.objects.filter(username=username).exists():
                    user = User.objects.get(username=username)

                    if Tenant_User.objects.filter(user=user, system=True).exists():
                        tenant_user = Tenant_User.objects.get(user=user, system=True)
                        if tenant_user.tenant.id != _tenant.id:
                            raise ValueError('User is already assigned to a different tenant')

                    user.is_staff = options['staff']
                    user.is_superuser = options['superuser']
                else:
                    user = User.objects.create(
                        username=username,
                        is_staff=options['staff'],
                        is_superuser=options['superuser']
                    )

                user.groups.set(_groups)
                if not user.check_password(_password):
                    user.set_password(_password)
                else:
                    self.stdout.write(f'password did not change for {user.username}.')
                user.save()

                if not Tenant_User.objects.filter(user=user, system=True).exists():
                    Tenant_User.objects.create(
                        tenant=_tenant,
                        user=user,
                        system=True
                    )

                self.stdout.write(f'successfully upserted user {user.username} and registered it for tenant {tenant}')
            else:
                user = User.objects.create(
                    username=username,
                    is_staff=options['staff'],
                    is_superuser=options['superuser']
                )
                user.set_password(_password)
                user.groups.set(_groups)
                user.save()
                Tenant_User.objects.create(
                    tenant=_tenant,
                    user=user,
                    system=True
                )

                self.stdout.write(f'successfully created user {user.username} and registered it for tenant {tenant}')




