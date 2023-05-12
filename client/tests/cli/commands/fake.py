# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from compose_client.library.utils.types import JSONType


def fake_data_series_rest_list_entry(base_url: str, data_series_id: str, point_in_time: str,
                                     data_series_external_id: str) -> JSONType:
    return {
        "url": f"{base_url}/api/dataseries/dataseries/{data_series_id}/",
        "id": f"{data_series_id}",
        "external_id": data_series_external_id,
        "point_in_time": point_in_time,
        "last_modified_at": point_in_time,
        "name": data_series_external_id,
        "locked": False,
        "backend": "DYNAMIC_SQL_MATERIALIZED",
        "extra_config": {
            "auto_clean_history_after_days": -1,
            "auto_clean_meta_model_after_days": -1
        },
        "allow_extra_fields": False,
        "dimensions": f"{base_url}/api/dataseries/dataseries/{data_series_id}/dimension/",
        "float_facts": f"{base_url}/api/dataseries/dataseries/{data_series_id}/floatfact/",
        "string_facts": f"{base_url}/api/dataseries/dataseries/{data_series_id}/stringfact/",
        "text_facts": f"{base_url}/api/dataseries/dataseries/{data_series_id}/textfact/",
        "timestamp_facts": f"{base_url}/api/dataseries/dataseries/{data_series_id}/timestampfact/",
        "image_facts": f"{base_url}/api/dataseries/dataseries/{data_series_id}/imagefact/",
        "file_facts": f"{base_url}/api/dataseries/dataseries/{data_series_id}/filefact/",
        "json_facts": f"{base_url}/api/dataseries/dataseries/{data_series_id}/jsonfact/",
        "boolean_facts": f"{base_url}/api/dataseries/dataseries/{data_series_id}/booleanfact/",
        "consumers": f"{base_url}/api/dataseries/dataseries/{data_series_id}/consumer/",
        "data_points": f"{base_url}/api/dataseries/dataseries/{data_series_id}/datapoint/",
        "history_data_points": f"{base_url}/api/dataseries/dataseries/{data_series_id}/history/datapoint/",
        "data_points_bulk": f"{base_url}/api/dataseries/dataseries/{data_series_id}/bulk/datapoint/",
        "data_point_validate_external_ids": f"{base_url}/api/dataseries/dataseries/{data_series_id}/bulk/check-external-ids/",
        "cube_sql": f"{base_url}/api/dataseries/dataseries/{data_series_id}/cubesql/",
        "create_view": f"{base_url}/api/dataseries/dataseries/{data_series_id}/createview/",
        "prune_history": f"{base_url}/api/dataseries/dataseries/{data_series_id}/prune/history/",
        "prune_meta_model": f"{base_url}/api/dataseries/dataseries/{data_series_id}/prune/metamodel/",
        "truncate": f"{base_url}/api/dataseries/dataseries/{data_series_id}/truncate/",
        "permission_user": f"{base_url}/api/dataseries/dataseries/{data_series_id}/permission/user/",
        "permission_group": f"{base_url}/api/dataseries/dataseries/{data_series_id}/permission/group/",
        "data_point_structure": {
            "external_id": "required: external_id",
            "payload": {
                # no payload here, or we have to mock that out as well
            }
        }
    }


def fake_data_series_gets(
        base_url: str,
        ds_1_id: str,
        ds_1_external_id: str,
        ds_2_id: str,
        ds_2_external_id: str
  ) -> JSONType:
    ds_1 = fake_data_series_rest_list_entry(base_url, ds_1_id, "2021-02-06T11:05:59.764287Z", ds_1_external_id)
    ds_2 = fake_data_series_rest_list_entry(base_url, ds_2_id, "2021-02-06T11:05:59.764287Z", ds_2_external_id)

    detail_urls = [
        {
            elem['url']: elem,
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/dimension/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/floatfact/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/stringfact/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/textfact/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/timestampfact/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/imagefact/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/filefact/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/jsonfact/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/booleanfact/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/consumer/": [],
            f"{base_url}/api/dataseries/dataseries/{elem['id']}/permission/group/": {
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            }
        }
        for elem in [ds_1, ds_2]
    ]

    ret = {
        f'{base_url}/api/dataseries/dataseries/': {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                ds_1,
                ds_2
            ]
        }
    }
    for urls in detail_urls:
        ret = {
            **ret,
            **urls
        }

    return ret

