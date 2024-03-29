# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.db.models import QuerySet
from django.utils.safestring import SafeString
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import JSONRenderer
from typing import Union, Type, Sequence, Any, Dict
from rest_framework.request import Request

from rest_framework.response import Response

from skipper.core.views import mixin as view_mixins
from skipper.dataseries import constants
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT, DATASERIES_PERMISSION_KEY_CONSUMER
from skipper.dataseries.models.metamodel.base_fact import BaseFact
from skipper.dataseries.models.metamodel.boolean_fact import BooleanFact
from skipper.dataseries.models.metamodel.consumer import Consumer
from skipper.dataseries.models.metamodel.index import UserDefinedIndex, get_indexes_by_target_id
from skipper.dataseries.models.metamodel.dimension import Dimension
from skipper.dataseries.models.metamodel.file_fact import FileFact
from skipper.dataseries.models.metamodel.float_fact import FloatFact
from skipper.dataseries.models.metamodel.image_fact import ImageFact
from skipper.dataseries.models.metamodel.json_fact import JsonFact
from skipper.dataseries.models.metamodel.string_fact import StringFact
from skipper.dataseries.models.metamodel.text_fact import TextFact
from skipper.dataseries.models.metamodel.timestamp_fact import TimestampFact
from skipper.dataseries.serializers.metamodel.base_fact import BaseFactSerializer
from skipper.dataseries.serializers.metamodel.consumer import ConsumerSerializer
from skipper.dataseries.serializers.metamodel.dimension import DimensionSerializer
from skipper.dataseries.serializers.metamodel.facts import StringFactSerializer, TextFactSerializer, \
    TimestampFactSerializer, ImageFactSerializer, JsonFactSerializer, FloatFactSerializer, BooleanFactSerializer, \
    FileFactSerializer
from skipper.dataseries.serializers.metamodel.index import IndexSerializer
from skipper.dataseries.views.common import HasDataSeriesGlobalReadPermission, get_dataseries_permissions_class
from skipper.dataseries.views.contract import get_data_series_object
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.dataseries.views.metamodel.filters import filter_set
from skipper.dataseries.views.metamodel.permissions import metamodel_base_line_permissions


class BaseDataSeriesViewSet(viewsets.GenericViewSet):  # type: ignore
    skipper_base_name: str


def relation_dataseries_child_view_set(
        child_type: Union[
            Type[BaseFact],
            Type[Dimension],
            Type[Consumer],
            Type[UserDefinedIndex]
        ],
        serializer_class_value: Union[
            Type[BaseFactSerializer],
            Type[DimensionSerializer],
            Type[ConsumerSerializer],
            Type[IndexSerializer]
        ],
        skipper_base_name_value: str,
        relation_name: str,
        view_display_name: str,
        view_description_string: str,
        permission_key: str = DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT
) -> Type[BaseDataSeriesViewSet]:
    class ActualViewSet(
        CustomizableBrowsableAPIRendererObjectMixin,
        view_mixins.HttpErrorAwareCreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        mixins.ListModelMixin,
        BaseDataSeriesViewSet
    ):
        skipper_base_name = skipper_base_name_value

        renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

        permission_classes  = (
            *metamodel_base_line_permissions,
            HasDataSeriesGlobalReadPermission,
            get_dataseries_permissions_class(permission_key)
        )


        def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
            instance = self.get_object()
            if issubclass(child_type, BaseFact) or issubclass(child_type, Dimension):
                target_id = instance.id
                indexes_on_this_target = list(get_indexes_by_target_id(target_id))
                if len(indexes_on_this_target) > 0:
                    raise ValidationError({
                        'non_field_errors': ['This object may not be deleted as long as an index is referencing it.']
                    })
            return super().destroy(request, *args, **kwargs)

        def get_description_string(self) -> str:
            return SafeString(view_description_string)

        def get_view_name(self) -> str:
            return view_display_name

        def get_name_string(self) -> str:
            ds_object = get_data_series_object(self.kwargs, permission_key, self.request)
            if ds_object is None:
                raise NotFound()
            if 'pk' in self.kwargs:
                return f'{ds_object.name} - {self.get_view_name()}: {self.get_object().name}'
            else:
                return f'{ds_object.name} - {self.get_view_name()}s'


        serializer_class = serializer_class_value
        pagination_class = None

        filterset_class = filter_set(f'{relation_name}__external_id')

        # hack: we need to keep track whether we already replaced
        # the kwargs or we do twice and cause subsequent get_object calls to fail
        replaced_kwargs_already: bool = False

        def get_object(self) -> Any:
            if not self.replaced_kwargs_already:
                if 'by_external_id' in self.kwargs:
                    self.kwargs['pk'] = get_object_or_404(
                        self.get_queryset().filter(**{
                            f'{relation_name}__external_id': self.kwargs['pk']
                        })).id
                self.replaced_kwargs_already = True
            return super().get_object()

        def get_queryset(self) -> 'QuerySet[Any]':
            data_series = get_data_series_object(self.kwargs, permission_key, self.request)
            if data_series is None:
                return child_type.objects.none()
            else:
                filter: Dict[str, Any] = {
                    f'{relation_name}__data_series': data_series.id
                }
                return child_type.objects \
                    .select_related(relation_name) \
                    .filter(**filter) \
                    .order_by('id') \
                    .all()

    return ActualViewSet


