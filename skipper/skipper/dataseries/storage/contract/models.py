from typing import List
from django.db.models import Model

from skipper.core import models

class DisplayDataPoint(Model):
    id = models.string_field(max_length=512, pk=True)
    payload = models.json_field(null=False)
    external_id = models.external_id_field_sql_safe(null=False)
    point_in_time = models.string_field(100, null=False)
    versions = models.json_field(null=True)
    pagination_data = models.json_field(null=False)

    class Meta:
        managed = False
        default_permissions: List[str] = []
        db_table = 'DOES_NOT_EXIST'