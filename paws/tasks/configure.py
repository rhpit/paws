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

"""Configure task.

Configure task is the next generation of the winsetup task which is no
longer supported after 0.5.0. Winsetup task will eventually be removed from
paws source code in the future.
"""

import ast

import os
from ansible.errors import AnsibleRuntimeError

from paws.compat import string_types
from paws.core import Namespace, PawsTask
from paws.exceptions import SSHError
from paws.helpers import file_mgmt, get_ssh_conn, cleanup
from paws.lib.remote import create_inventory, PlaybookCall, ParsePSResults, \
    ResultsHandler
from paws.lib.windows import create_ps_exec_playbook


class Configure(PawsTask):
    """Paws configure task.

    This class handles configuring Windows resources. Configuration is
    performed by running either Ansible playbook or Windows PowerShell scripts.
    """

    script_type = ''
    extra_vars = dict()
    results_class = None
    res = list()

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

            $ paws <options> configure [SCRIPT] <options>

            -- API --

        .. code-block:: python

            from paws.tasks import Configure

            configure = Configure(
                userdir,
                resources,
                credentials,
                script='<script>,
                variables='<variables>'
            )
            configure.run()
        """
        super(Configure, self).__init__(userdir, verbose)
        self.resources = resources
        self.credentials = credentials
        self.verbose = verbose
        self.playbook = PlaybookCall(self.userdir)

        # cache options for later use
        try:
            self.script = os.path.join(self.userdir, getattr(
                kwargs['args'], 'script'))
            self.script_vars = getattr(kwargs['args'], 'script_vars', None)
            self.systems = getattr(kwargs['args'], 'systems', 'all')
        except KeyError:
            self.script = os.path.join(self.userdir, getattr(
                Namespace(kwargs), 'script'))
            self.script_vars = getattr(Namespace(kwargs), 'script_vars', None)
            self.systems = getattr(Namespace(kwargs), 'systems', 'all')

        # script exist
        if not os.path.exists(self.script):
            self.logger.error('Script %s not found!' % self.script)
            raise SystemExit(1)

        # override resources if resources.paws exists
        if os.path.exists(self.resources_paws_file):
            self.resources = file_mgmt('r', self.resources_paws_file)

        # clean up prior inventory file
        cleanup([self.playbook.inventory_file])

        # create ansible inventory
        create_inventory(self.playbook.inventory_file, self.resources)

        # set the systems under test
        self.set_sut()

        # use smart technology to determine script type
        self.discover()

    def __set_playbook_vars(self):
        """Construct the playbook variables from the users input."""

        # set attributes to control parsing results
        self.results_class = ResultsHandler
        self.default_callback = True

        data = dict()
        try:
            # variables defined
            vars_file = os.path.join(self.userdir, self.script_vars)
            if os.path.isfile(vars_file):
                # variables in file format
                data = file_mgmt('r', vars_file)
            elif isinstance(self.script_vars, string_types):
                # variables in string format
                data = ast.literal_eval(self.script_vars)

            # set playbook variables
            for key, value in data.items():
                self.extra_vars[key] = value

        except (AttributeError, TypeError):
            # variables undefined
            pass

    def __set_powershell_vars(self):
        """Construct the powershell variables from the users input."""

        # set attributes to control parsing results
        self.results_class = ParsePSResults
        self.default_callback = False

        self.extra_vars['ps'] = self.script

        try:
            vars_file = os.path.join(self.userdir, self.script_vars)
            if os.path.isfile(vars_file):
                # variables is in file format
                self.extra_vars['psv'] = vars_file
                vtype = 'file'
            elif isinstance(self.script_vars, string_types):
                # variables in string format
                self.extra_vars['psv'] = self.script_vars
                vtype = 'str'
            else:
                # variables is neither file or string format
                vtype = None
        except (AttributeError, TypeError):
            # variables undefined
            vtype = self.script_vars

        # create ansible playbook to run powershell script
        self.script = create_ps_exec_playbook(self.userdir, vtype)

    def discover(self):
        """Discover the input script type.

        Currently the discovery is performed based on file extension.
        """
        # RFE: smarter checking over file extension
        file_ext = os.path.splitext(self.script)
        if 'yml' in file_ext[1] or 'yaml' in file_ext[1]:
            self.script_type = 'Ansible Playbook'
            self.__set_playbook_vars()
        elif 'ps1' in file_ext[1] or 'ps' in file_ext[1]:
            self.script_type = 'Windows PowerShell'
            self.__set_powershell_vars()

        self.logger.info('Script %s, type=%s.' % (self.script,
                                                  self.script_type))

    def set_sut(self):
        """Set the systems under test."""
        if self.systems == 'all':
            self.res = self.resources['resources']
            return

        _active, _res = list(), list()

        try:
            for sut in self.resources['resources']:
                if sut['name'] in self.systems:
                    _res.append(sut)
                _active.append(sut['name'])
            self.res = _res
        except AttributeError:
            self.res = self.resources['resources']

        if len(self.res) == 0:
            self.logger.error('Systems supplied do not map to active systems. '
                              'Supplied resources : %s\n'
                              'Active resources   : %s' %
                              (self.resources, _active))
            raise SystemExit(1)

    def run(self):
        """Configure Windows services on supplied systems.

        :return: exit code
        :rtype: int
        """
        self.start()

        for res in self.res:
            try:
                # cloud providers
                host = res['public_v4']
            except KeyError:
                host = res['ip']

            self.extra_vars['hosts'] = host

            try:
                self.logger.info('Attempting to establish SSH connection '
                                 'to %s.' % host)
                get_ssh_conn(host, res['win_username'],
                             res['win_password'])

                self.playbook.run(
                    self.script,
                    self.extra_vars,
                    results_class=self.results_class,
                    default_callback=self.default_callback
                )
            except SSHError:
                self.exit_code = 1
                self.logger.error('Unable to establish SSH connection to '
                                  '%s.' % host)
            except (AnsibleRuntimeError, SystemExit):
                self.exit_code = 1
            finally:
                self.end()

                self.logger.info('END: %s, TIME: %dh:%dm:%ds' % (
                    self.name, self.hours, self.minutes, self.seconds))
        return self.exit_code
