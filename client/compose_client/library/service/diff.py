# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Callable, Generic, List, Optional, Dict, TypeVar, Sequence, Iterable, Protocol, Any, Set

from compose_client.library.models.definition.data_series_definition import DataSeriesDefinition
from compose_client.library.models.definition.dimension import Dimension
from compose_client.library.models.definition.engine import EngineDefinition
from compose_client.library.models.definition.group import GroupDefinition, GroupPermissions
from compose_client.library.models.definition.http_endpoint import HttpEndpointDefinition
from compose_client.library.models.definition.datapoint import DataPoint, FileTypeContent
from compose_client.library.models.definition.data_series_definition import DataSeriesStructure
from compose_client.library.models.definition.index import Index
from compose_client.library.models.diff.data_series import DataSeriesDefinitionDiff, DataSeriesStructureDiff
from compose_client.library.models.diff.engine import EngineDefinitionDiff
from compose_client.library.models.diff.group import GroupDefinitionDiff
from compose_client.library.models.diff.http_endpoint import HttpEndpointDefinitionDiff
from compose_client.library.models.diff.datapoint_operation import DataPointOperation
from compose_client.library.models.identifiable import Identifiable, IdentifiableByName
from compose_client.library.models.operation.general import ExternalIdOperation, OperationType, NameOperation, Operation

T = TypeVar('T')

_Identifiable = TypeVar('_Identifiable', bound=Identifiable, contravariant=True)
_IdentifiableByName = TypeVar('_IdentifiableByName', bound=IdentifiableByName)


class BaseGroupPermissionsOnObject(Protocol):
    name: str
    group_permissions: List[str]

    def to_dict(self) -> Any: ...


_BaseGroupPermissionsOnObject = TypeVar('_BaseGroupPermissionsOnObject', bound=BaseGroupPermissionsOnObject)

class RecreateInsteadOfUpdateCheck(Protocol[_Identifiable]):
    def __call__(self, base: _Identifiable, target: _Identifiable) -> bool: ...


# we default delete_missing to True here because the usual case is for structural children
def list_diff_dataseries_child(
        base: Sequence[_Identifiable],
        target: Sequence[_Identifiable],
        delete_missing: bool = True,
        recreate_instead_of_update: RecreateInsteadOfUpdateCheck[_Identifiable] = lambda base, target: False
) -> List[ExternalIdOperation]:
    ret: List[ExternalIdOperation] = []

    base_as_dict: Dict[str, _Identifiable] = {elem.external_id: elem for elem in base}
    target_as_dict: Dict[str, _Identifiable] = {elem.external_id: elem for elem in target}

    if delete_missing:
        deleted = base_as_dict.keys() - target_as_dict.keys()
        for elem in deleted:
            ret.append(ExternalIdOperation(
                operation_type=OperationType.DELETE,
                external_id=elem,
                payload=base_as_dict[elem].to_dict()
            ))

    new = target_as_dict.keys() - base_as_dict.keys()
    for elem in new:
        ret.append(
            ExternalIdOperation(
                operation_type=OperationType.CREATE,
                external_id=elem,
                payload=target_as_dict[elem].to_dict()
            )
        )

    in_both = set(target_as_dict.keys()).intersection(base_as_dict.keys())
    updated = set([
        external_id
        for external_id in in_both
        if target_as_dict[external_id] != base_as_dict[external_id]
    ])
    for elem in updated:
        _base_elem = base_as_dict[elem]
        _target_elem = target_as_dict[elem]
        if recreate_instead_of_update(base=_base_elem, target=_target_elem):
            # drop
            ret.append(
                ExternalIdOperation(
                    operation_type=OperationType.DELETE,
                    external_id=elem,
                    payload=base_as_dict[elem].to_dict()
                )
            )
            # and create
            ret.append(
                ExternalIdOperation(
                    operation_type=OperationType.CREATE,
                    external_id=elem,
                    payload=target_as_dict[elem].to_dict()
                )
            )
        else:
            ret.append(
                ExternalIdOperation(
                    operation_type=OperationType.UPDATE,
                    external_id=elem,
                    payload=target_as_dict[elem].to_dict()
                )
            )

    return ret


