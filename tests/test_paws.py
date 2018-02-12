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
"""Unit tests to test each paws task using paws as a library import.

Before running the tests within this module you will need to edit a vars
file. Please open the ./playbooks/vars.yml conf and replace the content
matching your content locally. This file contains information such as:

    - user directory
    - resource file
    - credential file
    - powershell file
    - group file

These files can be found at the following project:

    - https://github.com/rhpit/ws

Once the vars file is filled in, go ahead and run the tests!
"""
import os
import pytest

from paws.helpers import file_mgmt
from paws.tasks.group import Group
from paws.tasks import Provision, Teardown, Show
from paws.tasks.winsetup import Winsetup


@pytest.fixture(scope='class')
def param():
    """Parameter fixture used by all test cases."""
    data = dict()

    # load test configuration
    cfg = file_mgmt('r', 'playbooks/vars.yml')

    # set absolute file paths
    creds_file = os.path.join(cfg['user_dir'], cfg['credential'])
    topology_file = os.path.join(cfg['user_dir'], cfg['topology'])
    resources_paws = os.path.join(cfg['user_dir'], 'resources.paws')
    group_file = os.path.join(cfg['user_dir'], cfg['group'])

    # set keys
    data['user_dir'] = cfg['user_dir']
    data['powershell'] = cfg['powershell']
    data['resources_paws_file'] = resources_paws
    data['group_file'] = group_file
    data['credentials'] = file_mgmt('r', creds_file)
    data['resources'] = file_mgmt('r', topology_file)
    data['group'] = file_mgmt('r', group_file)

    return data


class TestTasks(object):
    """Test paws tasks."""

    @staticmethod
    def test_provision(param):
        """Test provision task.

        :param param: Parameter fixture.
        """
        provision = Provision(
            param['user_dir'],
            param['resources'],
            param['credentials'],
            verbose=1
        )

        results = provision.run()
        assert results == 0

    @staticmethod
    def test_winsetup(param):
        """Test winsetup task.

        :param param: Parameter fixture.
        """
        param['resources_paws'] = file_mgmt('r', param['resources_paws_file'])

        winsetup = Winsetup(
            param['user_dir'],
            param['resources_paws'],
            param['credentials'],
            verbose=1,
            powershell=param['powershell']
        )

        results = winsetup.run()
        assert results == 0

    @staticmethod
    def test_show(param):
        """Test show task.

        :param param: Parameter fixture.
        """
        show = Show(
            param['user_dir'],
            param['resources'],
            param['credentials'],
            verbose=1
        )

        results = show.run()
        assert results == 0

    @staticmethod
    def test_teardown(param):
        """Test teardown task.

        :param param: Parameter fixture.
        """
        teardown = Teardown(
            param['user_dir'],
            param['resources'],
            param['credentials'],
            verbose=1
        )

        results = teardown.run()
        assert results == 0

    @staticmethod
    def test_group(param):
        """Test group task.

        :param param: Parameter fixture.
        """
        group = Group(
            param['user_dir'],
            param['group'],
            verbose=1,
            name=param['group_file']
        )

        results = group.run()
        assert results == 0
