# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import subprocess
import argparse
import buildinfo.version as version
import datetime
import os
import getpass

default_test_container = subprocess.check_output([
    "bash",
    "-c",
    f"COMPOSE_PROJECT_NAME={getpass.getuser()}_skipper docker-compose ps -q neuroforge_skipper_base_dev"
]).decode().strip()

def log(message: str) -> None:
    print(message)


def setDevOpsVersionBuildVar(version: str) -> None:
    print(f'##vso[task.setvariable variable=skipper_build_version]{version}')


def setup_for_build() -> None:
    log('setting up tools for build.')
    subprocess.check_call([
        'bash',
        '-c',
        'curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/master/contrib/install.sh | sh -s -- -b ./build'
    ])
    log('finished setting up tools for build.')


def run_integration_tests() -> None:
    log('running integration tests.')
    subprocess.check_call([
        'bash',
        '-c',
        'cd ../deploy && exec bash test.sh'
    ], env={
        **os.environ,
        'COMPOSE_PROJECT_NAME': os.environ.get('COMPOSE_PROJECT_NAME', '') + 'integration_test',
        'NFCOMPOSE_SETUP_SKIP_PULL': 'yes'
    })
    log('finished running integration tests.')


def run_unit_tests() -> None:
    log('running unit tests.')
    subprocess.check_call([
        'docker',
        'exec',
        '-u',
        f'{os.getuid()}:{os.getgid()}',
        os.getenv('SKIPPER_BUILD_TEST_CONTAINER', default_test_container),
        'bash',
        '-c',
        f'cd {os.getenv("SKIPPER_BUILD_TEST_CONTAINER_BASE_PATH", "/neuroforge/skipper")} && pwd && ls -la'
    ])
    subprocess.check_call([
        'docker',
        'exec',
        '-u',
        f'{os.getuid()}:{os.getgid()}',
        os.getenv('SKIPPER_BUILD_TEST_CONTAINER', default_test_container),
        'bash',
        '-c',
        f'cd {os.getenv("SKIPPER_BUILD_TEST_CONTAINER_BASE_PATH", "/neuroforge/skipper")} && exec bash create_venv.sh'
    ])
    subprocess.check_call([
        'docker',
        'exec',
        '-u',
        f'{os.getuid()}:{os.getgid()}',
        os.getenv('SKIPPER_BUILD_TEST_CONTAINER', default_test_container),
        'bash',
        '-c',
        (
            f'cd {os.getenv("SKIPPER_BUILD_TEST_CONTAINER_BASE_PATH", "/neuroforge/skipper")} && ' +
            f'SKIPPER_TESTING_DB_HOST={os.getenv("SKIPPER_TESTING_DB_HOST", "postgres_container_cephalopod")} ' +
            f'bash test.sh'
        )
    ])
    subprocess.check_call([
        'docker',
        'exec',
        '-u',
        f'{os.getuid()}:{os.getgid()}',
        os.getenv('SKIPPER_BUILD_TEST_CONTAINER', default_test_container),
        'bash',
        '-c',
        f'cd {os.getenv("SKIPPER_BUILD_TEST_CONTAINER_BASE_PATH", "/neuroforge/skipper")} && exec bash typecheck.sh'
    ])
    log('finished running unit tests.')


def trivy_check(image: str) -> None:
    log(f'checking image {image} with trivy.')
    subprocess.check_call([
        'trivy',
        'image',
        '--ignore-unfixed',
        '--skip-files',
        '/neuroforge/skipper/skipper/environment_local.py',
        '--exit-code',
        '1',
        image
    ], env={
        **os.environ,
        'PATH': os.environ['PATH'] + ':./build'
    })
    log('finished checking image with trivy.')


def build_docker(image_name: str, date_string: str, production_docker_tag: bool) -> None:
    skipper_build_version = f'{version.version_string}-{date_string}'
    setDevOpsVersionBuildVar(skipper_build_version)
    cmd = [
        'docker',
        'build',
        '--build-arg',
        f'SKIPPER_VERSION={skipper_build_version}',
        '-f',
        'Dockerfile-production'
    ]

    if not production_docker_tag:
        cmd.extend([
            '-t',
            f'{image_name}:{version.major_version_string}'
        ])

        cmd.extend([
            '-t',
            f'{image_name}:{version.minor_version_string}'
        ])

        cmd.extend([
            '-t',
            f'{image_name}:{version.patch_version_string}'
        ])

        cmd.extend([
            '-t',
            f'{image_name}:{version.version_string}-{date_string}'
        ])
    else:
        cmd.extend([
            '-t',
            f'{image_name}:latestProduction'
        ])

    cmd.extend([
        '.'
    ])

    log('running: ' + ' '.join(cmd))

    subprocess.check_call(cmd)

    trivy_check(
        f'{image_name}:{version.version_string}-{date_string}'
    )


