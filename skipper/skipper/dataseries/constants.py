# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from skipper import modules


def skipper_base_name(basename: str) -> str:
    return f'skipper-{modules.url_representation(modules.Module.DATA_SERIES)}-{basename}'


def component_root(component: str) -> str:
    return skipper_base_name(f'{component}-api-root')


root_view_base_name = skipper_base_name('api-root')
data_root_view_base_name = component_root('data')

data_series_base_name = skipper_base_name('dataseries')

node_red_base_name = skipper_base_name('dataseries-nodered')

storage_backend_data_base_name = skipper_base_name('dataseries-storagebackenddata')

prune_data_series_base_name = skipper_base_name('dataseries-prunedataseriesbasename')

data_series_float_fact_base_name = skipper_base_name('dataseries-floatfact')

data_series_string_fact_base_name = skipper_base_name('dataseries-stringfact')

data_series_text_fact_base_name = skipper_base_name('dataseries-textfact')

data_series_timestamp_fact_base_name = skipper_base_name('dataseries-timestampfact')

data_series_image_fact_base_name = skipper_base_name('dataseries-imagefact')

data_series_file_fact_base_name = skipper_base_name('dataseries-filefact')

data_series_json_fact_base_name = skipper_base_name('dataseries-jsonfact')

data_series_boolean_fact_base_name = skipper_base_name('dataseries-booleanfact')

data_series_dimension_base_name = skipper_base_name('dataseries-dimension')

data_series_consumer_base_name = skipper_base_name('dataseries-consumer')

data_series_consumer_event_base_name = skipper_base_name('dataseries-consumer-event')

data_series_index_base_name = skipper_base_name('dataseries-index')

data_series_data_point_base_name = skipper_base_name('dataseries-datapoint')

data_series_history_data_point_base_name = skipper_base_name('dataseries-history-datapoint')

data_series_permission_user_base_name = skipper_base_name('dataseries-permission-user')

data_series_permission_group_base_name = skipper_base_name('dataseries-permission-group')

data_point_example_input_base_name = skipper_base_name('datapoint-example-input')
