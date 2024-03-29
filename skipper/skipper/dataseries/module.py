# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.conf.urls import include
from django.contrib import admin
from django.urls import path, re_path
from rest_framework import routers
from typing import Any, List, Dict

from skipper import modules
from skipper.core.feature_flags import get_feature_flag
from skipper.core.utils.router import DefaultRouter
from skipper.core.views import mixin
from skipper.core.views.module import APIOverviewView
from skipper.dataseries import constants
from skipper.dataseries.admin import DataSeriesAdmin, ConsumerEventAdmin, ConsumerAdmin, PostgresAnalyticsUserAdmin, \
    BulkInsertTaskDataAdmin, MetaModelTaskDataAdmin
from skipper.dataseries.models import ConsumerEvent, BulkInsertTaskData, MetaModelTaskData
from skipper.dataseries.models.analytics import PostgresAnalyticsUser
from skipper.dataseries.models.metamodel.consumer import Consumer
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.views.datapoint.bulk import DataSeriesBulkCreateView
from skipper.dataseries.views.datapoint.check_external_id import DataSeriesCheckExternalIdsView
from skipper.dataseries.views.datapoint.crud import DataSeries_DataPointViewSet, history_DataSeries_DataPointViewSet
from skipper.dataseries.views.event import DataSeries_ConsumerEventViewSet
from skipper.dataseries.views.metamodel.create_view import DataSeriesCreateViewView
from skipper.dataseries.views.metamodel.cube_sql import DataSeriesCubeSQLView
from skipper.dataseries.views.metamodel.data_series import DataSeriesViewSet
from skipper.dataseries.views.metamodel.data_series_permission_group import DataSeriesPermissionGroupViewSet
from skipper.dataseries.views.metamodel.data_series_permission_user import DataSeriesPermissionUserViewSet
from skipper.dataseries.views.metamodel.prune_history import DataSeriesPruneHistoryView
from skipper.dataseries.views.metamodel.prune_metamodel import DataSeriesPruneMetaModelView
from skipper.dataseries.views.metamodel.structure import \
    DataSeries_UserDefinedIndexViewSet, DataSeries_StringFactViewSet, DataSeries_TextFactViewSet, \
    DataSeries_TimestampFactViewSet, DataSeries_ImageFactViewSet, DataSeries_JsonFactViewSet, \
    DataSeries_FloatFactViewSet, DataSeries_DimensionViewSet, DataSeries_BooleanFactViewSet, \
    DataSeries_FileFactViewSet, DataSeries_ConsumerViewSet
from skipper.dataseries.views.metamodel.truncate import DataSeriesTruncateView
from skipper.dataseries.views.prune_data_series import PruneDataSeriesView
from skipper.dataseries.views.storages import storage_backend_data_view

admin.site.register(DataSeries, DataSeriesAdmin)
admin.site.register(Consumer, ConsumerAdmin)
admin.site.register(ConsumerEvent, ConsumerEventAdmin)
admin.site.register(PostgresAnalyticsUser, PostgresAnalyticsUserAdmin)
admin.site.register(BulkInsertTaskData, BulkInsertTaskDataAdmin)
admin.site.register(MetaModelTaskData, MetaModelTaskDataAdmin)


def get_module() -> modules.Module:
    return modules.Module.DATA_SERIES


def get_root_view_base_name() -> str:
    return constants.root_view_base_name


class DataSeriesAPIView(mixin.AllowedToBrowseAPIViewMixin, routers.APIRootView):
    pass


class DataSeriesRouter(DefaultRouter):
    APIRootView = DataSeriesAPIView

    # only needed for component style modules
    # root_view_name = constants.data_root_view_base_name
    root_view_name = constants.root_view_base_name

    skipper_base_name = constants.root_view_base_name