def user_defined_index_recreate_instead_of_update(base: Index, target: Index) -> bool:
    # targets cant be updated -> must recreate
    return base.targets != target.targets


def list_diff_dataseries_user_defined_index(
    base: Sequence[Index], 
    target: Sequence[Index],
    delete_missing: bool = True
) -> List[ExternalIdOperation]:
    return list_diff_dataseries_child(
        base=base,
        target=target,
        delete_missing=delete_missing,
        recreate_instead_of_update=user_defined_index_recreate_instead_of_update
    )


def dimension_recreate_instead_of_update(base: Dimension, target: Dimension) -> bool:
    # reference changed, drop before 
    return base.reference != target.reference


def list_diff_dataseries_dimension(
        base: Sequence[Dimension],
        target: Sequence[Dimension],
        delete_missing: bool = True
) -> List[ExternalIdOperation]:
    return list_diff_dataseries_child(
        base=base,
        target=target,
        delete_missing=delete_missing, 
        recreate_instead_of_update=dimension_recreate_instead_of_update
    )


def group_permissions_diff(
        base: Sequence[_BaseGroupPermissionsOnObject],
        target: Sequence[_BaseGroupPermissionsOnObject],
        revoke_missing_group_permissions: bool
) -> List[NameOperation]:
    ret: List[NameOperation] = []

    base_as_dict: Dict[str, _BaseGroupPermissionsOnObject] = {elem.name: elem for elem in base}
    target_as_dict: Dict[str, _BaseGroupPermissionsOnObject] = {elem.name: elem for elem in target}

    if revoke_missing_group_permissions:
        deleted = base_as_dict.keys() - target_as_dict.keys()
        for elem in deleted:
            ret.append(NameOperation(
                operation_type=OperationType.DELETE,
                name=elem,
                payload=base_as_dict[elem].to_dict()
            ))

    new = target_as_dict.keys() - base_as_dict.keys()
    for elem in new:
        ret.append(
            NameOperation(
                operation_type=OperationType.CREATE,
                name=elem,
                payload=target_as_dict[elem].to_dict()
            )
        )

    in_both = set(target_as_dict.keys()).intersection(base_as_dict.keys())
    updated = set([
        external_id
        for external_id in in_both
        if target_as_dict[external_id] != base_as_dict[external_id]
    ])
    for elem in updated:
        if revoke_missing_group_permissions:
            ret.append(
                NameOperation(
                    operation_type=OperationType.UPDATE,
                    name=elem,
                    payload=target_as_dict[elem].to_dict()
                )
            )
        else:
            merged = target_as_dict[elem].to_dict()
            merged['group_permissions'] = list(set(
                merged['group_permissions'] + base_as_dict[elem].group_permissions
            ))
            ret.append(
                NameOperation(
                    operation_type=OperationType.UPDATE,
                    name=elem,
                    payload=merged
                )
            )
    return ret


