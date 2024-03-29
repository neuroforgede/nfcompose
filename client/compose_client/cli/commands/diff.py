# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import json
from typing import Iterable, Any, Protocol, TypeVar, Dict, Optional, List, Union

import click

from compose_client.cli.click_ext.option import RequiredIf  # type: ignore
from compose_client.library.connection.client import Credentials, get_client, APIClient
from compose_client.library.models.domain_aliases import parse_domain_aliases, invert_dict
from compose_client.library.service.diff import diff_all_data_series, diff_all_engine_definitions, \
    diff_all_group_definitions, diff_all_http_endpoint_definitions
from compose_client.library.service.fetcher import ComposeDataSeriesDefinitionFetcher, \
    FileStorageDataSeriesDefinitionFetcher, FileStorageBaseFetcher, \
    ComposeBaseFetcher, URL, ComposeEngineDefinitionFetcher, FileStorageEngineDefinitionFetcher, FileStorageGroupDefinitionFetcher, \
    ComposeGroupDefinitionFetcher, FileStorageHttpEndpointDefinitionFetcher, ComposeHttpEndpointDefinitionFetcher
from compose_client.library.storage.file import LocalFileStorageAdapter, EnumEncoder, FileStorageAdapter


@click.group()
def diff() -> None:
    """
    Generate diff files
    """
    pass


T = TypeVar('T')


class ComposeFetcherType(Protocol):
    def __call__(self, client: APIClient) -> ComposeBaseFetcher: ...


class FileFetcherType(Protocol):
    def __call__(self, storage_adapter: FileStorageAdapter, path: str) -> FileStorageBaseFetcher: ...


class DiffAlgorithm(Protocol):
    def __call__(self, base: Iterable[Any], target: Iterable[Any], delete_in_base: bool, revoke_missing_group_permissions: bool) -> Iterable[Any]: ...


def _diff(
        base: str,
        target: str,
        outfile: str,
        base_type: str,
        target_type: str,
        base_compose_user: str,
        base_compose_password: str,
        target_compose_user: str,
        target_compose_password: str,
        delete_in_base: bool,
        revoke_missing_group_permissions: bool,
        compose_fetcher_type: ComposeFetcherType,
        file_fetcher_type: FileFetcherType,
        diff_algorithm: DiffAlgorithm,
        base_kwargs: Dict[str, Any],
        target_kwargs: Dict[str, Any]
) -> None:
    """
    skeleton function that executes the diff algorithm in a standardized manner
    """
    base_fetcher: Union[ComposeBaseFetcher, FileStorageBaseFetcher]
    if base_type == 'compose':
        base_fetcher = compose_fetcher_type(
            client=get_client(
                credentials=Credentials(
                    base_url=base,
                    user=base_compose_user,
                    password=base_compose_password
                )
            )
        )
    elif base_type == 'file':
        base_fetcher = file_fetcher_type(
            storage_adapter=LocalFileStorageAdapter(),
            path=base
        )
    else:
        raise AssertionError()

    target_fetcher: Union[ComposeBaseFetcher, FileStorageBaseFetcher]
    if target_type == 'compose':
        target_fetcher = compose_fetcher_type(
            client=get_client(
                credentials=Credentials(
                    base_url=target,
                    user=target_compose_user,
                    password=target_compose_password
                )
            )
        )
    elif target_type == 'file':
        target_fetcher = file_fetcher_type(
            storage_adapter=LocalFileStorageAdapter(),
            path=target
        )
    else:
        raise AssertionError()

    base_definitions = base_fetcher.fetch(**base_kwargs)  # type: ignore
    target_definitions = target_fetcher.fetch(**target_kwargs)  # type: ignore

    _diffs = [elem for elem in diff_algorithm(base_definitions, target_definitions, delete_in_base, revoke_missing_group_permissions) if not elem.empty()]

    _diffs_as_dicts = list(map(lambda x: x.to_dict(), _diffs))  # type: ignore

    if outfile is not None and outfile != '':
        storage_adapter = LocalFileStorageAdapter()
        storage_adapter.write_json(outfile, data=_diffs_as_dicts)
    else:
        print(json.dumps(_diffs_as_dicts, cls=EnumEncoder, indent=4))


