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
Helper codes for unittest
http://docs.pytest.org/en/latest/goodpractices.html
go to anchor: conventions-for-python-test-discovery
"""

from os.path import join
from paws.util import file_mgmt
from paws.providers.openstack import Util, Glance, Nova
from paws.constants import ADMINISTRADOR_PWD, DEFAULT_USERDIR


# TODO: Need to revist this module and see if it is still required?

class CIHelper(object):

    def __init__(self, logger, ud=None):
        """Constructor."""
        if ud is None:
            self.userdir = DEFAULT_USERDIR
        else:
            self.userdir = ud
        self.images = []
        self.results = {}
        # Openstack credentials
        self.os_auth_url = None
        self.os_username = None
        self.os_password = None
        self.os_project_name = None
        self.creds_file = self.userdir + "/credentials.yaml"
        self.user_creds = self.get_credentials()
        self.log = logger

    def get_credentials(self):
        """Load credentials.yaml same used in PAWS"""
        # TODO: fix me
        creds = Util(self.creds_file)
        return creds.get_credentials()

    def set_paws_files(self, image, name):
        """Set required paws files.
        :param image: Windows image name
        :type image: str
        :param name: VM name
        :type name: str
        """
        # Local variables
        _creds_file = join(self.userdir, 'credentials.yaml')
        _res_file = join(self.userdir, 'resources.yaml')
        # Read required paws files
        creds_data = file_mgmt('r', _creds_file)
        res_data = file_mgmt('r', _res_file)

        # Get position in list for openstack credentials
        pos = next(index for index, key in enumerate(creds_data['credentials'])
                   if 'openstack' in key['provider'])

        try:
            # Set credential values
            creds_data['credentials'][pos]['os_auth_url'] = \
                self.user_creds['OS_AUTH_URL']
            creds_data['credentials'][pos]['os_username'] = \
                self.user_creds['OS_USERNAME']
            creds_data['credentials'][pos]['os_password'] = \
                self.user_creds['OS_PASSWORD']
            creds_data['credentials'][pos]['os_project_name'] = \
                self.user_creds['OS_PROJECT_NAME']
            # Set resources values
            res_data['resources'][0]['name'] = "%s" % name
            res_data['resources'][0]['image'] = image
            if ADMINISTRADOR_PWD in res_data['resources'][0]:
                res_data['resources'][0].pop(ADMINISTRADOR_PWD)

        except KeyError as ex:
            raise Exception(ex)

        # Write updated paws requires files
        file_mgmt('w', _creds_file, creds_data)
        file_mgmt('w', _res_file, res_data)

        return 0

    def get_win_images(self):
        """Get all available Windows images"""
        glance = Glance(self.user_creds)
        return glance.get_win_images()

    def get_vm_info(self, vm_name):
        """Get info from nova instance"""
        nova = Nova(self.user_creds)
        return nova.get_server(vm_name)

    def delete_vm(self, instance_id):
        """Delete nova instance"""
        nova = Nova(self.user_creds)
        return nova.delete_instance(instance_id)
