# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from skipper import modules
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.models.metamodel.boolean_fact import BooleanFact
from skipper.dataseries.models.metamodel.index import UserDefinedIndex, UserDefinedIndex_Target,\
    get_indexes_by_target_id
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType


DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class GetIndexByTargetIdTest(BaseViewTest):

    def test_get_index_by_target_id(self) -> None:
        tenant = Tenant.objects.get(name='default_tenant')

        index = UserDefinedIndex.objects.create(
            tenant=tenant,
            name='idx'
        )
        false_index = UserDefinedIndex.objects.create(
            tenant=tenant,
            name='idx2'
        )

        BooleanFact.objects.create(
            tenant=tenant,
            name='fact',
            optional=True
        )
        false_target = BooleanFact.objects.create(
            tenant=tenant,
            name='fact',
            optional=True
        )

        UserDefinedIndex_Target.objects.create(
            tenant=tenant,
            user_defined_index=index,
            target_id=index.id,
            target_type=IndexableDataSeriesChildType.BOOLEAN_FACT.value,
            target_position_in_index_order=0
        )
        UserDefinedIndex_Target.objects.create(
            tenant=tenant,
            user_defined_index=false_index,
            target_id=false_target.id,
            target_type=IndexableDataSeriesChildType.BOOLEAN_FACT.value,
            target_position_in_index_order=0
        )

        found_indexes = get_indexes_by_target_id(target_id=index.id)
        self.assertTrue(index in found_indexes)
        self.assertEqual(len(found_indexes), 1)
