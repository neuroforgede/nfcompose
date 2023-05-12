# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any, Dict

from django.db.models import Model
from rest_framework import serializers
from rest_framework.request import Request


class MultipleParameterHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        raise NotImplementedError()

    def get_url(self, obj: Model, view_name: str, request: Request, format: str) -> Any:
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = dict(self.get_extra_lookup_url_kwargs(obj, view_name, request, format))
        kwargs[self.lookup_url_kwarg] = lookup_value
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)  # type: ignore

    def get_object(self, view_name: str, *view_args: Any, **view_kwargs: Any) -> Model:
        # hack so that pycharm does not complain
        if 1 == 1:
            raise NotImplementedError('not supported!')
        raise NotImplementedError('not supported!')
