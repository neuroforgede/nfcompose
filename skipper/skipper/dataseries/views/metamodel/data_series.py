# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import uuid
from django.db.models import QuerySet, Q
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse
from typing import Type, Sequence, cast, Any

from skipper.core.models.guardian import get_objects_for_user_custom
from skipper.core.models.validation import validate_external_id_sql_safe
from skipper.dataseries import constants
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_DATA_SERIES, \
    get_permission_string_for_action_and_http_verb
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
from skipper.dataseries.serializers.metamodel.data_series import DataSeriesSerializer
from skipper.dataseries.views.common import get_dataseries_permissions_class
from skipper.dataseries.views.contract import get_data_series_object, ensure_http_method_globally_allowed
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.dataseries.views.metamodel.filters import filter_set
from skipper.dataseries.views.metamodel.permissions import metamodel_base_line_permissions
from django_filters.rest_framework import MultipleChoiceFilter  # type: ignore

from skipper.dataseries.storage.contract import StorageBackendType  # type: ignore

class DataSeriesFilterSet(filter_set('external_id')):  # type: ignore
    backend = MultipleChoiceFilter(choices=StorageBackendType.choices())

class DataSeriesViewSet(
    CustomizableBrowsableAPIRendererObjectMixin,
    viewsets.ModelViewSet  # type: ignore
):
    """
    DataSeries are the central data type of NF Compose.

    A DataSeries definition consists of a set of facts and dimensions.

    Facts can be of different data types - float, string, text, image, file, ...
    Dimensions are references to datapoints of other DataSeries

    Each DataSeries has a set of DataPoints associated with it.
    Those DataPoints must adhere to the DataSeries definition.
    
    extra_config contains extra configuration parameters for the dataseries.

    These are usually optional parameters such as:
        - auto_clean_history_after_days [int]
        - auto_clean_meta_model_after_days [int]

    Not all dataseries backends support all extra config parameters.
    Backends may also use this to configure special properties that
    are relevant to only them.

    DataSeries and everything below a dataseries module are also accessible via external-ids.
    
    Examples:

    URL to a dataseries:
    http://skipper.local:8000/api/dataseries/by-external-id/dataseries/<dataseries-external-id>/

    URL to a float fact under a dataseries:
    http://skipper.local:8000/api/dataseries/by-external-id/dataseries/<dataseries-external-id>/floatfact/<floatfact-external-id>/

    URL to the datapoint endpoint of a dataseries:
    http://skipper.local:8000/api/dataseries/by-external-id/dataseries/<dataseries-external-id>/datapoint/

    Url to a specific datapoint of a dataseries:
    http://skipper.local:8000/api/dataseries/by-external-id/dataseries/<dataseries-external-id>/datapoint/<datapoint-external-id>/
    """
    skipper_base_name = constants.data_series_base_name

    permission_classes  = [
        *metamodel_base_line_permissions,
        get_dataseries_permissions_class(DATASERIES_PERMISSION_KEY_DATA_SERIES)
    ]

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    ordering = ('id',)
    filterset_class = DataSeriesFilterSet

    action: str

    def get_name_string(self) -> str:
        if 'pk' in self.kwargs:
            _ds_object = self.get_object()
            return f'Data Series {_ds_object.name}'
        else:
            return self.get_view_name()

    # hack: we need to keep track whether we already replaced
    # the kwargs or we do twice and cause subsequent get_object calls to fail
    replaced_kwargs_already: bool = False

    def get_object(self) -> DataSeries:
        if not self.replaced_kwargs_already:
            kwargs_for_query = {
                'data_series': self.kwargs['pk']
            }
            if 'by_external_id' in self.kwargs:
                kwargs_for_query['by_external_id'] = self.kwargs['by_external_id']

            found_ds = get_data_series_object(
                kwargs_object=kwargs_for_query,
                action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
                request=self.request
            )
            # set the kwargs to the pk.
            # if we run with by-external-id this sets the pk properly
            # if we did not run with by-external id this just sets
            # the value properly.
            if found_ds is not None:
                # may be none if not running under by-external-id
                self.kwargs['pk'] = found_ds.id
            
            self.replaced_kwargs_already = True

        return cast(DataSeries, super().get_object())

    def check_object_permissions(self, request: Request, obj: DataSeries) -> None:
        super(DataSeriesViewSet, self).check_object_permissions(request, obj)
        ensure_http_method_globally_allowed(data_series=obj, request=request)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        references_to_this = DataSeries.objects.filter(
            Q(deleted_at__isnull=True) & Q(dataseries_dimension__deleted_at__isnull=True),  # type: ignore
            ~Q(id=instance.id),
            dataseries_dimension__dimension__reference=instance
        )

        if references_to_this.count() > 0:
            visible_references = []
            for referencing_ds in self._qs(references_to_this.all()):
                referencing_data_series_uri = request.build_absolute_uri(
                    reverse(constants.data_series_base_name + '-detail', args=[referencing_ds.id])
                )
                ds_dim: DataSeries_Dimension
                for ds_dim in referencing_ds.dataseries_dimension_set.all():
                    if ds_dim.dimension.reference.id == instance.id:
                        visible_reference = {
                            "data_series": referencing_data_series_uri,
                            "dimension": request.build_absolute_uri(
                                reverse(constants.data_series_dimension_base_name + '-detail', args=[
                                    referencing_ds.id,
                                    ds_dim.dimension.id
                                ])
                            )
                        }
                        visible_references.append(visible_reference)

            # do not give the ids out, as the user might not have all the permissions
            return Response(
                {
                    "non_field_errors": [
                        f'can\'t delete data_series, it is referenced in other data_series.'
                    ],
                    "visible_references": visible_references
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self) -> 'QuerySet[Any]':
        # doing this here also properly filters out everything
        # that is not related to the correct dataseries
        qs = self._qs(DataSeries.objects.all())
        if 'pk' in self.kwargs:
            if 'by_external_id' in self.kwargs:
                if len(qs) == 0 and len(DataSeries.objects.filter(external_id=self.kwargs['pk'])) == 1:
                    raise PermissionDenied()
            else:
                _id = self.kwargs['pk']
                _id_as_uuid: uuid.UUID
                try:
                    _id_as_uuid = uuid.UUID(str(_id))
                except ValueError as e:
                    raise NotFound(f'did not find dataseries with {_id} as it is no valid UUID')
                # this has to be done when fetching the queryset because we need to check OPTIONS requests properly
                if len(qs) == 0 and len(DataSeries.objects.filter(id=_id_as_uuid)) == 1:
                    raise PermissionDenied()
        return qs

    def _qs(self, base_qs: 'QuerySet[DataSeries]') -> 'QuerySet[DataSeries]':
        return get_objects_for_user_custom(
            self.request.user,
            [
                get_permission_string_for_action_and_http_verb(
                    action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
                    http_verb='GET'
                ),
                get_permission_string_for_action_and_http_verb(
                    action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
                    http_verb=self.request.method
                )
            ],
            base_qs,
            True,
            app_label='dataseries'
        )

    def get_serializer_class(self) -> Any:
        return DataSeriesSerializer
