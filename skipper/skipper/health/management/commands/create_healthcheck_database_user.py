# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from skipper.health.models import HealthCheckDatabaseUser


class Command(BaseCommand):
    help = 'ensures a HealthCheckDatabaseUser is registered for the tenant'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--role',
            type=str,
            help='name of the role',
            required=True
        )
        parser.add_argument(
            '--upsert',
            help='whether the HealthCheckDatabaseUser will be updated if it already exists',
            action='store_true'
        )

    def handle(self, role: str, **options: Any) -> None:  # type: ignore
        with transaction.atomic():
            # explicitly
            if options['upsert']:
                if HealthCheckDatabaseUser.all_objects.filter(
                    role=role
                ).exists():
                    analytics_user: HealthCheckDatabaseUser = HealthCheckDatabaseUser.all_objects.filter(
                        role=role
                    )[0]
                    analytics_user.deleted_at = None
                    analytics_user.save()
                    # if we only want to upsert, we do not have to do anything as it stands
                    self.stdout.write(f'successfully upserted HealthCheckDatabaseUser with role {role}')
                    return

            if HealthCheckDatabaseUser.all_objects.filter(
                role=role
            ).exists():
                raise ValueError(f'HealthCheckDatabaseUser with role {role} already exists')

            HealthCheckDatabaseUser.objects.create(
                role=role,
            )
            self.stdout.write(f'successfully created HealthCheckDatabaseUser with role {role}')




