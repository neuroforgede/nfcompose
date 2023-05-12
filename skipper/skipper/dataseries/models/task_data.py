# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import User
from django.db.models import ForeignKey, DO_NOTHING, BigAutoField, DateTimeField, CASCADE, TextField, BigIntegerField
from django.db.models.base import Model
from django.db.models.fields.json import JSONField  # type: ignore
from django_multitenant.fields import TenantForeignKey  # type: ignore
from django_multitenant.mixins import TenantModelMixin  # type: ignore
from django_multitenant.models import TenantManager  # type: ignore

from skipper.core.models import fields
from skipper.core.models import JSONEncoder
from skipper.core.models.tenant import get_tenant_model
from skipper.dataseries.models.metamodel.data_series import DataSeries

class BulkInsertTaskData(TenantModelMixin, Model):  # type: ignore
    """
    Database model to keep track of the actual data that is to be inserted for
    bulk inserts.
    """
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING, db_constraint=False, db_index=False)

    id = BigAutoField(primary_key=True)

    # no need for an index here even though we filter on it when deleting old data series
    # if this becomes a performance problem, we should think about using partitions instead
    data_series = TenantForeignKey(DataSeries, on_delete=CASCADE, db_constraint=False)

    # we do not have to order by point_in_time as when we need it, we can just order by id
    # which should be enough ordering
    point_in_time = DateTimeField(auto_now_add=False, db_index=False)

    sub_clock = BigIntegerField(null=False, db_index=False)

    # contains validated data and the serialization keys, right now
    # we could separate it out later once we know that we do not need more fields
    # but for now this is just fine and flexible enough
    data = JSONField(null=False, encoder=JSONEncoder)

    last_error = JSONField(null=True, default=None)

    user = ForeignKey(User, on_delete=DO_NOTHING, db_constraint=False, db_index=False)
    record_source = TextField()

    objects: TenantManager = TenantManager()

    @property
    def tenant_field(self) -> str:
        return 'tenant_id'

    class Meta:
        db_table = '_3_bulk_insert_task_data'


class MetaModelTaskData(TenantModelMixin, Model):  # type: ignore
    """
    Database model to keep track of the metamodel task data that change
    e.g. the DDL in the database. These are stored in database so that if
    the celery broker dies, we can at least recover.
    """
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING, db_constraint=False, db_index=False)

    id = fields.id_field()

    task = TextField(null=False, blank=False)

    # no need for an index here even though we filter on it when deleting old data series
    # if this becomes a performance problem, we should think about using partitions instead
    data_series = TenantForeignKey(DataSeries, on_delete=CASCADE, db_constraint=False)

    # we do not have to order by point_in_time as when we need it, we can just order by id
    # which should be enough ordering
    point_in_time = DateTimeField(auto_now_add=False, db_index=True)

    data = JSONField(null=False, encoder=JSONEncoder)

    last_error = JSONField(null=True, default=None)

    user = ForeignKey(User, on_delete=DO_NOTHING, db_constraint=False, db_index=False)
    record_source = TextField()

    objects: TenantManager = TenantManager()

    @property
    def tenant_field(self) -> str:
        return 'tenant_id'

    class Meta:
        db_table = '_3_meta_model_task_data'