def diff_data_series(
    base: Optional[DataSeriesDefinition],
    target: Optional[DataSeriesDefinition],
    include_consumers: bool = True,
    include_group_permissions: bool = True,
    delete_in_base: bool = False,
    revoke_missing_group_permissions: bool = True,
    remove_missing_consumers: bool = True
) -> DataSeriesDefinitionDiff:
    ''' Generates instructions needed to transform DataSeries `base` into `target`

    Structures missing in `base` will be created, structures differing between the versions will be changed or re-
    created, structures that exist only in `base` might be deleted, depending on settings.
    Special use: Set `base = None` to generate a diff that simply creates `target`.

    Args:
        base: DataSeriesDefinition to be changed.
        target: DataSeriesDefinitions to change to.
        include_consumers: Whether or not to diff consumers.
        include_group_permissions: Whether or not to include group permissions.
        delete_in_base: Whether or not structures that only exist in `base` should be deleted.
        revoke_missing_group_permissions: Same as delete_in_base, but for group permissions. Only relevant if
            include_group_permissions is True.
        remove_missing_consumers: Same as delete_in_base, but for group permissions. Only relevant if
            include_consumers is True.
    
    Returns:
        Diff object containing the operations required to translate base into target
    '''
    
    if base is None and target is None:
        raise AssertionError()

    if base is None:
        # create completely new
        return DataSeriesDefinitionDiff(
            external_id=target.data_series.external_id,
            data_series=ExternalIdOperation(
                external_id=target.data_series.external_id,
                operation_type=OperationType.CREATE,
                payload=target.data_series.to_dict()
            ),
            structure=DataSeriesStructureDiff(
                float_facts=list_diff_dataseries_child([], target.structure.float_facts),
                string_facts=list_diff_dataseries_child([], target.structure.string_facts),
                text_facts=list_diff_dataseries_child([], target.structure.text_facts),
                timestamp_facts=list_diff_dataseries_child([], target.structure.timestamp_facts),
                image_facts=list_diff_dataseries_child([], target.structure.image_facts),
                file_facts=list_diff_dataseries_child([], target.structure.file_facts),
                json_facts=list_diff_dataseries_child([], target.structure.json_facts),
                boolean_facts=list_diff_dataseries_child([], target.structure.boolean_facts),
                dimensions=list_diff_dataseries_dimension([], target.structure.dimensions),
            ),
            indexes=list_diff_dataseries_user_defined_index([], target.indexes),
            consumers=list_diff_dataseries_child([], target.consumers, delete_missing=False) if include_consumers else [],
            group_permissions=group_permissions_diff([], target.group_permissions, revoke_missing_group_permissions=False) if include_group_permissions else []
        )

    if target is None:
        if not delete_in_base:
            # if we don't want to delete in the target, we simply
            # return an empty diff
            return DataSeriesDefinitionDiff(
                external_id=base.data_series.external_id,
                data_series=None,
                structure=DataSeriesStructureDiff(
                    float_facts=[],
                    string_facts=[],
                    text_facts=[],
                    timestamp_facts=[],
                    image_facts=[],
                    file_facts=[],
                    json_facts=[],
                    boolean_facts=[],
                    dimensions=[]
                ),
                indexes=[],
                consumers=[],
                group_permissions=[]
            )

        # delete completely
        # here we also create the diff to delete all structure elements separately
        # as we have to delete e.g. any dead dimensions before being able
        # to delete the referenced DataSeries
        return DataSeriesDefinitionDiff(
            external_id=base.data_series.external_id,
            data_series=ExternalIdOperation(
                external_id=base.data_series.external_id,
                operation_type=OperationType.DELETE,
                payload=base.data_series.to_dict()
            ),
            # TODO: when deleting, we maybe dont want to go through the facts one by one
            # as if we delete things by accident, this makes it harder to recover from?
            structure=DataSeriesStructureDiff(
                float_facts=list_diff_dataseries_child(base.structure.float_facts, []),
                string_facts=list_diff_dataseries_child(base.structure.string_facts, []),
                text_facts=list_diff_dataseries_child(base.structure.text_facts, []),
                timestamp_facts=list_diff_dataseries_child(base.structure.timestamp_facts, []),
                image_facts=list_diff_dataseries_child(base.structure.image_facts, []),
                file_facts=list_diff_dataseries_child(base.structure.file_facts, []),
                json_facts=list_diff_dataseries_child(base.structure.json_facts, []),
                boolean_facts=list_diff_dataseries_child(base.structure.boolean_facts, []),
                dimensions=list_diff_dataseries_dimension(base.structure.dimensions, []),
            ),
            indexes=list_diff_dataseries_user_defined_index(base.indexes, []),
            consumers=list_diff_dataseries_child(base.consumers, [], delete_missing=True) if include_consumers else [],
            group_permissions=group_permissions_diff(base.group_permissions, [], revoke_missing_group_permissions=True) if include_group_permissions else []
        )

    if base.data_series.external_id != target.data_series.external_id:
        raise AssertionError()

    update_op_ds: Optional[ExternalIdOperation] = None
    if base.data_series != target.data_series:
        # check if DataSeries needs to be updated
        update_op_ds = ExternalIdOperation(
            external_id=target.data_series.external_id,
            operation_type=OperationType.UPDATE,
            payload=target.data_series.to_dict()
        )

    return DataSeriesDefinitionDiff(
        external_id=base.data_series.external_id,
        data_series=update_op_ds,
        structure=DataSeriesStructureDiff(
            float_facts=list_diff_dataseries_child(base.structure.float_facts, target.structure.float_facts),
            string_facts=list_diff_dataseries_child(base.structure.string_facts, target.structure.string_facts),
            text_facts=list_diff_dataseries_child(base.structure.text_facts, target.structure.text_facts),
            timestamp_facts=list_diff_dataseries_child(base.structure.timestamp_facts, target.structure.timestamp_facts),
            image_facts=list_diff_dataseries_child(base.structure.image_facts, target.structure.image_facts),
            file_facts=list_diff_dataseries_child(base.structure.file_facts, target.structure.file_facts),
            json_facts=list_diff_dataseries_child(base.structure.json_facts, target.structure.json_facts),
            boolean_facts=list_diff_dataseries_child(base.structure.boolean_facts, target.structure.boolean_facts),
            dimensions=list_diff_dataseries_dimension(base.structure.dimensions, target.structure.dimensions),
        ),
        
        indexes=list_diff_dataseries_user_defined_index(base.indexes, target.indexes),
        consumers=list_diff_dataseries_child(base.consumers, target.consumers, delete_missing=remove_missing_consumers) if include_consumers else [],
        group_permissions=group_permissions_diff(base.group_permissions, target.group_permissions, revoke_missing_group_permissions) if include_group_permissions else []
    )