def push_docker(image_name: str, date_string: str, production_docker_tag: bool) -> None:

    if not production_docker_tag:
        to_push = [
            f'{image_name}:{version.version_string}',
            f'{image_name}:{version.version_string}-{date_string}'
        ]
    else:
        to_push = [
            f'{image_name}:latestProduction'
        ]

    for image in to_push:
        log('pushing ' + image)

        cmd = [
            'docker',
            'push',
            image
        ]

        log('running: ' + ' '.join(cmd))

        subprocess.check_call(cmd)


def build_base_image(base_image_name: str, base_image_tag: str) -> None:
    # pull the latest base image base
    subprocess.check_call([
        'docker',
        'pull',
        'python:3.11'
    ])
    subprocess.check_call([
        'docker',
        'build',
        '-f',
        'Dockerfile-base',
        '--no-cache',
        '-t',
        f'{base_image_name}:{base_image_tag}',
        '.'
    ])
    trivy_check(f'{base_image_name}:{base_image_tag}')


def push_base_image(base_image_name: str, base_image_tag: str) -> None:
    subprocess.check_call([
        'docker',
        'push',
        f'{base_image_name}:{base_image_tag}'
    ])


def str2bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


parser = argparse.ArgumentParser(description='Builds NF Compose')
sub_parsers = parser.add_subparsers(
    title='commands',
    description='valid commands'
)

build_parser = sub_parsers.add_parser('build', help='build skipper docker image')
build_parser.set_defaults(action='build')
build_parser.add_argument('--productionDockerTag', type=str2bool, help='whether to use the latestProduction instead of the generated version or not',
                          required=False,
                          nargs='?', const=True, default=False)
build_parser.add_argument('--imageName', type=str,
                          help='image name (with registry url) to tag the resulting docker image with', required=True)
build_parser.add_argument('--buildBase', type=str2bool,
                          help='whether to include base image build script', required=False,
                          nargs='?', const=True, default=False)
build_parser.add_argument('--skipTests', type=str2bool,
                          help='whether to skip running the unit tests', required=False,
                          nargs='?', const=True, default=False)
build_parser.add_argument('--skipPush', type=str2bool,
                          help='whether to skip pushing the docker image', required=False,
                          nargs='?', const=True, default=False)

setup_parser = sub_parsers.add_parser('setup', help='setup build tools')
setup_parser.set_defaults(action='setup')

build_base_parser = sub_parsers.add_parser('buildBase', help='build the base docker image')
build_base_parser.add_argument('--skipPush', type=str2bool,
                               help='whether to skip pushing the base image to the NF docker registry', required=False,
                               nargs='?', const=True, default=False)
build_base_parser.set_defaults(action='buildBase')

args = vars(parser.parse_args())
if 'action' not in args:
    parser.print_help()
    exit(1)

BASE_IMAGE = 'ghcr.io/neuroforgede/nfcompose-skipper-base'
BASE_IMAGE_TAG = 'py-3.11'

action = args['action']
if action == 'setup':
    setup_for_build()
elif action == 'buildBase':
    build_base_image(
        base_image_name=BASE_IMAGE,
        base_image_tag=BASE_IMAGE_TAG
    )
    if not args['skipPush']:
        push_base_image(
            base_image_name=BASE_IMAGE,
            base_image_tag=BASE_IMAGE_TAG
        )
elif action == 'build':
    if not args['skipTests']:
        run_unit_tests()

    production_docker_tag: bool = False
    if 'productionDockerTag' in args:
        if len(version.suffix_version) != 0 and args['productionDockerTag']:
            raise Exception('suffix_version is not empty, can\'t build with latest tag')
        production_docker_tag = args['productionDockerTag']

    image_name: str = args['imageName']

    today = datetime.datetime.now()
    date_string = today.strftime("%Y-%m-%d-%H-%M-%S")

    # MAIN BEGINS HERE:
    if 'buildBase' in args:
        if args['buildBase']:
            build_base_image(
                base_image_name=BASE_IMAGE,
                base_image_tag=BASE_IMAGE_TAG
            )

    build_docker(image_name=image_name, date_string=date_string, production_docker_tag=production_docker_tag)

    if not args['skipTests']:
        run_integration_tests()

    if not args['skipPush']:
        push_docker(image_name=image_name, date_string=date_string, production_docker_tag=production_docker_tag)

log('done.')
