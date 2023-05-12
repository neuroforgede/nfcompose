# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from unittest import TestCase

from skipper.core.models.validation import validate_external_id_sql_safe


class ExternalIdValidationTest(TestCase):

    def test(self) -> None:

        symbols = ['`', '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '{', '[', '}', '}', '|',
                   '\\', ':', ';', ',', "'", '<', '>', '.', '?', '/', u'\u2190', u'\u2191', u'\u00AC', '±', '§',
                   u'\u2524', u'\u2588', u'\u2302', '¾', 'É', 'Õ', 'Æ', '¥', 'Ä', 'µ', '€', '²³']

        for s in symbols:
            self.assertTrue(not validate_external_id_sql_safe(f'external_id{s}'))

        self.assertTrue(not validate_external_id_sql_safe(''))

        self.assertTrue(validate_external_id_sql_safe('external_id'))
        self.assertTrue(validate_external_id_sql_safe('external1'))
        self.assertTrue(validate_external_id_sql_safe('0'))



