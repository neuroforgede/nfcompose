# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from skipper.core.models.tenant import Tenant


class Command(BaseCommand):
    help = 'creates a new tenant'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--name',
            type=str,
            help='the name of the tenant to create',
            required=True
        )
        parser.add_argument(
            '--upsert',
            help='whether the user will be updated if it already exists',
            action='store_true'
        )

    def handle(self, name: str, **options: Any) -> None:  # type: ignore
        with transaction.atomic():
            if Tenant.objects.filter(name=name).exists():
                if options['upsert']:
                    # if we only want to upsert, we do not have to do anything as it stands
                    self.stdout.write(f'successfully upserted tenant with name {name}')
                    return
                raise ValueError(f'tenant with name {name} already exists')
            Tenant.objects.create(
                name=name
            )
            self.stdout.write(f'successfully created tenant with name {name}')