DataSeries_StringFactViewSet = relation_dataseries_child_view_set(
    child_type=StringFact,
    serializer_class_value=StringFactSerializer,
    skipper_base_name_value=constants.data_series_string_fact_base_name,
    relation_name='dataseries_stringfact',
    view_display_name='String Fact',
    view_description_string=f"""
    CRUD API for StringFacts.<br>
    StringFacts are UTF-8 encoded facts limited to 255 chars.
    """
)
DataSeries_TextFactViewSet = relation_dataseries_child_view_set(
    child_type=TextFact,
    serializer_class_value=TextFactSerializer,
    skipper_base_name_value=constants.data_series_text_fact_base_name,
    relation_name='dataseries_textfact',
    view_display_name='Text Fact',
    view_description_string=f"""
    CRUD API for TextFacts.<br>
    TextFacts are UTF-8 encoded facts only limited in length by the underlying storage layer.
    """
)
DataSeries_TimestampFactViewSet = relation_dataseries_child_view_set(
    child_type=TimestampFact,
    serializer_class_value=TimestampFactSerializer,
    skipper_base_name_value=constants.data_series_timestamp_fact_base_name,
    relation_name='dataseries_timestampfact',
    view_display_name='Timestamp Fact',
    view_description_string=f"""
    CRUD API for TimestampFacts.<br>
    TimestampFacts are Timestamps represented in UTC. DataPoints that contain Timestamps
    can be created with Timestamps of other timezones and even internally stored as such, but NF Compose always normalizes
    Timestamps to UTC.
    """
)
DataSeries_ImageFactViewSet = relation_dataseries_child_view_set(
    child_type=ImageFact,
    serializer_class_value=ImageFactSerializer,
    skipper_base_name_value=constants.data_series_image_fact_base_name,
    relation_name='dataseries_imagefact',
    view_display_name='Image Fact',
    view_description_string=f"""
    CRUD API for ImageFacts.<br>
    ImageFacts are not stored directly in the database of NF Compose, but instead inside of
    the S3 compatible object store NF Compose is configured to use. ImageFacts are similar to FileFacts but
    are validated to be proper images. If you have a special file format that is not recognized by default, it
    might be helpful to use a FileFact instead.
    """
)
DataSeries_FileFactViewSet = relation_dataseries_child_view_set(
    child_type=FileFact,
    serializer_class_value=FileFactSerializer,
    skipper_base_name_value=constants.data_series_file_fact_base_name,
    relation_name='dataseries_filefact',
    view_display_name='File Fact',
    view_description_string=f"""
    CRUD API for FileFacts.<br>
    FileFacts are not stored directly in the database of NF Compose, but instead inside of
    the S3 compatible object store NF Compose is configured to use.
    """
)
DataSeries_JsonFactViewSet = relation_dataseries_child_view_set(
    child_type=JsonFact,
    serializer_class_value=JsonFactSerializer,
    skipper_base_name_value=constants.data_series_json_fact_base_name,
    relation_name='dataseries_jsonfact',
    view_display_name='JSON Fact',
    view_description_string=f"""
    CRUD API for JSONFacts.<br>
    JSONFacts are useful whenever you want to store more complex objects in a fact.
    Filtering for JSON Facts is not currently supported, though.
    """
)
DataSeries_FloatFactViewSet = relation_dataseries_child_view_set(
    child_type=FloatFact,
    serializer_class_value=FloatFactSerializer,
    skipper_base_name_value=constants.data_series_float_fact_base_name,
    relation_name='dataseries_floatfact',
    view_display_name='Float Fact',
    view_description_string=f"""
    CRUD API for FloatFacts.<br>
    FloatFacts are numeric double precision floating point values.
    """
)
DataSeries_BooleanFactViewSet = relation_dataseries_child_view_set(
    child_type=BooleanFact,
    serializer_class_value=BooleanFactSerializer,
    skipper_base_name_value=constants.data_series_boolean_fact_base_name,
    relation_name='dataseries_booleanfact',
    view_display_name='Boolean Fact',
    view_description_string=f"""
    CRUD API for BooleanFacts.<br>
    BooleanFacts are simple true/false values.
    """
)
DataSeries_DimensionViewSet = relation_dataseries_child_view_set(
    child_type=Dimension,
    serializer_class_value=DimensionSerializer,
    skipper_base_name_value=constants.data_series_dimension_base_name,
    relation_name='dataseries_dimension',
    view_display_name='Dimension',
    view_description_string=f"""
    CRUD API for Dimensions.<br>
    Dimensions are references to other DataSeries' Datapoints
    """
)