def diff_all_data_series(
        base: Iterable[DataSeriesDefinition],
        target: Iterable[DataSeriesDefinition],
        include_consumers: bool = True,
        include_group_permissions: bool = True,
        delete_in_base: bool = False,
        revoke_missing_group_permissions: bool = True,
        remove_missing_consumers: bool = True
) -> Iterable[DataSeriesDefinitionDiff]:
    '''Performs `diff_data_series` element-wise for every external_id that appears. 

    External IDs in `base` do not need to exactly match those in `target`.
    
    Special uses: 
        * Pass `[]` to `base` to let the diff create `target` from scratch.
        * Pass `[]` to `target` and set `delete_in_base` to True to generate instructions how to remove everything
            in `base`. 
    '''
    base_by_external_id = {elem.data_series.external_id: elem for elem in base}
    target_by_external_id = {elem.data_series.external_id: elem for elem in target}

    all_external_ids = set(base_by_external_id.keys()).union(set(target_by_external_id.keys()))

    diffs: List[DataSeriesDefinitionDiff] = []
    for external_id in all_external_ids:
        diff = diff_data_series(
            base_by_external_id.get(external_id, None),
            target_by_external_id.get(external_id, None),
            include_consumers=include_consumers,
            include_group_permissions=include_group_permissions,
            delete_in_base=delete_in_base,
            revoke_missing_group_permissions=revoke_missing_group_permissions,
            remove_missing_consumers=remove_missing_consumers
        )
        diffs.append(diff)

    return diffs


