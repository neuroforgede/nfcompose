# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.contrib.auth import get_user_model
from django.db.models import ForeignKey, CharField
from django.db.models.deletion import CASCADE

from skipper.core.models import softdelete
from skipper.core.models import fields


class PreSharedToken(softdelete.SoftDeletionModel):
    id = fields.id_field()
    key = CharField(
        unique=True,
        null=False,
        blank=False,
        max_length=256,
        help_text="The actual preshared token credential. Must be unique across all users in the whole system"
    )
    user = ForeignKey(get_user_model(), on_delete=CASCADE, help_text="the user this token is referring to")

    class Meta:
        db_table = '_core_PreSharedToken'.lower()