def get_urls(module_settings: Dict[str, Any]) -> List[Any]:
    _listed_views: Dict[str, Any] = {
        'dataseries': DataSeriesViewSet.skipper_base_name + '-list',
        'storage_backend_data': constants.storage_backend_data_base_name + '-root',
        'prune_dataseries': PruneDataSeriesView.skipper_base_name
    }

    class DataSeriesAPIView(APIOverviewView):
        """
        Overview for the DataSeries API
        """
        skipper_base_name = constants.root_view_base_name
        listed_views = _listed_views

    router = DataSeriesRouter()

    router.register(
        r'dataseries',
        DataSeriesViewSet,
        basename=DataSeriesViewSet.skipper_base_name)

    router.register(
        r'(?P<by_external_id>by-external-id)/dataseries',
        DataSeriesViewSet,
        basename=DataSeriesViewSet.skipper_base_name + 'by-external-id')

    def _register(pattern: str, viewset: Any, basename: str) -> None:
        router.register('(?P<by_external_id>by-external-id)/' + pattern,
                        viewset,
                        basename=basename + 'by-external-id')
        router.register(pattern,
                        viewset,
                        basename=basename)

    _register(r'dataseries/(?P<data_series>[^/.]+)/floatfact',
              DataSeries_FloatFactViewSet,
              basename=DataSeries_FloatFactViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/stringfact',
              DataSeries_StringFactViewSet,
              basename=DataSeries_StringFactViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/textfact',
              DataSeries_TextFactViewSet,
              basename=DataSeries_TextFactViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/timestampfact',
              DataSeries_TimestampFactViewSet,
              basename=DataSeries_TimestampFactViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/imagefact',
              DataSeries_ImageFactViewSet,
              basename=DataSeries_ImageFactViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/filefact',
              DataSeries_FileFactViewSet,
              basename=DataSeries_FileFactViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/jsonfact',
              DataSeries_JsonFactViewSet,
              basename=DataSeries_JsonFactViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/booleanfact',
              DataSeries_BooleanFactViewSet,
              basename=DataSeries_BooleanFactViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/dimension',
              DataSeries_DimensionViewSet,
              basename=DataSeries_DimensionViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/consumer',
              DataSeries_ConsumerViewSet,
              basename=DataSeries_ConsumerViewSet.skipper_base_name)

    if get_feature_flag("compose.structure.indexes"):
        _register(r'dataseries/(?P<data_series>[^/.]+)/index',
              DataSeries_UserDefinedIndexViewSet,
              basename=DataSeries_UserDefinedIndexViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/consumer/(?P<consumer>[^/.]+)/event',
              DataSeries_ConsumerEventViewSet,
              basename=DataSeries_ConsumerEventViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/datapoint',
              DataSeries_DataPointViewSet,
              basename=DataSeries_DataPointViewSet.skipper_base_name)

    _register(r'dataseries/(?P<data_series>[^/.]+)/history/datapoint',
              history_DataSeries_DataPointViewSet,
              basename=history_DataSeries_DataPointViewSet.skipper_base_name)

    _register(
        r'dataseries/(?P<data_series>[^/.]+)/permission/user',
        DataSeriesPermissionUserViewSet,
        basename=DataSeriesPermissionUserViewSet.skipper_base_name
    )

    _register(
        r'dataseries/(?P<data_series>[^/.]+)/permission/group',
        DataSeriesPermissionGroupViewSet,
        basename=DataSeriesPermissionGroupViewSet.skipper_base_name
    )

    urls = [
        path('', DataSeriesAPIView.as_view(), name=DataSeriesAPIView.skipper_base_name),
        path(r'storage/data/', storage_backend_data_view, name=constants.storage_backend_data_base_name + '-root'),
        path(f'prune/dataseries/', PruneDataSeriesView.as_view(), name=PruneDataSeriesView.skipper_base_name),
        path(
            '',
            include(router.urls)
        ),
    ]

    def add_view(pattern: str, view: Any, name: str) -> None:
        urls.extend([
            re_path(
                '^' + pattern,
                view.as_view(),
                name=name
            ),
            re_path(
                '^by-external-id/' + pattern,
                view.as_view(),
                name=name + 'by-external-id',
                kwargs={
                    # does not matter what we set here, we only need it to be present
                    "by_external_id": True
                }
            ),
        ])

    add_view(
        r'dataseries/(?P<data_series>[^/.]+)/bulk/datapoint/',
        DataSeriesBulkCreateView,
        name=constants.data_series_data_point_base_name + '-create-bulk'
    )

    add_view(
        r'dataseries/(?P<data_series>[^/.]+)/bulk/check-external-ids/',
        DataSeriesCheckExternalIdsView,
        name=constants.data_series_data_point_base_name + '-check-external-ids'
    )

    add_view(
        r'dataseries/(?P<data_series>[^/.]+)/createview/',
        DataSeriesCreateViewView,
        name=constants.data_series_base_name + '-createview'
    )

    add_view(
        r'dataseries/(?P<data_series>[^/.]+)/prune/history/',
        DataSeriesPruneHistoryView,
        name=constants.data_series_base_name + '-prune-history'
    )

    add_view(
        r'dataseries/(?P<data_series>[^/.]+)/prune/metamodel/',
        DataSeriesPruneMetaModelView,
        name=constants.data_series_base_name + '-prune-metamodel'
    )

    add_view(
        r'dataseries/(?P<data_series>[^/.]+)/truncate/',
        DataSeriesTruncateView,
        name=constants.data_series_base_name + '-truncate'
    )

    add_view(
        r'dataseries/(?P<data_series>[^/.]+)/cubesql/',
        DataSeriesCubeSQLView,
        name=constants.data_series_base_name + '-cubesql'
    )

    return urls
