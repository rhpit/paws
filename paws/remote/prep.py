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
Preparation module to run required configuration on new Windows systems.
"""

from logging import getLogger

from paws.constants import ADMINISTRATOR, ADMINISTRADOR_PWD
from paws.remote.results import GenModuleResults
from paws.util import file_mgmt, update_resources_paws, get_ssh_conn
from paws.util import exec_cmd_by_ssh

LOG = getLogger(__name__)


class WinPrep(object):
    """WinPrep class."""

    def __init__(self, ansible, resources_paws):
        """Constructor."""
        self.ansible = ansible
        self.resources_paws = resources_paws

    def set_administrator_password(self):
        """Set Windows Administrator account password.

        Password is pre-defined within resources elment within topology file.
        """
        resources_paws = file_mgmt('r', self.resources_paws)
        _list_vm = []
        _counter = 0

        # Check if any resources need to set Administrator password
        for win in resources_paws['resources']:
            if ADMINISTRADOR_PWD in win:
                _list_vm.append(win['name'])

        # Return if list is empty
        if not _list_vm:
            LOG.debug("Skip setting password for Administrator account")
            return True

        for elem in resources_paws["resources"]:
            if elem["name"] in _list_vm:
                LOG.info("Set Administrator password on %s:%s",
                         elem['name'], elem['public_v4'])
                cmd = "net user Administrator %s" % \
                    elem[ADMINISTRADOR_PWD]

                self.ansible.run_module(
                    dict(name="Set Administrator password", hosts=elem["name"],
                         gather_facts='no',
                         tasks=[dict(action=dict(module='raw', args=cmd))]),
                    results_class=GenModuleResults
                )

                # Update resources keys
                elem["win_username"] = ADMINISTRATOR
                elem["win_password"] = elem[ADMINISTRADOR_PWD]
                elem.pop(ADMINISTRADOR_PWD)

                LOG.info("Successfully set Administrator password on "
                         "%s:%s", elem['name'], elem['public_v4'])
                _counter += 1

        # Update Ansible host file and resources.paws
        if _counter > 0:
            self.ansible.create_hostfile(tp_obj=resources_paws)
            # TODO: need move update_resources_paws
            update_resources_paws(self.resources_paws, resources_paws)

    def ipconfig_release(self, server):
        """Release the Windows IPv4 address for all adapters.

        To take a snapshot of a Windows server you need to release all IPv4
        ethernet connections and shutdown the server. This will allow the
        snapshot to not be created with any prior network connections. If this
        is not done, the new server provisioned based on the snapshot created.
        Will not have network connectivity, until you release ethernet
        connections/renew.

        :param server: System resource data.
        """
        server_name = server['name']
        server_ip = server['public_v4']
        server_username = server['win_username']
        server_password = server['win_password']

        LOG.debug("Release all IPv4 addr for %s" % server_name)

        # Wait for ssh connection
        LOG.info("Attempting to establish SSH connection to %s", server_ip)
        get_ssh_conn(server_ip, server_username, password=server_password)

        # Release ipconfig
        exec_cmd_by_ssh(
            server_ip,
            server_username,
            'ipconfig /release',
            password=server_password
        )

        LOG.debug("Successfully released all IPv4 addr for %s" % server_name)

    def rearm_server(self, server):
        """Extend the Windows rearm count.

        Windows only allows X amount of days to use their software in the
        trial period. You can extend this up to 3 times. Need to rearm a
        server if planning to take snapshot in order to extend the trial
        period window.

        - slmgr.vbs -rearm (rearm server)
        - slmgr.vbs /dlv (Display software licensing)
        - shutdown.exe /r /f /t 0 (Restart to take effect)

        :param server: System resource data.
        """
        server_name = server['name']
        server_ip = server['public_v4']
        server_username = server['win_username']
        server_password = server['win_password']

        LOG.debug("Extending the rearm count for %s" % server_name)
        LOG.info("Attempting to establish SSH connection to %s", server_ip)
        get_ssh_conn(server_ip, server_username, password=server_password)

        # Rearm server
        exec_cmd_by_ssh(
            server_ip,
            server_username,
            'cscript C:\\Windows\\System32\\slmgr.vbs -rearm',
            password=server_password
        )

        LOG.info("Attempting to establish SSH connection to %s", server_ip)
        get_ssh_conn(server_ip, server_username, password=server_password)

        # Restart server
        exec_cmd_by_ssh(
            server_ip,
            server_username,
            'shutdown.exe /r /f /t 0',
            password=server_password
        )
        LOG.debug("Successfully extended the rearm count for %s" % server_name)
