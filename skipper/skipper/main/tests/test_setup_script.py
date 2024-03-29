# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.test import TestCase


class TestSetupScript(TestCase):

    def test_setup_script(self) -> None:
        from skipper.main.management.commands.skipper_local_test_setup import Command
        command = Command()
        command.handle()
