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

"""Winsetup task."""

from ansible.errors import AnsibleRuntimeError
from os.path import join, exists, isfile

from paws.compat import string_types
from paws.constants import WIN_EXEC_YAML, ADMIN
from paws.core import PawsTask, Namespace
from paws.exceptions import SSHError
from paws.helpers import cleanup, get_ssh_conn, file_mgmt
from paws.lib.remote import PlaybookCall, GenModuleResults, create_inventory
from paws.lib.windows import create_ps_exec_playbook


class Winsetup(PawsTask):
    """Paws winsetup task.

    This class will handle configuring your Windows resources by running
    scripts against them using Ansible. Scripts currently are PowerShell
    based.
    """

    def __init__(self, userdir, resources, credentials, verbose=0, **kwargs):
        """Constructor.

        :param userdir: User directory.
        :type userdir: str
        :param resources: System resources.
        :type resources: dict
        :param credentials: Provider credentials.
        :type credentials: dict
        :param verbose: Verbosity level.
        :type verbose: int
        :param kwargs: Extra key:value data.
        :type kwargs: dict

        Usage:

            -- CLI --

        .. code-block: bash

            $ paws <options> winsetup <options>

            -- API --

        .. code-block:: python

            from paws.tasks import Winsetup

            winsetup = Winsetup(
                userdir,
                resources,
                credentials,
                powershell='powershell.ps1',
                powershell_vars='powershell_vars.ps1'
            )
            winsetup.run()
        """
        super(Winsetup, self).__init__(userdir, verbose)
        self.resources = resources
        self.credentials = credentials
        self.verbose = verbose

        try:
            if isinstance(kwargs['args'], Namespace):
                self.args = kwargs['args']
        except KeyError:
            self.args = Namespace(kwargs)

        self.playbook = PlaybookCall(self.userdir)
        self.winsetup_yaml = join(self.userdir, WIN_EXEC_YAML)
        self.pshell = join(self.userdir, self.args.powershell)

        try:
            self.psv = self.args.powershell_vars
        except AttributeError:
            self.psv = None

    def pre_run(self):
        """Perform any necessary pre task actions."""
        # Clean files generated by paws
        cleanup([self.winsetup_yaml])

        # Use paws generated topology file?
        if exists(self.resources_paws_file):
            self.resources = file_mgmt('r', self.resources_paws_file)

        # Create inventory file
        create_inventory(self.playbook.inventory_file, self.resources)

        # Verify PowerShell script exists
        if not exists(self.pshell):
            self.logger.error(
                "PowerShell script: %s does not exist!", self.pshell
            )
            raise SystemExit(1)

    def get_systems(self):
        """Return a list of systems to configure.

        Paws users can specificy system(s) from CLI to configure. By default
        if none are given, it will configure all resources inside topology.
        """
        _active = []
        _res = []

        try:
            for sut in self.resources['resources']:
                if sut['name'] in self.args.systems:
                    _res.append(sut)
                _active.append(sut['name'])
            self.resources = _res
        except AttributeError:
            self.resources = self.resources['resources']

        if self.resources.__len__() == 0:
            self.logger.error("Supplied systems do not map to active systems.")
            self.logger.error("Given resources  : %s" % self.resources)
            self.logger.error("Active resources : %s" % _active)
            raise SystemExit(1)

    def run(self):
        """The main method for winsetup. This method will create a list of
        systems to configure based on input, verify SSH connections with
        remote systems and then execute PowerShell script against them.
        """
        # pre run tasks
        self.pre_run()

        self.logger.info("START: %s", self.name)

        # Save start time
        self.start()

        # Get systems
        self.get_systems()

        # Run PowerShell script against supplied machines
        for res in self.resources:
            pb_vars = {}

            # Get resource IP
            try:
                sut_ip = res['public_v4']
            except KeyError:
                sut_ip = res['ip']

            # Get resource authentication
            try:
                # Authenticate with SSH private key
                sut_ssh_key = res['ssh_key_file']
                sut_ssh_user = ADMIN
                sut_ssh_password = None
            except KeyError:
                # Authenticate with username and password
                sut_ssh_key = None
                sut_ssh_user = res['win_username']
                sut_ssh_password = res['win_password']

            # Initialize playbook variables
            pb_vars["hosts"] = sut_ip
            pb_vars["ps"] = self.pshell

            try:
                _psvfile = join(self.userdir, self.psv)
                if isfile(_psvfile):
                    # PowerShell vars is a file
                    pb_vars["psv"] = _psvfile
                    pvars = "file"
                elif isinstance(self.psv, string_types):
                    # PowerShell vars is a string
                    pvars = "str"
                    pb_vars["psv"] = self.psv
                else:
                    # PowerShell is neither file or unicode
                    pvars = None
            except (AttributeError, TypeError):
                # No PowerShell vars defined, use default
                pvars = self.psv

            # Create playbook to run PowerShell script on Windows resources
            self.winsetup_yaml = create_ps_exec_playbook(self.userdir, pvars)

            # Test if remote machine is ready for SSH connection
            try:
                self.logger.info(
                    "Attempting to establish SSH connection to %s", sut_ip
                )

                get_ssh_conn(
                    sut_ip,
                    sut_ssh_user,
                    sut_ssh_password,
                    sut_ssh_key
                )

                # Playbook call - run PowerShell script on Windows resources
                self.playbook.run(
                    self.winsetup_yaml,
                    pb_vars,
                    results_class=GenModuleResults
                )
            except SSHError:
                # set exit code
                self.exit_code = 1

                self.logger.error(
                    "Unable to establish SSH connection to %s", sut_ip
                )
            except (AnsibleRuntimeError, SystemExit):
                # set exit code
                self.exit_code = 1
            finally:
                # save end time
                self.end()

                # clean up run time files
                if not self.verbose:
                    cleanup([self.winsetup_yaml], self.userdir)

                self.logger.info(
                    "END: %s, TIME: %dh:%dm:%ds", self.name, self.hours,
                    self.minutes, self.seconds
                )

        return self.exit_code
