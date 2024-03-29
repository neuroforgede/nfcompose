# type: ignore
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, Mapping, List, Tuple

import click


class RequiredIf(click.Option):
    def __init__(self, *args: Any, **kwargs: Any):
        self.required_if = kwargs.pop('required_if')
        assert self.required_if, "'required_if' parameter required"
        kwargs['help'] = (
                kwargs.get('help', '') +
                ' NOTE: This argument is required if \n %s' %
                '\n or '.join([f'`{elem[0]}` = `{elem[1]}`' for elem in self.required_if])
        ).strip()
        super(RequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx: click.Context, opts: Mapping[str, Any], args: List[str]) -> Tuple[Any, List[str]]:
        we_are_present = self.name in opts

        for requirement in self.required_if:
            is_required = requirement[0] in opts and opts[requirement[0]] == requirement[1]

            if is_required and not we_are_present:
                raise click.UsageError(
                    f"Illegal usage: `{self.name}` is required when `{requirement[0]}` = `{requirement[1]}`")

        self.prompt = None

        return super(RequiredIf, self).handle_parse_result(ctx, opts, args)