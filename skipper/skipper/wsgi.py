# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


"""
WSGI config for skipper project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.http import HttpRequest, HttpResponse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skipper.settings')

application = get_wsgi_application()

orig_get_response = application.get_response
def get_response(request: HttpRequest) -> HttpResponse:
    # required for docker healthcheck
    if request.path == '/healthz/':
        return HttpResponse()
    return orig_get_response(request)  # type: ignore

application.get_response = get_response  # type: ignore