def diff_engine_definition(
        base: Optional[EngineDefinition],
        target: Optional[EngineDefinition],
        delete_in_base: bool = False,
        revoke_missing_group_permissions: bool = True
) -> EngineDefinitionDiff:
    ''' Generates instructions needed to transform Engine Definition `base` into `target`

    Structures missing in `base` will be created, structures differing between the versions will be changed or re-
    created, structures that exist only in `base` might be deleted, depending on settings.
    Special use: Set `base = None` to generate a diff that simply creates `target`.

    Args:
        base: Definition to be changed.
        target: Definition to change to.
        delete_in_base: Whether or not structures that only exist in `base` should be deleted.
        revoke_missing_group_permissions: Whether or not group permissions that only exist in `base` should be deleted.
    
    Returns:
        Diff object containing the operations required to translate base into target
    '''
    if base is None and target is None:
        raise AssertionError()

    if base is None:
        # create completely new
        return EngineDefinitionDiff(
            external_id=target.engine.external_id,
            engine=ExternalIdOperation(
                external_id=target.engine.external_id,
                operation_type=OperationType.CREATE,
                payload=target.engine.to_dict()
            ),
            # EngineSecrets do not have eternal_ids,
            secret=Operation(
                operation_type=OperationType.CREATE,
                payload=target.secret.to_dict()
            ),
            group_permissions=group_permissions_diff(
                base=[],
                target=target.group_permissions,
                revoke_missing_group_permissions=False
            )
        )

    if target is None:
        if not delete_in_base:
            # if we don't want to delete in the target, we simply
            # return an empty diff
            return EngineDefinitionDiff(
                external_id=base.engine.external_id,
                engine=None,
                secret=None,
                group_permissions=[]
            )
        return EngineDefinitionDiff(
            external_id=base.engine.external_id,
            engine=ExternalIdOperation(
                external_id=base.engine.external_id,
                operation_type=OperationType.DELETE,
                payload=base.engine.to_dict()
            ),
            secret=Operation(
                operation_type=OperationType.DELETE,
                payload=base.secret.to_dict()
            ),
            group_permissions=group_permissions_diff(
                base=base.group_permissions,
                target=[],
                revoke_missing_group_permissions=True
            )
        )

    if base.engine.external_id != target.engine.external_id:
        raise AssertionError()

    update_op_engine: Optional[ExternalIdOperation] = None
    if base.engine != target.engine:
        # check if Engine needs to be updated
        update_op_engine = ExternalIdOperation(
            external_id=target.engine.external_id,
            operation_type=OperationType.UPDATE,
            payload=target.engine.to_dict()
        )

    update_op_secret: Optional[Operation] = None
    if base.secret != target.secret:
        # check if EngineSecret needs to be updated
        update_op_secret = Operation(
            operation_type=OperationType.UPDATE,
            payload=target.secret.to_dict()
        )

    return EngineDefinitionDiff(
        external_id=base.engine.external_id,
        engine=update_op_engine,
        secret=update_op_secret,
        group_permissions=group_permissions_diff(
            base=base.group_permissions,
            target=target.group_permissions,
            revoke_missing_group_permissions=revoke_missing_group_permissions
        )
    )


def diff_all_engine_definitions(
        base: Iterable[EngineDefinition],
        target: Iterable[EngineDefinition],
        delete_in_base: bool = False,
        revoke_missing_group_permissions: bool = True
) -> Iterable[EngineDefinitionDiff]:
    '''Performs `diff_engine_definition` element-wise for every external_id that appears. 

    External IDs in `base` do not need to exactly match those in `target`.
    
    Special uses: 
        * Pass `[]` to `base` to let the diff create `target` from scratch.
        * Pass `[]` to `target` and set `delete_in_base` to True to generate instructions how to remove everything
            in `base`. 
    '''
    base_by_external_id = {elem.engine.external_id: elem for elem in base}
    target_by_external_id = {elem.engine.external_id: elem for elem in target}

    all_external_ids = set(base_by_external_id.keys()).union(set(target_by_external_id.keys()))

    diffs: List[EngineDefinitionDiff] = []
    for external_id in all_external_ids:
        _base: Optional[EngineDefinition] = base_by_external_id.get(external_id, None)
        _target: Optional[EngineDefinition] = target_by_external_id.get(external_id, None)
        diff = diff_engine_definition(
            _base,
            _target,
            delete_in_base,
            revoke_missing_group_permissions
        )
        diffs.append(diff)

    return diffs


