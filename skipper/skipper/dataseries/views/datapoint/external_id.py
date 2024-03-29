# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Dict, Any, Optional


def use_external_id_as_dimension_identifier(
        url_query_params: Dict[str, Any],
        request_body_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    :param url_query_params:
    :param request_body_data: only has to be set when calling this method directly from a validation call
                              or during representation generation
    :return: whether to use external ids to identify dimensions
    """
    if 'identify_dimensions_by_external_id' in url_query_params:
        _url_val = url_query_params['identify_dimensions_by_external_id']
        return _url_val == 'true' or _url_val == '' or _url_val is None
    if request_body_data is not None and 'identify_dimensions_by_external_id' in request_body_data:
        return bool(request_body_data['identify_dimensions_by_external_id'])
    return False
