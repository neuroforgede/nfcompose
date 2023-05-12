# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.http import QueryDict
from rest_framework.exceptions import ValidationError
from typing import Dict, Any, Set, cast

from formencode.variabledecode import variable_decode  # type: ignore
from rest_framework import parsers


class DataPointMultipartFormencodeParser(parsers.MultiPartParser):

    def parse(self, stream: Any, media_type: Any = None, parser_context: Any = None) -> parsers.DataAndFiles: # type: ignore
        result = cast(parsers.DataAndFiles, super().parse(  # type: ignore
            stream,
            media_type=media_type,
            parser_context=parser_context
        ))

        _data_keys: Set[str] = set(result.data.keys())
        _file_keys: Set[str] = set(result.files.keys())

        _intersect = _file_keys.intersection(_data_keys)
        if len(_intersect) > 0:
            raise ValidationError('files and data had intersection on keys: ' + str(_intersect))

        # merge everything together
        merged = QueryDict(mutable=True)

        merged.update(result.data)
        merged.update(result.files)  # type: ignore

        # TODO: somehow mark the decoded data as "multipart with jsons as string"?

        # decode it together
        decoded_merged = variable_decode(merged)

        parser_context['__JSON_AS_STRING__'] = True

        if len(result.files) > 0:
            # if we had at least one file put everything into files so we
            # later know we had at least one file by running len(request.FILES)
            parser_context['request'].META['SKIPPER_REQUEST_HAD_FILES'] = True
            return parsers.DataAndFiles(decoded_merged, {})  # type: ignore
        else:
            # just put it into data, doesnt matter really otherwise
            return parsers.DataAndFiles(decoded_merged, {})  # type: ignore