def diff_http_endpoint_definition(
        base: Optional[HttpEndpointDefinition],
        target: Optional[HttpEndpointDefinition],
        delete_in_base: bool = False,
        revoke_missing_group_permissions: bool = True
) -> HttpEndpointDefinitionDiff:
    ''' Generates instructions needed to transform HttpEndpointDefinition `base` into `target`

    Structures missing in `base` will be created, structures differing between the versions will be changed or re-
    created, structures that exist only in `base` might be deleted, depending on settings.
    Special use: Set `base = None` to generate a diff that simply creates `target`.

    Args:
        base: Definition to be changed.
        target: Definition to change to.
        delete_in_base: Whether or not structures that only exist in `base` should be deleted.
        revoke_missing_group_permissions: Whether or not group permissions that only exist in `base` should be deleted.
    
    Returns:
        Diff object containing the operations required to translate base into target
    '''
    if base is None and target is None:
        raise AssertionError()

    if base is None:
        # create completely new
        return HttpEndpointDefinitionDiff(
            external_id=target.http_endpoint.external_id,
            http_endpoint=ExternalIdOperation(
                external_id=target.http_endpoint.external_id,
                operation_type=OperationType.CREATE,
                payload=target.http_endpoint.to_dict()
            ),
            group_permissions=group_permissions_diff(
                base=[],
                target=target.group_permissions,
                revoke_missing_group_permissions=False
            )
        )

    if target is None:
        if not delete_in_base:
            # if we don't want to delete in the target, we simply
            # return an empty diff
            return HttpEndpointDefinitionDiff(
                external_id=base.http_endpoint.external_id,
                http_endpoint=None,
                group_permissions=[]
            )
        return HttpEndpointDefinitionDiff(
            external_id=base.http_endpoint.external_id,
            http_endpoint=ExternalIdOperation(
                external_id=base.http_endpoint.external_id,
                operation_type=OperationType.DELETE,
                payload=base.http_endpoint.to_dict()
            ),
            group_permissions=group_permissions_diff(
                base=base.group_permissions,
                target=[],
                revoke_missing_group_permissions=True
            )
        )

    if base.http_endpoint.external_id != target.http_endpoint.external_id:
        raise AssertionError()

    update_op_http_endpoint: Optional[ExternalIdOperation] = None
    if base.http_endpoint != target.http_endpoint:
        # check if Engine needs to be updated
        update_op_http_endpoint = ExternalIdOperation(
            external_id=target.http_endpoint.external_id,
            operation_type=OperationType.UPDATE,
            payload=target.http_endpoint.to_dict()
        )

    return HttpEndpointDefinitionDiff(
        external_id=base.http_endpoint.external_id,
        http_endpoint=update_op_http_endpoint,
        group_permissions=group_permissions_diff(
            base=base.group_permissions,
            target=target.group_permissions,
            revoke_missing_group_permissions=revoke_missing_group_permissions
        )
    )


