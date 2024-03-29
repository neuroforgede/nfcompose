# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.http import HttpRequest
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from typing import Any, Sequence, Type, Dict, List

from skipper.core.views.mixin import HasTenantSetPermission
from skipper.dataseries import constants
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.serializers.prune_data_series import PruneDataSeriesSerializer
from skipper.dataseries.storage import actions
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.core.renderers import CustomizableBrowsableAPIRendererObjectMixin


class PruneDataSeriesPermission(BasePermission):

    def has_permission(self, request: HttpRequest, view: Any) -> bool:
        user = request.user
        if user is None:
            return False
        else:
            if user.is_superuser:
                return True
            if user.has_perm('dataseries.prune_data_series'):
                return True
            return False


class PruneDataSeriesView(CustomizableBrowsableAPIRendererObjectMixin, GenericAPIView):  # type: ignore
    """
    Prune deleted DataSeries. All data deleted in this manner is unrecoverable outside of backups.
    """
    skipper_base_name = constants.prune_data_series_base_name

    permission_classes  = (
        permissions.IsAuthenticated,
        HasTenantSetPermission,
        PruneDataSeriesPermission,
    )

    def get_view_name(self) -> str:
        return 'Prune (whole) DataSeries'

    def get_serializer_class(self) -> Any:
        return PruneDataSeriesSerializer

    def get_queryset(self) -> Any:
        return DataSeries.objects.none()

    def post(self, request: Request, **kwargs: str) -> Response:
        serializer_class = PruneDataSeriesSerializer
        serializer = serializer_class(
            data=request.data,
            context=self.get_serializer_context(),
            many=False
        )
        serializer.is_valid(raise_exception=True)

        older_than = serializer.validated_data['older_than']

        tenant = get_current_tenant()

        assert tenant is not None

        to_delete: Dict[str, List[Dict[str, str]]] = {}

        for backend in StorageBackendType:
            to_delete[str(backend)] = [{
                'id': str(dead_ds.id),
                'name': dead_ds.name,
                'external_id': dead_ds.external_id,
                'backend_type': dead_ds.backend,
                'deleted_at': dead_ds.deleted_at
            } for dead_ds in list(DataSeries.all_objects.all().filter(
                tenant=tenant,
                deleted_at__isnull=False,
                deleted_at__lt=older_than,
                backend=backend.value
            ))]

        accept = serializer.validated_data['accept']
        if accept:
            for _backend, ds_to_delete_list in to_delete.items():
                for ds_to_delete in ds_to_delete_list:
                    actions.nuke_data_series(
                        tenant_id=tenant.id,
                        backend_type=_backend,
                        data_series_id=ds_to_delete['id'],
                        older_than=older_than
                    )
            return Response(to_delete, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(to_delete)
