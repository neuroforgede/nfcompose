# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import logging
from django.db import connections, transaction
from django.db.models import Model, CharField, Manager, QuerySet

logger = logging.getLogger(__name__)

POSTGRES_PERMISSIONS_LOCK = "POSTGRES_PERMISSIONS"

# whenever you add something here, be sure to create a migration that re-runs setup_locks!
default_locks = [
    POSTGRES_PERMISSIONS_LOCK
]


class LockManager(Manager):  # type: ignore
    use_in_migrations = True

    def setup_locks(self) -> None:
        with transaction.atomic():
            with connections['default'].cursor() as cursor:
                for lock in default_locks:
                    cursor.execute('LOCK TABLE "_core_lock" IN ACCESS EXCLUSIVE MODE')
                    cursor.execute(f"""
                    INSERT INTO "_core_lock"(key)
                    VALUES(%(lock_key)s)
                    ON CONFLICT DO NOTHING;
                    """, {
                        'lock_key': lock
                    })

    def aquire_lock(self, key: str) -> None:
        qs: 'QuerySet[Lock]' = self.filter(key=key)
        # we have to evaluate the queryset here to get the lock
        logger.info('aquired lock: ' + list(qs.select_for_update())[0].key)


class Lock(Model):
    key = CharField(max_length=100, primary_key=True)

    objects = LockManager()

    class Meta:
        db_table = '_core_Lock'.lower()
