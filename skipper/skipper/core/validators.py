# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy
from jsonschema import Draft7Validator  # type: ignore
from typing import Any, Dict, Optional


@deconstructible
class JSONSchemaData(object):
    schema: Dict[str, Any]
    definitions: Optional[Dict[str, Any]]

    def __init__(self, schema: Dict[str, Any], definitions: Optional[Dict[str, Any]]):
        self.schema = schema
        self.definitions = definitions


@deconstructible
class JSONSchemaValidator(BaseValidator):
    validator: Any

    def __init__(self, json_schema_data: Optional[JSONSchemaData] = None, limit_value: Optional[Any] = None):
        if limit_value is None and json_schema_data is None or limit_value is not None and json_schema_data is not None:
            raise AssertionError('either limit_value or json_schema_data must be set!')
        if limit_value is not None:
            json_schema_data = JSONSchemaData(schema=limit_value, definitions=None)
        if json_schema_data.definitions:
            self.validator = Draft7Validator(dict(definitions=json_schema_data.definitions, **json_schema_data.schema))
        else:
            self.validator = Draft7Validator(json_schema_data.schema)
        super().__init__(limit_value=json_schema_data.schema)

    def compare(self, a: Any, b: Any) -> Any:
        errors = list(self.validator.iter_errors(a))
        if errors:
            raise ValidationError(
                [
                    ValidationError(
                        gettext_lazy("JSONSchema: %(value)s"),
                        params={"value": error.message.replace("\\\\", "\\")},
                        code="jsonschema",
                    )
                    for error in errors
                ]
            )


json_dict_str_str = JSONSchemaValidator(
    json_schema_data=JSONSchemaData(schema={
        "type": "object",
        "properties": {},
        "additionalProperties": {"type": "string"}
    }, definitions=None)
)

json_dict = JSONSchemaValidator(
    json_schema_data=JSONSchemaData(schema={
        "type": "object"
    }, definitions=None)
)
