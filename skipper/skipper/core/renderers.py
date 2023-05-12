# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.http import Http404
from rest_framework.exceptions import NotFound, APIException, ValidationError
from rest_framework.renderers import BrowsableAPIRenderer, HTMLFormRenderer
from typing import Any, Mapping, Dict, Optional
from django.template import engines, loader
from rest_framework import serializers

def get_class(elem: Any) -> Any:
    if hasattr(elem, '_proxy_class'):
        # Deal with proxy classes. Ie. BoundField behaves as if it
        # is a Field instance when using ClassLookupDict.
        base_class = elem._proxy_class
    else:
        base_class = elem.__class__
    return base_class


class FixedHTMLFormRenderer(HTMLFormRenderer):
    def render_field(self, field: Any, parent_style: Any) -> Any:
        if isinstance(field._field, serializers.HiddenField):
            return ''

        style = self.default_style[field].copy()
        style.update(field.style)
        if 'template_pack' not in style:
            style['template_pack'] = parent_style.get('template_pack', self.template_pack)
        style['renderer'] = self

        # Get a clone of the field with text-only value representation.
        field = field.as_form_field()

        if style.get('input_type') == 'datetime-local' and isinstance(field.value, str):
            field.value = field.value.rstrip('Z')

        if 'template' in style:
            template_name = style['template']
        else:
            template_name = style['template_pack'].strip('/') + '/' + style['base_template']

        template = loader.get_template(template_name)

        # we splice in the label manually, fallback to default behaviour
        try:
            context = {'label': field._field.label, 'field': field, 'style': style}
        except:
            context = {'field': field, 'style': style}
        return template.render(context)
    

class CustomizableBrowsableAPIRenderer(BrowsableAPIRenderer):
    form_renderer_class = FixedHTMLFormRenderer

    def get_context(self, data: Any, accepted_media_type: str, renderer_context: Mapping[str, Any]) -> Dict[str, Any]:
        base_ctx = super().get_context(data, accepted_media_type, renderer_context)

        view = renderer_context['view']
        if hasattr(view, 'get_description_string'):
            try:
                base_ctx['description'] = view.get_description_string()
            except APIException:
                pass
            except Http404:
                pass

        if hasattr(view, 'get_name_string'):
            try:
                base_ctx['name'] = view.get_name_string()
            except APIException:
                # PermissionDenied, NotFound are really relevant here, but
                # its better to not display anything than failing completely
                pass
            except Http404:
                pass

        return base_ctx


class CustomizableBrowsableAPIRendererObjectMixin(object):
    def get_object_or_None(self) -> Optional[Any]:
        try:
            return self.get_object()  # type: ignore
        except Http404:
            return None
        except NotFound:
            return None




