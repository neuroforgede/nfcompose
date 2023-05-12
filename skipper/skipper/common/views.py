# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any
from django.http.response import HttpResponse

from django.shortcuts import render
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required

from skipper.settings import LOGIN_URL

version: str
with open('skipper/static-private/version.txt') as version_file:
    version = version_file.read().replace('\n', '')

licenses: str
with open('skipper/static-private/OPENSOURCE_LICENSES.html') as licenses_file:
    licenses = licenses_file.read().replace('\n', '')

@permission_classes([IsAuthenticated])
@login_required(login_url='/' + LOGIN_URL)
def licensing_view(request: Any) -> Any:
    if request.method == 'GET':
        return render(request, 'skipper/licensing.html', {
            'name': 'Licensing',
            'version': version
        })

@permission_classes([IsAuthenticated])
@login_required(login_url='/' + LOGIN_URL)
def licensing_oss_view(request: Any) -> Any:
    return HttpResponse(content=licenses, content_type='text/html')