@diff.command('dataseries')  # type: ignore
@click.option('--domain-aliases', type=click.STRING, required=False, help='JSON Mapping of domains and ports')
@click.option('--regex-filter', type=click.STRING, required=False, help='regex filter to filter the dataseries to include/exclude based on their external_id')
@click.option('--base-type', type=click.Choice(['compose', 'file']), required=True, default='file')
@click.option('--base-compose-user', type=click.STRING, cls=RequiredIf, required_if=[('base_type', 'compose')])
@click.option('--base-compose-password', type=click.STRING, cls=RequiredIf, required_if=[('base_type', 'compose')])
@click.option('--target-type', type=click.Choice(['compose', 'file']), required=True, default='file')
@click.option('--target-compose-user', type=click.STRING, cls=RequiredIf, required_if=[('target_type', 'compose')])
@click.option('--target-compose-password', type=click.STRING, cls=RequiredIf, required_if=[('target_type', 'compose')])
@click.option('--outfile', type=click.STRING, help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.option('--external-id', type=click.STRING, required=False, multiple=True, help='only include dataseries with this external_id')
@click.option(
    '--consumers/--no-consumers',
    default=True,
    help='whether to have the diff algorithm include consumers. Default: --consumers',
    is_flag=True
)
@click.option(
    '--remove-missing-consumers/--no-remove-missing-consumers',
    default=True,
    help='whether to have the diff algorithm remove consumers that exist in base but not in target. Default: --remove-missing-consumers',
    is_flag=True
)
# TODO: group filter?
# TODO: only include groups that are part of the json?
@click.option(
    '--group-permissions/--no-group-permissions',
    default=True,
    help='whether to have the diff algorithm include group permissions. Default: --group-permissions',
    is_flag=True
)
@click.option(
    '--revoke-missing-group-permissions/--no-revoke-missing-group-permissions',
    default=True,
    help='whether to have the diff revoke missing group permissions that exist in base but not in target. Default: --revoke-missing-group-permissions',
    is_flag=True
)
@click.option(
    '--delete-in-base/--no-delete-in-base',
    default=False,
    help='whether to have the diff algorithm mark dataseries it does not find in the target'
         ' to be deleted in the base. Default: --no-delete-in-base',
    is_flag=True
)
@click.argument('base')
@click.argument('target')
def diff_data_series_definition(
        domain_aliases: Optional[str],
        regex_filter: Optional[str],
        base: str,
        target: str,
        outfile: str,
        base_type: str,
        target_type: str,
        base_compose_user: str,
        base_compose_password: str,
        target_compose_user: str,
        target_compose_password: str,
        consumers: bool,
        group_permissions: bool,
        revoke_missing_group_permissions: bool,
        remove_missing_consumers: bool,
        delete_in_base: bool,
        external_id: List[str]
) -> None:
    """
    Generate a diff file that describes the changes to
    convert base into target
    """

    domain_aliases_obj = parse_domain_aliases(domain_aliases)
    inverted_domain_aliases_obj = invert_dict(domain_aliases_obj)
    if inverted_domain_aliases_obj is None:
        raise AssertionError('passed domain aliases are not invertible')

    _diff(
        base=base,
        target=target,
        outfile=outfile,
        base_type=base_type,
        target_type=target_type,
        base_compose_user=base_compose_user,
        base_compose_password=base_compose_password,
        target_compose_user=target_compose_user,
        target_compose_password=target_compose_password,
        delete_in_base=delete_in_base,
        revoke_missing_group_permissions=revoke_missing_group_permissions,
        file_fetcher_type=FileStorageDataSeriesDefinitionFetcher,
        compose_fetcher_type=ComposeDataSeriesDefinitionFetcher,
        diff_algorithm=lambda x, y, _delete_in_base, _revoke_missing_group_permissions: diff_all_data_series(
           x,
           y,
           include_consumers=consumers,
           include_group_permissions=group_permissions,
           remove_missing_consumers=remove_missing_consumers,
           delete_in_base=_delete_in_base,
           revoke_missing_group_permissions=_revoke_missing_group_permissions
        ),
        base_kwargs={
            "regex_filter": regex_filter,
            "external_ids": external_id if len(external_id) > 0 else None
        },
        # target is what we want to be at, so local files
        target_kwargs={
            "domain_aliases": domain_aliases_obj,
            "regex_filter": regex_filter,
            "external_ids": external_id if len(external_id) > 0 else None
        }
    )


@diff.command('engines')  # type: ignore
@click.option('--domain-aliases', type=click.STRING, required=False, help='JSON Mapping of domains and ports')
@click.option('--base-type', type=click.Choice(['compose', 'file']), required=True, default='file')
@click.option('--base-compose-user', type=click.STRING, cls=RequiredIf, required_if=[('base_type', 'compose')])
@click.option('--base-compose-password', type=click.STRING, cls=RequiredIf, required_if=[('base_type', 'compose')])
@click.option('--target-type', type=click.Choice(['compose', 'file']), required=True, default='file')
@click.option('--target-compose-user', type=click.STRING, cls=RequiredIf, required_if=[('target_type', 'compose')])
@click.option('--target-compose-password', type=click.STRING, cls=RequiredIf, required_if=[('target_type', 'compose')])
@click.option('--outfile', type=click.STRING, help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.option(
    '--delete-in-base/--no-delete-in-base',
    default=False,
    help='whether to have the diff algorithm mark dataseries it does not find in the target'
         ' to be deleted in the base. Default: --no-delete-in-base',
    is_flag=True
)
@click.option(
    '--revoke-missing-group-permissions/--no-revoke-missing-group-permissions',
    default=True,
    help='whether to have the diff revoke missing group permissions that exist in base but not in target. Default: --revoke-missing-group-permissions',
    is_flag=True
)
@click.argument('base')
@click.argument('target')
def diff_engine_definition(
        domain_aliases: Optional[str],
        base: str,
        target: str,
        outfile: str,
        base_type: str,
        target_type: str,
        base_compose_user: str,
        base_compose_password: str,
        target_compose_user: str,
        target_compose_password: str,
        delete_in_base: bool,
        revoke_missing_group_permissions: bool
) -> None:
    """
    Generate a diff file that describes the changes to
    convert target into src
    """

    domain_aliases_obj = parse_domain_aliases(domain_aliases)
    inverted_domain_aliases_obj = invert_dict(domain_aliases_obj)
    if inverted_domain_aliases_obj is None:
        raise AssertionError('passed domain aliases are not invertible')

    _diff(
        base=base,
        target=target,
        outfile=outfile,
        base_type=base_type,
        target_type=target_type,
        base_compose_user=base_compose_user,
        base_compose_password=base_compose_password,
        target_compose_user=target_compose_user,
        target_compose_password=target_compose_password,
        delete_in_base=delete_in_base,
        revoke_missing_group_permissions=revoke_missing_group_permissions,
        file_fetcher_type=FileStorageEngineDefinitionFetcher,
        compose_fetcher_type=ComposeEngineDefinitionFetcher,
        diff_algorithm=diff_all_engine_definitions,
        base_kwargs={},
        # target is what we want to be at, so local files
        target_kwargs={"domain_aliases": domain_aliases_obj}
    )


@diff.command('httpendpoints')  # type: ignore
@click.option('--base-type', type=click.Choice(['compose', 'file']), required=True, default='file')
@click.option('--base-compose-user', type=click.STRING, cls=RequiredIf, required_if=[('base_type', 'compose')])
@click.option('--base-compose-password', type=click.STRING, cls=RequiredIf, required_if=[('base_type', 'compose')])
@click.option('--target-type', type=click.Choice(['compose', 'file']), required=True, default='file')
@click.option('--target-compose-user', type=click.STRING, cls=RequiredIf, required_if=[('target_type', 'compose')])
@click.option('--target-compose-password', type=click.STRING, cls=RequiredIf, required_if=[('target_type', 'compose')])
@click.option('--outfile', type=click.STRING, help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.option(
    '--delete-in-base/--no-delete-in-base',
    default=False,
    help='whether to have the diff algorithm mark dataseries it does not find in the target'
         ' to be deleted in the base. Default: --no-delete-in-base',
    is_flag=True
)
@click.option(
    '--revoke-missing-group-permissions/--no-revoke-missing-group-permissions',
    default=True,
    help='whether to have the diff revoke missing group permissions that exist in base but not in target. Default: --revoke-missing-group-permissions',
    is_flag=True
)
@click.argument('base')
@click.argument('target')
def diff_http_endpoint_definition(
        base: str,
        target: str,
        outfile: str,
        base_type: str,
        target_type: str,
        base_compose_user: str,
        base_compose_password: str,
        target_compose_user: str,
        target_compose_password: str,
        delete_in_base: bool,
        revoke_missing_group_permissions: bool
) -> None:
    """
    Generate a diff file that describes the changes to
    convert target into src
    """
    _diff(
        base=base,
        target=target,
        outfile=outfile,
        base_type=base_type,
        target_type=target_type,
        base_compose_user=base_compose_user,
        base_compose_password=base_compose_password,
        target_compose_user=target_compose_user,
        target_compose_password=target_compose_password,
        delete_in_base=delete_in_base,
        revoke_missing_group_permissions=revoke_missing_group_permissions,
        file_fetcher_type=FileStorageHttpEndpointDefinitionFetcher,
        compose_fetcher_type=ComposeHttpEndpointDefinitionFetcher,
        diff_algorithm=diff_all_http_endpoint_definitions,
        base_kwargs={},
        target_kwargs={}
    )


@diff.command('groups')  # type: ignore
@click.option('--base-type', type=click.Choice(['compose', 'file']), required=True, default='file')
@click.option('--base-compose-user', type=click.STRING, cls=RequiredIf, required_if=[('base_type', 'compose')])
@click.option('--base-compose-password', type=click.STRING, cls=RequiredIf, required_if=[('base_type', 'compose')])
@click.option('--target-type', type=click.Choice(['compose', 'file']), required=True, default='file')
@click.option('--target-compose-user', type=click.STRING, cls=RequiredIf, required_if=[('target_type', 'compose')])
@click.option('--target-compose-password', type=click.STRING, cls=RequiredIf, required_if=[('target_type', 'compose')])
@click.option('--outfile', type=click.STRING, help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.option(
    '--delete-in-base/--no-delete-in-base',
    default=False,
    help='whether to have the diff algorithm mark dataseries it does not find in the target'
         ' to be deleted in the base. . Default: --no-delete-in-base',
    is_flag=True
)
@click.argument('base')
@click.argument('target')
def diff_group_definition(
        base: str,
        target: str,
        outfile: str,
        base_type: str,
        target_type: str,
        base_compose_user: str,
        base_compose_password: str,
        target_compose_user: str,
        target_compose_password: str,
        delete_in_base: bool
) -> None:
    """
    Generate a diff file that describes the changes to
    convert target into src
    """
    _diff(
        base=base,
        target=target,
        outfile=outfile,
        base_type=base_type,
        target_type=target_type,
        base_compose_user=base_compose_user,
        base_compose_password=base_compose_password,
        target_compose_user=target_compose_user,
        target_compose_password=target_compose_password,
        delete_in_base=delete_in_base,
        # we dont support revoke_missing_group_permissions on the group command for now
        # (there should only be one project managing the group)
        revoke_missing_group_permissions=False,
        file_fetcher_type=FileStorageGroupDefinitionFetcher,
        compose_fetcher_type=ComposeGroupDefinitionFetcher,
        # we dont support revoke_missing_group_permissions on the group command for now
        # (there should only be one project managing the group)
        diff_algorithm=lambda x, y, _delete_in_base, _revoke_missing_group_permissions: diff_all_group_definitions(
           x,
           y,
           delete_in_base=_delete_in_base
        ),
        base_kwargs={},
        target_kwargs={}
    )
