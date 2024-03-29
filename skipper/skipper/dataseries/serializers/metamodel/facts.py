# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.dataseries import constants
from skipper.dataseries.models.metamodel.boolean_fact import BooleanFact, DataSeries_BooleanFact
from skipper.dataseries.models.metamodel.file_fact import DataSeries_FileFact, FileFact
from skipper.dataseries.models.metamodel.float_fact import FloatFact, DataSeries_FloatFact
from skipper.dataseries.models.metamodel.image_fact import ImageFact, DataSeries_ImageFact
from skipper.dataseries.models.metamodel.json_fact import JsonFact, DataSeries_JsonFact
from skipper.dataseries.models.metamodel.string_fact import StringFact, DataSeries_StringFact
from skipper.dataseries.models.metamodel.text_fact import TextFact, DataSeries_TextFact
from skipper.dataseries.models.metamodel.timestamp_fact import TimestampFact, DataSeries_TimestampFact
from skipper.dataseries.serializers.metamodel.base_fact import generate_fact_serializer
from skipper.dataseries.storage.contract import FactType


FloatFactSerializer = generate_fact_serializer(
    detail_base_name=constants.data_series_float_fact_base_name,
    model_type=FloatFact,
    relation_type=DataSeries_FloatFact,
    fact_type=FactType.Float
)
StringFactSerializer = generate_fact_serializer(
    detail_base_name=constants.data_series_string_fact_base_name,
    model_type=StringFact,
    relation_type=DataSeries_StringFact,
    fact_type=FactType.String
)
TextFactSerializer = generate_fact_serializer(
    detail_base_name=constants.data_series_text_fact_base_name,
    model_type=TextFact,
    relation_type=DataSeries_TextFact,
    fact_type=FactType.Text
)
TimestampFactSerializer = generate_fact_serializer(
    detail_base_name=constants.data_series_timestamp_fact_base_name,
    model_type=TimestampFact,
    relation_type=DataSeries_TimestampFact,
    fact_type=FactType.Timestamp
)
ImageFactSerializer = generate_fact_serializer(
    detail_base_name=constants.data_series_image_fact_base_name,
    model_type=ImageFact,
    relation_type=DataSeries_ImageFact,
    fact_type=FactType.Image
)
FileFactSerializer = generate_fact_serializer(
    detail_base_name=constants.data_series_file_fact_base_name,
    model_type=FileFact,
    relation_type=DataSeries_FileFact,
    fact_type=FactType.File
)
JsonFactSerializer = generate_fact_serializer(
    detail_base_name=constants.data_series_json_fact_base_name,
    model_type=JsonFact,
    relation_type=DataSeries_JsonFact,
    fact_type=FactType.JSON
)
BooleanFactSerializer = generate_fact_serializer(
    detail_base_name=constants.data_series_boolean_fact_base_name,
    model_type=BooleanFact,
    relation_type=DataSeries_BooleanFact,
    fact_type=FactType.Boolean
)