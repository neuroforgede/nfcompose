# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from typing import Type


class DataSeriesBaseFilterSet(FilterSet):  # type: ignore
    name = CharFilter(method='filter_name_contains')

    def filter_name_contains(self, qs, name, value):  # type: ignore
        return qs.filter(name__icontains=value)


def filter_set(external_id_path: str) -> Type[DataSeriesBaseFilterSet]:
    class ActualFilterSet(DataSeriesBaseFilterSet):
        external_id = CharFilter(field_name=external_id_path,
                                 method='external_id_equal', label='External Id')

        def external_id_equal(self, qs, name, value):  # type: ignore
            return qs.filter(**{external_id_path: value})

    return ActualFilterSet
