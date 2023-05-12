# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django_multitenant.mixins import TenantModelMixin  # type: ignore
from typing import Optional, Dict, cast, Any, List

from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from rest_framework import views, response
from rest_framework.request import Request

from skipper import modules
from skipper import settings
from skipper.core.views import mixin
from skipper.core.views import util as skipper_view_util


# lets monkey patch django-multitenant to work properly for migrations and code that uses apps.get_model(...)
def monkey_patch_multitenant() -> None:

    def __setattr__(self: Any, attrname: Any, val: Any) -> Any:
        if (
            attrname in ('tenant_id', 'tenant')
            and not self._state.adding
            and val
            and self.tenant_value
            and val != self.tenant_value
            and val != self.tenant_object
        ):
            self._try_update_tenant = True

        return super(TenantModelMixin, self).__setattr__(attrname, val)

    TenantModelMixin.__setattr__ = __setattr__

    @property  # type: ignore
    def tenant_field(self: Any) -> Any:
        return 'tenant_id'

    TenantModelMixin.tenant_field = tenant_field

    @property  # type: ignore
    def tenant_value(self: Any) -> Any:
        return self.tenant_id

    TenantModelMixin.tenant_value = tenant_value

    @property  # type: ignore
    def tenant_object(self: Any) -> Any:
        return self.tenant

    TenantModelMixin.tenant_object = tenant_object


monkey_patch_multitenant()


module_root_view_base_names = {}
problem_root_view_base_names = {}

module_patterns = []
for module, module_settings in settings.SKIPPER_MODULES_SETTINGS.items():
    loaded_module_definition = __import__(module + '.module', fromlist=[''])
    module_patterns.append(
        path(
            module_settings['base_path'] + str(  # type: ignore
                modules.url_representation(loaded_module_definition.get_module())) + '/',
            include(loaded_module_definition.get_urls(module_settings))
        )
    )

    url_representation = modules.url_representation(loaded_module_definition.get_module())

    if 'type' in cast(Dict[str, str], module_settings) and cast(Dict[str, str], module_settings)['type'] == 'problem':
        problem_root_view_base_names[url_representation] = loaded_module_definition.get_root_view_base_name()
    else:
        module_root_view_base_names[url_representation] = loaded_module_definition.get_root_view_base_name()


class Overview(mixin.AllowedToBrowseAPIViewMixin, views.APIView):
    """
    List of loaded modules
    """
    listed_views = module_root_view_base_names

    def get(self, request: Request, format: Optional[str] = None) -> response.Response:
        ret: Dict[str, Any] = {}
        for name, view in module_root_view_base_names.items():
            assert name != 'problems'
            ret[name] = skipper_view_util.get_sub_url_view(view, request)
        return response.Response(data=ret)


admin.site.site_header = 'NF Compose Administration'
admin.site.site_title = 'NF Compose Administration'
admin.site.index_title = 'Admin Overview'


urlpatterns: List[Any] = module_patterns
urlpatterns += [
    path(settings.ROOT_API_PATH, Overview.as_view()),
    path('admin/', admin.site.urls),
    path('', include('django_prometheus.urls'))
]
# for non production environments, we directly serve static files
urlpatterns += cast(Any, static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))