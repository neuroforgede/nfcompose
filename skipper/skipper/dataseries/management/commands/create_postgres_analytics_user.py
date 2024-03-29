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
from skipper.dataseries.models import PostgresAnalyticsUser


class Command(BaseCommand):
    help = 'ensures a PostgresAnalyticsUser is registered for the tenant'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--tenant',
            type=str,
            help='the name of the tenant to use for this user',
            required=True
        )
        parser.add_argument(
            '--role',
            type=str,
            help='name of the role',
            required=True
        )
        parser.add_argument(
            '--upsert',
            help='whether the PostgresAnalyticsUser will be updated if it already exists',
            action='store_true'
        )
        parser.add_argument(
            '--tenant-global-read',
            help='whether the PostgresAnalyticsUser has tenant global read permissions',
            action='store_true'
        )

    def handle(self, tenant: str, role: str, **options: Any) -> None:  # type: ignore
        with transaction.atomic():
            _tenant = Tenant.objects.get(name=tenant)

            # explicitly
            if options['upsert']:
                if PostgresAnalyticsUser.all_objects.filter(
                    tenant=_tenant,
                    role=role
                ).exists():
                    analytics_user: PostgresAnalyticsUser = PostgresAnalyticsUser.all_objects.filter(
                        tenant=_tenant,
                        role=role
                    )[0]
                    analytics_user.deleted_at = None
                    analytics_user.tenant_global_read = options['tenant_global_read']
                    analytics_user.save()
                    # if we only want to upsert, we do not have to do anything as it stands
                    self.stdout.write(f'successfully upserted PostgresAnalyticsUser with role {role}  for tenant {tenant}')
                    return

            if PostgresAnalyticsUser.all_objects.filter(
                tenant=_tenant,
                role=role
            ).exists():
                raise ValueError(f'PostgresAnalyticsUser with role {role} already exists for tenant {tenant}')

            PostgresAnalyticsUser.objects.create(
                tenant=_tenant,
                role=role,
                tenant_global_read=options['tenant_global_read']
            )
            self.stdout.write(f'successfully created PostgresAnalyticsUser with role {role} for tenant {tenant}')




