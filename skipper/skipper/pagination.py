# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from collections import OrderedDict
from typing import Optional, Any, List, Callable

from django.db.models.query import QuerySet
from django.http import HttpRequest
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination, BasePagination
from rest_framework.request import Request
from rest_framework.response import Response
import base64
import binascii

from skipper import settings

from rest_framework.utils.urls import remove_query_param, replace_query_param  # type: ignore


class StandardResultsSetPagination(PageNumberPagination):
    page_size = settings.DEFAULT_PAGE_SIZE
    page_size_query_param = 'pagesize'
    max_page_size = settings.MAX_PAGE_SIZE


def _positive_int(integer_string: str, strict: bool = False, cutoff: Optional[int] = None) -> int:
    """
    Cast a string to a strictly positive integer.
    """
    ret = int(integer_string)
    if ret < 0 or (ret == 0 and strict):
        raise ValueError()
    if cutoff:
        return min(ret, cutoff)
    return ret


class IdBasedPagination(BasePagination):
    """
    Assumes the id of the model is called "id"
    """
    display_page_controls = False

    last_id = 'last'
    page_size_query_param = 'pagesize'

    page_size = settings.DEFAULT_PAGE_SIZE
    prev_page: Optional[List[Any]]

    # Set to an integer to limit the maximum page size the client may request.
    # Only relevant if 'page_size_query_param' has also been set.
    max_page_size = settings.MAX_PAGE_SIZE

    request: Request

    _next_last_id_object: Optional[Any]

    display_prev_page = True

    def get_page_size(self, request: Any) -> int:
        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size

    def paginate_queryset(self, queryset: QuerySet[Any], request: Any, view: Any = None) -> Optional[List[Any]]:
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        self.page_size_value = page_size

        def b64decode(x: Optional[str]) -> Optional[str]:
            if x is None:
                return None
            try:
                return base64.b64decode(x, validate=True).decode('ascii')
            except UnicodeDecodeError:
                raise ValidationError(f'failed to base64 decode query parameter {self.last_id}')
            except binascii.Error:
                raise ValidationError(f'failed to base64 decode query parameter {self.last_id}')

        def b64encode(x: str) -> str:
            _bytes = x.encode('ascii')
            return base64.b64encode(_bytes).decode('ascii')

        raw_last_id_query = request.query_params.get(self.last_id, None)
        last_id_query = b64decode(raw_last_id_query)

        self.display_prev_page = True
        if hasattr(view, 'should_include_prev_page_for_pagination'):
            self.display_prev_page = view.should_include_prev_page_for_pagination(request)

        self.encode_last_id: Callable[[Any], str] = lambda x: b64encode(str(x))

        if hasattr(view, 'encode_last_id_for_pagination'):
            self.encode_last_id = lambda x: b64encode(view.encode_last_id_for_pagination(x))

        if last_id_query is not None:
            self.prev_link_last_id = last_id_query

            if hasattr(view, 'get_next_page_query_for_pagination'):
                qs = view.get_next_page_query_for_pagination(last_id_query, self.page_size_value + 2, request)
            else:
                qs = queryset.filter(id__gte=last_id_query)

            if hasattr(view, 'get_prev_page_query_for_pagination'):
                rev = view.get_prev_page_query_for_pagination(last_id_query, self.page_size_value + 1, request)
            else:
                rev = qs.reverse().filter(id__lte=self.prev_link_last_id)

            if rev is not None:
                self.prev_page = list(rev[0:self.page_size_value + 1])
            else:
                self.prev_page = None
        else:
            if hasattr(view, 'get_next_page_query_for_pagination'):
                qs = view.get_next_page_query_for_pagination(None, self.page_size_value + 1, request)
            else:
                qs = queryset
            self.prev_link_last_id = None
            self.prev_page = None

        self.request = request
        self.queryset = queryset

        if hasattr(view, 'get_total_count_for_pagination'):
            self.total_count = view.get_total_count_for_pagination(request)
        else:
            self.total_count = queryset.count()

        # we have to actually query the next page_size + 2 elements (if possible)
        # this way, we actually make sure to not generate a next page link if it
        # is not required
        qs_as_list = list(qs[0:page_size + 2])

        _additional_minus = 0
        if len(qs_as_list) == page_size + 2:
            _additional_minus = 1

        _last_id_in_list = False

        if len(qs_as_list) > 0:
            first_id = self.encode_last_id(qs_as_list[0])
            if raw_last_id_query is not None and first_id == raw_last_id_query:
                _last_id_in_list = True
                if len(qs_as_list) > page_size + 1:
                    self._next_last_id_object = qs_as_list[len(qs_as_list) - 1 - _additional_minus]
                else:
                    self._next_last_id_object = None
            else:
                _last_id_in_list = False
                if len(qs_as_list) > page_size:
                    self._next_last_id_object = qs_as_list[len(qs_as_list) - 2 - _additional_minus]
                else:
                    self._next_last_id_object = None
        else:
            _last_id_in_list = False
            self._next_last_id_object = None

        if _last_id_in_list:
            if _additional_minus > 0:
                return qs_as_list[1:-_additional_minus]
            else:
                return qs_as_list[1:]
        else:
            if len(qs_as_list) > page_size:
                return qs_as_list[:-(1+_additional_minus)]
            else:
                return qs_as_list

    def get_paginated_response(self, data: List[Any]) -> Any:  # pragma: no cover
        response_dict = OrderedDict([
            ('next', self.get_next_link())
        ])
        if self.display_prev_page:
            response_dict['previous'] = self.get_prev_link()
        if self.total_count is not None:
            response_dict['count'] = self.total_count
        response_dict['data'] = data
        return Response(response_dict)

    def get_prev_link(self) -> Any:
        if self.prev_page is None:
            return None

        url = self.request.build_absolute_uri()

        if len(self.prev_page) == 0:
            return remove_query_param(url, self.last_id)

        if len(self.prev_page) > self.page_size_value:
            prev_page_last_id = self.encode_last_id(self.prev_page[len(self.prev_page) - 1])

            return replace_query_param(url, self.last_id, prev_page_last_id)
        else:
            return remove_query_param(url, self.last_id)

    def get_next_link(self) -> Any:
        if self._next_last_id_object is None:
            return None

        url = self.request.build_absolute_uri()
        return replace_query_param(url, self.last_id, self.encode_last_id(self._next_last_id_object))

    def get_results(self, data: Any) -> Any:
        return data['results']
