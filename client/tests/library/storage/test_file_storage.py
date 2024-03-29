# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import json
import unittest

from pyfakefs.fake_filesystem_unittest import Patcher  # type: ignore

from compose_client.library.storage.file import LocalFileStorageAdapter


class LocalFileStorageAdapterTest(unittest.TestCase):
    def test_file_storage_adapter_listdir(self) -> None:
        with Patcher() as patcher:
            patcher.fs.create_dir('/mydir')
            patcher.fs.create_dir('/mydir/subdir')
            patcher.fs.create_file('/mydir/test.json', contents='{}')
            patcher.fs.create_file('/mydir/subdir/subdirtest.json', contents='{"hello": "world"}')

            local_file_storage_adapter = LocalFileStorageAdapter()

            files = local_file_storage_adapter.listdir('/mydir')

            self.assertEqual(2, len(files))
            self.assertIn('test.json', files)
            self.assertIn('subdir', files)
            self.assertNotIn('subdirtest.json', files)

    def test_file_storage_adapter_write_json(self) -> None:
        with Patcher() as patcher:
            patcher.fs.create_dir('/mydir')

            local_file_storage_adapter = LocalFileStorageAdapter()

            local_file_storage_adapter.write_json(path='/mydir/test.json', data={
                "hello": "world"
            })

            files = local_file_storage_adapter.listdir('/mydir')

            self.assertEqual(1, len(files))
            self.assertIn('test.json', files)

            with open('/mydir/test.json') as file:
                data = json.load(file)

                self.assertEqual(data['hello'], 'world')

    def test_file_storage_adapter_write_json_creates_subdirs(self) -> None:
        with Patcher() as patcher:
            local_file_storage_adapter = LocalFileStorageAdapter()

            local_file_storage_adapter.write_json(path='/mydir/subdir/test.json', data={
                "hello": "world"
            })

            files = local_file_storage_adapter.listdir('/mydir')

            self.assertEqual(1, len(files))
            self.assertIn('subdir', files)

            subdir_files = local_file_storage_adapter.listdir('/mydir/subdir')
            self.assertEqual(1, len(subdir_files))
            self.assertIn('test.json', subdir_files)

    def test_file_storage_adapter_read_json(self) -> None:
        with Patcher() as patcher:
            patcher.fs.create_dir('/mydir')
            patcher.fs.create_file('/mydir/test.json', contents='{"hello": "world"}')

            local_file_storage_adapter = LocalFileStorageAdapter()

            data = local_file_storage_adapter.read_json(path='/mydir/test.json')

            self.assertEqual(data['hello'], 'world')



