# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

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
    version="2.3.5",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
    ],
    test_suite='setup.cli_test_suite',
    python_requires='>=3.9',
    install_requires=[
        "requests>=2.32.5,<2.33",
        "dataclasses-json>=0.6.7,<0.7",
        "click>=8.1.8,<8.2",
    ],
    extras_require={
        'dev': [
            # THESE MUST stay in dev, as this has a gpl license
            'pytest>=8.3.5,<9',
            # no pytest-pep8 as it fetches pytest-cache which is gpl licensed
            'pytest-cov>=7.0.0,<8',
            'faker==8.1.2',
            'pyfakefs==4.3.3',
            'wheel>=0.45.1,<1',
            # liccheck currently imports pkg_resources, which setuptools 82 removed.
            'setuptools<82',
            'liccheck==0.9.2',
            "mypy>=1.19.1,<1.20",
            "types-requests==2.32.4.20250913"
        ]
    }
)
