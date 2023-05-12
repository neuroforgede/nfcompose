# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from getpass import getpass
from typing import Any, List

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = 'creates a new user'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--username',
            type=str,
            help='username of the user',
            required=True
        )
        parser.add_argument(
            '--token',
            type=str,
            help='token to set for the user',
            required=True
        )

    def handle(self, username: str, token: str, **options: Any) -> None:  # type: ignore
        with transaction.atomic():
            if len(token) == 0:
                raise ValueError('empty token specified, aborting...')

            user: User = User.objects.get(username=username)

            if Token.objects.filter(user=user).exists():
                token_obj: Token = Token.objects.get(user=user)
                token_obj.delete()

            Token.objects.create(
                key=token,
                user=user
            )

            self.stdout.write(f'successfully set token for user {user.username}')




