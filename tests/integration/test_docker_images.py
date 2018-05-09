#
# paws -- provision automated windows and services
# Copyright (C) 2016 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Test paws docker images.

Prerequisite:

You should have a working paws user directory containing required files to
run paws for OpenStack provider. Please visit the following to learn more:
    - https://rhpit.github.io/paws/guide.html#prerequisites

You also should have docker installed and the service running.

Description:

This pytest class contains 6 tests to validate the paws supported docker
images.
    1. Test downloading docker image.
    2. Start container (based on paws image) and run paws provision task.
    3. Start container (based on paws image) and run paws show task.
    4. Start container (based on paws image) and run paws winsetup task.
    5. Start container (based on paws image) and run paws teardown task.
    6. Start container (based on paws image) and run paws group task.

How to run:
    1. Create a virtual environment & activate
        $ virtualenv venv & source venv/bin/activate
    2. Install required packages
        $ pip install -r test-requirements.txt
    3. Run pytest
        - Test paws devel docker image
        $ export DOCKER_IMAGE='rywillia/paws:devel'
        $ export USER_DIR='/home/<user>/ws
        $ pytest test_docker_images.py -v -s --junit-xml=test_docker_images.xml

        - Test paws latest docker image
        $ export USER_DIR='/home/<user>/ws
        $ pytest test_docker_images.py -v -s --junit-xml=test_docker_images.xml
"""

import docker
import os
import pytest

from uuid import uuid4

# define constants used by all functions
DOCKER_IMAGE = os.getenv('DOCKER_IMAGE', 'rywillia/paws:latest')
USER_DIR = os.getenv('USER_DIR')

if USER_DIR is None:
    print('USER_DIR is undefined!')
    raise SystemExit(1)


@pytest.fixture(scope='class')
def client():
    """Docker client used by each test case.

    :return: docker client object
    """
    return docker.from_env()


def start_container(client):
    """Start container based on paws image.

    :param client: docker client connection
    :return: container object
    """
    container = client.containers.run(
        DOCKER_IMAGE,
        name='paws-%s' % str(uuid4())[:8],
        detach=True,
        tty=True,
        command='/bin/bash',
        volumes={USER_DIR: {
            'bind': '/home/paws/ws', 'mode': 'rw'}}
    )
    return container


def run_cmd(container, cmd):
    """Run command within the given container.

    :param container: container object
    :param cmd: command to run
    :return: command results
    """
    results = container.exec_run(cmd)
    print(results[1])
    return results[0]


def delete_container(container):
    """Delete container based on paws image.

    :param container: container object
    """
    container.stop()
    container.remove()


class TestDockerImages(object):

    @staticmethod
    def test_download_image(client):
        assert client.images.pull(DOCKER_IMAGE)

    @staticmethod
    def test_provision(client):
        container = start_container(client)
        results = run_cmd(container, 'paws -v provision')
        delete_container(container)
        assert not results

    @staticmethod
    def test_show(client):
        container = start_container(client)
        results = run_cmd(container, 'paws -v show')
        delete_container(container)
        assert not results

    @staticmethod
    def test_winsetup(client):
        container = start_container(client)
        results = run_cmd(
            container, 'paws -v winsetup -ps powershell/get_system_info.ps1'
        )
        delete_container(container)
        assert not results

    @staticmethod
    def test_configure(client):
        container = start_container(client)
        results = run_cmd(
            container, 'paws -v configure powershell/get_system_info.ps1'
        )
        delete_container(container)
        assert not results

    @staticmethod
    def test_teardown(client):
        container = start_container(client)
        results = run_cmd(container, 'paws -v teardown')
        delete_container(container)
        assert not results

    @staticmethod
    def test_group(client):
        container = start_container(client)
        results = run_cmd(
            container, 'paws -v group -n group/chocolatey_example.yaml'
        )
        delete_container(container)
        assert not results
