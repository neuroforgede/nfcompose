# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.core.exceptions import ValidationError

from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseViewTest


class TestTenantNaming(BaseViewTest):

    def test(self) -> None:
        symbols = ['`', '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '{', '[', '}', '}', '|',
                   '\\', ':', ';', ',', "'", '<', '>', '.', '?', '/', u'\u2190', u'\u2191', u'\u00AC', '±', '§',
                   u'\u2524', u'\u2588', u'\u2302', '¾', 'É', 'Õ', 'Æ', '¥', 'Ä', 'µ', '€', '²³']

        for s in symbols:
            with self.assertRaises(ValidationError):
                Tenant.objects.create(
                    name=f'name_{s}'
                )
        for s in symbols:
            with self.assertRaises(ValidationError):
                Tenant.objects.create(
                    name=f'{s}_name'
                )
        for s in symbols:
            with self.assertRaises(ValidationError):
                Tenant.objects.create(
                    name=f'name_{s}_name'
                )