def diff_all_http_endpoint_definitions(
        base: Iterable[HttpEndpointDefinition],
        target: Iterable[HttpEndpointDefinition],
        delete_in_base: bool = False,
        revoke_missing_group_permissions: bool = True
) -> Iterable[HttpEndpointDefinitionDiff]:
    '''Performs `diff_http_endpoint_definition` element-wise for every external_id that appears. 

    External IDs in `base` do not need to exactly match those in `target`.
    
    Special uses: 
        * Pass `[]` to `base` to let the diff create `target` from scratch.
        * Pass `[]` to `target` and set `delete_in_base` to True to generate instructions how to remove everything
            in `base`. 
    '''
    base_by_external_id = {elem.http_endpoint.external_id: elem for elem in base}
    target_by_external_id = {elem.http_endpoint.external_id: elem for elem in target}

    all_external_ids = set(base_by_external_id.keys()).union(set(target_by_external_id.keys()))

    diffs: List[HttpEndpointDefinitionDiff] = []
    for external_id in all_external_ids:
        _base: Optional[HttpEndpointDefinition] = base_by_external_id.get(external_id, None)
        _target: Optional[HttpEndpointDefinition] = target_by_external_id.get(external_id, None)
        diff = diff_http_endpoint_definition(
            _base,
            _target,
            delete_in_base,
            revoke_missing_group_permissions
        )
        diffs.append(diff)

    return diffs


def diff_group_definition(
        base: Optional[GroupDefinition],
        target: Optional[GroupDefinition],
        delete_in_base: bool = False
) -> GroupDefinitionDiff:
    ''' Generates instructions needed to transform GroupDefinition `base` into `target`

    Structures missing in `base` will be created, structures differing between the versions will be changed or re-
    created, structures that exist only in `base` might be deleted, depending on settings.
    Special use: Set `base = None` to generate a diff that simply creates `target`.

    Args:
        base: Definition to be changed.
        target: Definition to change to.
        delete_in_base: Whether or not structures that only exist in `base` should be deleted.
    
    Returns:
        Diff object containing the operations required to translate base into target
    '''
    if base is None and target is None:
        raise AssertionError()

    if base is None:
        # create completely new
        return GroupDefinitionDiff(
            name=target.group.name,
            group=NameOperation(
                operation_type=OperationType.CREATE,
                name=target.group.name,
                payload=target.group.to_dict()
            ),
            group_permissions=Operation(
                operation_type=OperationType.CREATE,
                payload=target.group_permissions.to_dict()
            )
        )

    if target is None:
        if not delete_in_base:
            # if we don't want to delete in the target, we simply
            # return an empty diff
            return GroupDefinitionDiff(
                name=base.group.name,
                group=None,
                group_permissions=None
            )
        return GroupDefinitionDiff(
            name=base.group.name,
            group=NameOperation(
                operation_type=OperationType.DELETE,
                name=base.group.name,
                payload=base.group.to_dict()
            ),
            # EngineSecrets do not have eternal_ids,
            group_permissions=Operation(
                operation_type=OperationType.DELETE,
                payload=base.group_permissions.to_dict()
            )
        )

    if base.group.name != target.group.name:
        raise AssertionError()

    update_op_group: Optional[NameOperation] = None
    if base.group != target.group:
        # check if Group needs to be updated
        update_op_group = NameOperation(
            name=target.group.name,
            operation_type=OperationType.UPDATE,
            payload=target.group.to_dict()
        )

    update_op_permissions: Optional[Operation] = None
    if base.group_permissions != target.group_permissions:
        # check if Group permissions need to be updated
        update_op_permissions = Operation(
            operation_type=OperationType.UPDATE,
            payload=target.group_permissions.to_dict()
        )

    return GroupDefinitionDiff(
        name=base.group.name,
        group=update_op_group,
        group_permissions=update_op_permissions
    )


def diff_all_group_definitions(
        base: Iterable[GroupDefinition],
        target: Iterable[GroupDefinition],
        delete_in_base: bool = False
) -> Iterable[GroupDefinitionDiff]:
    '''Performs `diff_group_definition` element-wise for every external_id that appears. 

    External IDs in `base` do not need to exactly match those in `target`.
    
    Special uses: 
        * Pass `[]` to `base` to let the diff create `target` from scratch.
        * Pass `[]` to `target` and set `delete_in_base` to True to generate instructions how to remove everything
            in `base`. 
    '''
    base_by_name = {elem.group.name: elem for elem in base}
    target_by_name = {elem.group.name: elem for elem in target}

    all_names = set(base_by_name.keys()).union(set(target_by_name.keys()))

    diffs: List[GroupDefinitionDiff] = []
    for name in all_names:
        _base: Optional[GroupDefinition] = base_by_name.get(name, None)
        _target: Optional[GroupDefinition] = target_by_name.get(name, None)
        diff = diff_group_definition(
            _base,
            _target,
            delete_in_base
        )
        diffs.append(diff)

    return diffs


