# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import abc
import errno
import json
import os
from enum import Enum
from typing import List, Any, Type, Iterable

from compose_client.library.utils.types import JSONType


class FileStorageAdapter(abc.ABC):
    def exists(self, path: str) -> bool: ...
    def listdir(self, path: str) -> List[str]: ...
    def read_json(self, path: str) -> JSONType: ...
    def read_json_lines(self, path: str) -> Iterable[JSONType]: ...
    def write_json(self, path: str, data: Any) -> None: ...
    def write_json_lines(self, path: str, data: Iterable[Any]) -> None: ...


class EnumEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.name
        return json.JSONEncoder.default(self, obj)


def read_json_lines_from_stream(file_like: Any) -> Iterable[JSONType]:
    while True:
        line = file_like.readline()

        if not line:
            break

        yield json.loads(line)


class LocalFileStorageAdapter(FileStorageAdapter):

    encoder: Type[json.JSONEncoder]

    def __init__(self, encoder: Type[json.JSONEncoder] = EnumEncoder):
        super().__init__()
        self.encoder = encoder

    def exists(self, path: str) -> bool:
        return os.path.exists(os.path.dirname(path))

    def listdir(self, path: str) -> List[str]:
        return os.listdir(path)

    def read_json(self, path: str) -> JSONType:
        with open(path) as json_file:
            data = json.load(json_file)
            return data

    def read_json_lines(self, path: str) -> Iterable[JSONType]:
        with open(path) as json_file:
            for elem in read_json_lines_from_stream(json_file):
                yield elem

    def _ensure_folders_exist(self, path: str) -> None:
        _dir = os.path.dirname(path)
        if _dir != '':
            if not os.path.exists(os.path.dirname(path)):
                try:
                    os.makedirs(os.path.dirname(path))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

    def write_json(self, path: str, data: Any) -> None:
        self._ensure_folders_exist(path)

        with open(path, 'w') as json_file:
            json.dump(data, json_file, sort_keys=True, indent=4, cls=self.encoder)

    def write_json_lines(self, path: str, data: Iterable[Any]) -> None:
        self._ensure_folders_exist(path)

        with open(path, 'w') as json_file:
            for _def in data:
                print(json.dumps(_def, cls=self.encoder), file=json_file)
