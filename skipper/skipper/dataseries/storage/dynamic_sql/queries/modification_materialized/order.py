from typing import List, Tuple, Union, Any
import uuid

from skipper.dataseries.raw_sql import escape
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_column_name
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import data_point_id_column_def

FACT_DIM_TYPES = [
    ('image_facts', 'TEXT COLLATE "pg_catalog"."default"'),
    ('file_facts', 'TEXT COLLATE "pg_catalog"."default"'),
    ('float_facts', 'double precision'),
    ('string_facts', 'character varying(256) COLLATE "pg_catalog"."default"'),
    ('json_facts', 'jsonb'),
    ('dimensions', data_point_id_column_def),
    ('text_facts', 'text'),
    ('boolean_facts', 'BOOLEAN'),
    ('timestamp_facts', 'timestamp with time zone')
]

FACT_DIM_ORDER_IN_SQL = [elem[0] for elem in FACT_DIM_TYPES]

def add_columns_to_list(keys: List[Tuple[str, Union[str, uuid.UUID]]], list: List[Any]) -> None:
    for external_id, uuid in keys:
        column_name = escape.escape(materialized_column_name(uuid, external_id))
        list.append(column_name)
    
def add_columns_to_types_list(keys: List[Tuple[str, Union[str, uuid.UUID]]], col_type: str, list: List[Any]) -> None:
    for external_id, uuid in keys:
        list.append(col_type)