# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import setuptools
import unittest


def cli_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="compose_client",
    scripts=['bin/compose_cli'],
    version="2.2.0",
    author="NeuroForge GmbH & Co. KG",
    author_email="kontakt@neuroforge.de",
    description="NF Compose package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://neuroforge.de/compose/",
    package_data={ "compose_client": ["py.typed"] },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
    ],
    test_suite='setup.cli_test_suite',
    python_requires='>=3.8',
    install_requires=[
        "requests>=2.10",
        "dataclasses-json>=0.5.2",
        "click>=7.1, < 9.0",
    ],
    extras_require={
        'dev': [
            # THESE MUST stay in dev, as this has a gpl license
            'pytest',
            # no pytest-pep8 as it fetches pytest-cache which is gpl licensed
            'pytest-cov',
            'faker==8.1.2',
            'pyfakefs==4.3.3',
            'wheel',
            'liccheck>=0.7.2',
            "mypy>=0.800",
            "types-requests==2.28.11.13"
        ]
    }
)