def diff_datapoint(base_datapoint: DataPoint, target_datapoint: DataPoint, dataseries_structure: DataSeriesStructure) -> bool:
    """
        Args:
            - base_datapoint (:obj:`DataPoint`): the datapoint, which is to be changed
            - target_datapoint (:obj:`DataPoint`): the datapoint to change to
            - dataseries_definition (:obj:`DataSeriesStructure`): the structure of the dataseries being worked on

        Returns:    
            bool: The return Value. True if a diff exists, False otherwise

        Raises:
            NotImplementedError: Is thrown if the definition of the dataseries, which is being worked on, contains image or file facts (the comparison of those facts has not been implemented yet)
    """

    if len(dataseries_structure.file_facts) != 0 or len(dataseries_structure.image_facts) != 0:
        raise NotImplementedError("filefacts and imagefacts are not supported yet")

    if base_datapoint != target_datapoint:
        return True

    return False


def diff_datapoint_list(
    base_datapoints: List[DataPoint],
    target_datapoints: List[DataPoint],
    dataseries_structure: DataSeriesStructure
) -> List[DataPointOperation]:
    """
        this method is not intended for use on large dataseries

        Args:
            base_datapoints (:obj:`list` of :obj:`DataPoint`): a list of datapoints to be changed
            target_datapoints (:obj:`list` of :obj:`DataPoint`): the datapoints in the target

        Returns: 
            A List of DataPointOperations, which have to be updated/created/deleted. Unchanged datapoints will not be returned.

        Raises:
            NotImplementedError: Is thrown if the definition of the dataseries, which is being worked on, contains image or file facts (the comparison of those facts has not been implemented yet)
            ValueError: If there are duplicate external ids in either ``base_datapoints`` or ``target_datapoints``
    """

    base_external_ids: Set[str] = set()
    target_external_ids: Set[str] = set()

    for datapoint in base_datapoints:
        base_external_ids.add(datapoint.external_id)

    for datapoint in target_datapoints:
        target_external_ids.add(datapoint.external_id)

    if len(base_external_ids) != len(base_datapoints):
        raise ValueError('there are multiples of the same external_id in base')

    if len(target_external_ids) != len(target_datapoints):
        raise ValueError('there are multiples of the same external_id in target')

    datapoint_updates: List[DataPointOperation] = []
    base_datapoint_dict: Dict[str, DataPoint] = {}

    for base_datapoint in base_datapoints:
        base_datapoint_dict[base_datapoint.external_id] = base_datapoint

    for target_datapoint in target_datapoints:
        if target_datapoint.external_id in base_datapoint_dict:
            if diff_datapoint(base_datapoint=base_datapoint_dict[target_datapoint.external_id], target_datapoint=target_datapoint, dataseries_structure=dataseries_structure):
                datapoint_updates.append(DataPointOperation(operation_type=OperationType.UPDATE, datapoint=target_datapoint))
            base_datapoint_dict.pop(target_datapoint.external_id)
        else:
            datapoint_updates.append(DataPointOperation(operation_type=OperationType.CREATE, datapoint=target_datapoint))

    for base_datapoint_external_id in base_datapoint_dict.keys():
        datapoint_updates.append(DataPointOperation(operation_type=OperationType.DELETE, datapoint=DataPoint(external_id=base_datapoint_external_id, payload={})))

    return datapoint_updates