# not really a structure element, but uses the same recipe
DataSeries_ConsumerViewSet = relation_dataseries_child_view_set(
    child_type=Consumer,
    serializer_class_value=ConsumerSerializer,
    skipper_base_name_value=constants.data_series_consumer_base_name,
    relation_name='dataseries_consumer',
    view_display_name='Consumer',
    view_description_string="""
    CRUD API for Consumers.<br>
    Consumers define endpoints that are notified whenever a DataPoint (or multiple)
    is either changed or added.
    <br>
    These Consumers are notified by a POST with a body similar to this: <br>
    
    <pre>
{
    'data_series': {
        'id': &lt;id of dataseries&gt;,
        'external_id': &lt;external id of dataseries&gt;
    },
    'data_points': [{
        'id': &lt;id of datapoint&gt;,
        'external_id': &lt;external id of datapoint&gt;
    },{
        'id': &lt;id of datapoint&gt;,
        'external_id': &lt;external id of datapoint&gt;
    },...]
}</pre>
    
    Consumers can among other things define the required headers (e.g. for authorization purposes),
    as well as the retry or timeout strategy.
    """,
    permission_key=DATASERIES_PERMISSION_KEY_CONSUMER
)
DataSeries_UserDefinedIndexViewSet = relation_dataseries_child_view_set(
    child_type=UserDefinedIndex,
    serializer_class_value=IndexSerializer,
    skipper_base_name_value=constants.data_series_index_base_name,
    relation_name='dataseries_userdefinedindex',
    view_display_name='Index',
    view_description_string="""CRUD API for Indexes on Facts/Dimensions. <br>
    For every index in the dataseries pointing at a Fact/Dimension, <br>
    the underlying database will be optimized for search and ordering operations along this Datapoint attribute.<br>
    Index targets are lists of dictionaries, formatted like this: <br>
<pre>
{
    "targets": [{
        "target_id": &lt;id of fact/dimension&gt;,
        "target_external_id": &lt;external id of fact/dimension&gt;,
        "target_type": &lt;type of target fact/dimension(see below)&gt;
    }, ...]
}</pre>

    target_type must be one of: <br>
    "FLOAT_FACT", "STRING_FACT", "TIMESTAMP_FACT", "TEXT_FACT", "IMAGE_FACT", "FILE_FACT", "JSON_FACT", "BOOLEAN_FACT", "DIMENSION" <br>
    At least one of target_id or target_external_id must be specified. If both are specified, they must match the same Fact/Dimension.
    """,
    permission_key=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT

)
