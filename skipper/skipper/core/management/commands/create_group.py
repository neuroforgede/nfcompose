# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from skipper.core.models.tenant import Tenant, Tenant_Group


class Command(BaseCommand):
    help = 'creates a new group'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--tenant',
            type=str,
            help='the name of the tenant to use for this user',
            required=True
        )
        parser.add_argument(
            '--name',
            type=str,
            help='name of the group',
            required=True
        )
        parser.add_argument(
            '--upsert',
            help='whether the group will be updated if it already exists',
            action='store_true'
        )

    def handle(self, tenant: str, name: str, **options: Any) -> None:  # type: ignore
        with transaction.atomic():
            _tenant = Tenant.objects.get(name=tenant)

            group: Group
            if options['upsert']:
                if Group.objects.filter(name=name).exists():
                    group = Group.objects.get(name=name)

                    if Tenant_Group.objects.filter(group=group, system=True).exists():
                        tenant_group = Tenant_Group.objects.get(group=group, system=True)
                        if tenant_group.tenant.id != _tenant.id:
                            raise ValueError('User is already assigned to a different tenant')

                else:
                    group = Group.objects.create(
                        name=name
                    )

                group.save()

                if not Tenant_Group.objects.filter(group=group, system=True).exists():
                    Tenant_Group.objects.create(
                        tenant=_tenant,
                        group=group,
                        system=True
                    )

                self.stdout.write(f'successfully upserted group {group.name} and registered it for tenant {tenant}')
            else:
                group = Group.objects.create(
                    name=name
                )
                group.save()
                Tenant_Group.objects.create(
                    tenant=_tenant,
                    group=group,
                    system=True
                )

                self.stdout.write(f'successfully created group {group.name} and registered it for tenant {tenant}')


