# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from rest_framework import status
from typing import Any, Dict

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DataSeriesByExternalIdBasicTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'by-external-id/dataseries/'
    simulate_other_tenant = True

    def check_urls_by_external_id(self, data_series: Dict[str, Any]) -> None:
        # by-external-id functionality should work, but not be the default, so we should still always give out
        # the canonical url, as this will always work
        self.assertRegexpMatches(data_series['url'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/')
        self.assertRegexpMatches(data_series['dimensions'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/dimension/')
        self.assertRegexpMatches(data_series['json_facts'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/jsonfact/')
        self.assertRegexpMatches(data_series['timestamp_facts'],
                                 DATA_SERIES_BASE_URL + r'dataseries/(.*)/timestampfact/')
        self.assertRegexpMatches(data_series['file_facts'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/filefact/')
        self.assertRegexpMatches(data_series['image_facts'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/imagefact/')
        self.assertRegexpMatches(data_series['float_facts'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/floatfact/')
        self.assertRegexpMatches(data_series['boolean_facts'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/booleanfact/')
        self.assertRegexpMatches(data_series['text_facts'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/textfact/')
        self.assertRegexpMatches(data_series['string_facts'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/stringfact/')

        self.assertRegexpMatches(data_series['data_points'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/datapoint/')

        self.assertRegexpMatches(data_series['data_points_bulk'],
                                 DATA_SERIES_BASE_URL + r'dataseries/(.*)/bulk/datapoint/')
        self.assertRegexpMatches(data_series['data_point_validate_external_ids'],
                                 DATA_SERIES_BASE_URL + r'dataseries/(.*)/bulk/check-external-ids/')

        self.assertRegexpMatches(data_series['cube_sql'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/cubesql/')
        self.assertRegexpMatches(data_series['create_view'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/createview/')

    def check_urls_by_external_id_dp(self, data_point: Dict[str, Any]) -> None:
        self.assertRegexpMatches(data_point['url'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/datapoint/(.*)/')

    def check_urls_by_external_id_fact(self, fact: Dict[str, Any], fact_type: str) -> None:
        self.assertRegexpMatches(fact['url'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/' + fact_type + 'fact/(.*)/')

    def check_urls_by_external_id_dimension(self, fact: Dict[str, Any]) -> None:
        self.assertRegexpMatches(fact['url'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/dimension/(.*)/')

        self.assertRegexpMatches(fact['reference'], DATA_SERIES_BASE_URL + r'dataseries/(.*)/')

    def test_create_broken_url_data_series(self) -> None:
        # for dataseries it should be impossible to create weird situations where
        # url characters are used in the external id
        should_fail = self.client.post(self.url_under_test, data={
            'name': 'my_data_series_1',
            'external_id': '/'
        }, format='json')
        self.assertEquals(status.HTTP_400_BAD_REQUEST, should_fail.status_code)

    def test_create_and_fetch_via_external_id_in_url(self) -> None:
        data_series = self.create_payload(self.url_under_test, payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

        manual_url_response = self.client.get(self.url_under_test + 'external_id1/')
        self.assertEquals(status.HTTP_200_OK, manual_url_response.status_code)
        self.assertEquals(data_series, manual_url_response.json())

    def test_returned_has_correct_paths(self) -> None:
        data_series = self.create_payload(self.url_under_test, payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)
        self.check_urls_by_external_id(data_series)

    def test_data_point_is_accessible_via_external_id_url(self) -> None:
        data_series = self.create_payload(self.url_under_test, payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

        data_point = self.create_payload(self.url_under_test + f'{data_series["external_id"]}/datapoint/', payload={
            'external_id': '1',
            'payload': {}
        })
        self.check_urls_by_external_id_dp(data_point)

        should_redirect = self.client.get(path=self.url_under_test + 'external_id1/datapoint/1')
        self.assertEquals(status.HTTP_301_MOVED_PERMANENTLY, should_redirect.status_code)

        by_external_id_dp = self.get_payload(self.url_under_test + 'external_id1/datapoint/1/')
        self.assertEquals(data_point, by_external_id_dp)

        # url in the returned json should still be the canonical url as that is always safe
        self.check_urls_by_external_id_dp(data_point)

    def test_facts_are_accessible_via_external_id_url(self) -> None:
        for fact_type in ['float', 'string', 'text', 'json', 'image', 'boolean']:
            external_id_ds = f'external_id_{fact_type}'
            data_series = self.create_payload(self.url_under_test, payload={
                'name': 'my_data_series_1',
                'external_id': external_id_ds
            }, simulate_tenant=False)

            external_id_fact = f'my_awesome_{fact_type}_fact'

            fact = self.create_payload(self.url_under_test + f'{data_series["external_id"]}/{fact_type}fact/', payload={
                'name': f'{external_id_fact}_name',
                'external_id': external_id_fact,
                'optional': False
            }, simulate_tenant=False)
            self.check_urls_by_external_id_fact(fact, fact_type)

            should_redirect = self.client.get(
                path=self.url_under_test + f'{data_series["external_id"]}/{fact_type}fact/{external_id_fact}'
            )
            self.assertEquals(status.HTTP_301_MOVED_PERMANENTLY, should_redirect.status_code)

            by_external_id_fact = self.get_payload(self.url_under_test + f'{data_series["external_id"]}/{fact_type}fact/{external_id_fact}/')
            self.check_urls_by_external_id_fact(fact, fact_type)
            self.assertEquals(fact, by_external_id_fact)

    def test_dimensions_are_accessible_via_external_id_url(self) -> None:
        external_id_ds = f'external_id_dim'
        data_series = self.create_payload(self.url_under_test, payload={
            'name': 'my_data_series_1',
            'external_id': external_id_ds
        }, simulate_tenant=False)

        data_series_for_dim = self.create_payload(self.url_under_test, payload={
            'name': 'my_data_series_2',
            'external_id': external_id_ds + '_2'
        }, simulate_tenant=False)

        external_id_dim = f'my_awesome_dim'

        dim = self.create_payload(self.url_under_test + f'{data_series["external_id"]}/dimension/', payload={
            'name': f'{external_id_dim}_name',
            'external_id': external_id_dim,
            'optional': False,
            'reference': data_series_for_dim['url']
        }, simulate_tenant=False)
        self.check_urls_by_external_id_dimension(dim)

        should_redirect = self.client.get(
            path=self.url_under_test + f'{data_series["external_id"]}/dimension/{external_id_dim}'
        )
        self.assertEquals(status.HTTP_301_MOVED_PERMANENTLY, should_redirect.status_code)

        by_external_id_dim = self.get_payload(self.url_under_test + f'{data_series["external_id"]}/dimension/{external_id_dim}/')
        self.check_urls_by_external_id_dimension(dim)
        self.assertEquals(dim, by_external_id_dim)
