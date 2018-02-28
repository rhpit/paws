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
Test all available Windows images in OpenStack provider.

Prerequisite:

You should have a working paws user directory containing required files to
run paws for OpenStack provider. Please visit the following to learn more:
    - https://rhpit.github.io/paws/guide.html#prerequisites

Description:

This pytest class contains 4 tests to validate all available Windows images
in OpenStack provider.
    1. Provision Windows instance (paws provision)
        - Setting administrator account password
    2. Check to ensure Windows instance is running
        - This is put in place since sometimes the vm will be shutdown after
        sysprep reboot.
    3. Verify remote connection to instance (paws winsetup)
        - Runs a basic powershell script printing system information
    4. Teardown Windows instance (paws teardown)

How to run:
    1. Create a virtual environment & activate
        $ virtualenv venv & source venv/bin/activate
    2. Install required packages
        $ pip install paws-cli pytest
    3. Run pytest
        - Test all windows images
        $ export USER_DIR=/home/<user>/ws
        $ pytest test_windows_images.py -v -s --junit-xml=test_win_images.xml

        - Test certain windows images
        $ export USER_DIR=/home/<user>/ws
        $ export WINDOWS_IMAGES='image01,image02'
        $ pytest test_windows_images.py -v -s --junit-xml=test_win_images.xml
"""

import logging
import subprocess
from pprint import pformat
from uuid import uuid4

import pytest
from os import getenv
from os.path import join

from paws.exceptions import NotFound
from paws.helpers import file_mgmt
from paws.providers.openstack import LibCloud

# define logger
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

# define constants used by all functions
USER_DIR = getenv('USER_DIR')

if not USER_DIR:
    LOG.error('Environment variable: USER_DIR undefined!')
    raise SystemExit(1)

RESOURCES_YML = join(USER_DIR, 'resources.yaml')
CREDENTIALS_YML = join(USER_DIR, 'credentials.yaml')
LINE = '*' * 80
DIV = '=' * 20

# create the libcloud object establishing connection to openstack
credentials = file_mgmt('r', CREDENTIALS_YML)
for credential in credentials['credentials']:
    if credential['provider'].lower() == 'openstack':
        LIB_CLOUD = LibCloud(
            dict(
                os_username=credential['os_username'],
                os_password=credential['os_password'],
                os_auth_url=credential['os_auth_url'],
                os_project_name=credential['os_project_name']
            )
        )


def get_windows_images():
    """Get all the available windows images.

    :return: windows images names
    :rtype: list
    """
    windows_images = list()

    # did the user state the windows images to test?
    select_images = getenv('WINDOWS_IMAGES')

    if select_images:
        for image in select_images.split(','):
            windows_images.append(image)
    else:
        # RFE: would be nice to query image metadata for key such as OS=WINDOWS
        for item in LIB_CLOUD.driver.list_images():
            if 'win' in item.name:
                windows_images.append(str(item.name))

    if len(windows_images) == 0:
        LOG.error('No Windows images available to test!')
        raise SystemExit(1)

    LOG.info('Windows images')
    LOG.info(LINE)
    for index, image in enumerate(windows_images):
        index += 1
        LOG.info('%s. %s' % (index, image))
    LOG.info(LINE)

    return windows_images


def update_resources_yml(vm_name, image_name):
    """Update the resource topology file with the windows image to test.

    It will update the resources.yaml file located within the defined
    user directory above (USER_DIR constant).

    :param vm_name: name for the vm to be provisioned
    :type vm_name: str
    :param image_name: name for the image to be used when booting vm
    :type image_name: str
    """
    data = file_mgmt('r', RESOURCES_YML)

    for item in data['resources']:
        item['name'] = vm_name
        item['image'] = image_name
    file_mgmt('w', RESOURCES_YML, data)


@pytest.fixture(scope='class', params=get_windows_images())
def param(request):
    """Parameters used for each test execution.

    :param request: pytest request fixture
    """
    # define vm name and image
    test_data = dict(
        name='paws-%s' % str(uuid4())[:8],
        image=str(request.param)
    )

    # set windows image in paws resources file before test execution
    update_resources_yml(test_data['name'], test_data['image'])

    LOG.info('\n TESTING WINDOWS IMAGE: %s \n' % test_data['image'])

    LOG.info(pformat(file_mgmt('r', RESOURCES_YML)))

    # add the finalizer to run after all test execution
    def fin():
        """Finalizer to clean up left over vms after test execution."""
        LOG.info('\n' + DIV + ' FINALIZER ' + DIV)

        try:
            node = LIB_CLOUD.get_node(test_data['name'])
            LOG.info('VM: %s exists, need to delete before next test.' %
                     test_data['name'])
            LIB_CLOUD.driver.destroy_node(node)
            LOG.info('VM: %s successfully terminated.' % test_data['name'])
        except NotFound:
            LOG.info('VM: %s was cleaned up during test execution.' %
                     test_data['name'])

    request.addfinalizer(fin)
    return test_data


class TestWindowsImages(object):

    def test_provision(self, param):
        LOG.info('\n' + DIV + ' PROVISION ' + DIV)
        cmd = 'paws -v -ud %s provision' % USER_DIR
        LOG.info('Command to run: %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True)
        proc.communicate()
        assert proc.returncode == 0

    def test_is_vm_running(self, param):
        LOG.info('\n' + DIV + ' VM STATE ' + DIV)
        node = LIB_CLOUD.get_node(param['name'])
        LOG.info('\nVM status: %s' % node.state.lower())
        if node.state.lower() == 'running':
            assert True
        else:
            assert False

    def test_winsetup(self, param):
        LOG.info('\n' + DIV + ' WINSETUP ' + DIV)
        cmd = 'paws -v -ud %s winsetup -ps powershell/get_system_info.ps1' %\
              USER_DIR
        LOG.info('Command to run: %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True)
        proc.communicate()
        assert proc.returncode == 0

    def test_show(self, param):
        LOG.info('\n' + DIV + ' SHOW ' + DIV)
        cmd = 'paws -v -ud %s show' % USER_DIR
        LOG.info('Command to run: %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True)
        proc.communicate()
        assert proc.returncode == 0

    def test_teardown(self, param):
        LOG.info('\n' + DIV + ' TEARDOWN ' + DIV)
        cmd = 'paws -v -ud %s teardown' % USER_DIR
        LOG.info('Command to run: %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True)
        proc.communicate()
        assert proc.returncode == 0
