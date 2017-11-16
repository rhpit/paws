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
Remote package which contains modules used to talk to remote machines.
"""

from logging import getLogger
from os.path import join

from ansible.plugins.callback import CallbackBase

from paws.constants import WIN_EXEC_YAML
from paws.util import file_mgmt


LOG = getLogger(__name__)


class PawsCallbackBase(CallbackBase):
    """
    Paws custom Ansible callback class which overrides the default callback
    class. This will store the results as attributes to be accessed later on.
    """

    def __init__(self):
        """Constructor."""
        super(PawsCallbackBase, self).__init__()
        self.contacted = []
        self.unreachable = False

    def v2_runner_on_ok(self, result):
        """Store ok results."""
        CallbackBase.v2_runner_on_ok(self, result)
        self.contacted.append(
            {
                'host': result._host.get_name(),
                'success': True,
                'results': result._result
            }
        )

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Store failed results."""
        CallbackBase.v2_runner_on_failed(
            self, result, ignore_errors=ignore_errors)
        self.contacted.append(
            {
                'host': result._host.get_name(),
                'success': False,
                'results': result._result
            }
        )

    def v2_runner_on_unreachable(self, result):
        """Store unreachable results."""
        CallbackBase.v2_runner_on_unreachable(self, result)
        self.unreachable = True


class WinPsExecYAML(object):
    """
    Class which handles setting up the playbook data structure for
    calling PowerShell scripts against remote Windows servers.
    """

    def __init__(self, args):
        """Constructor."""
        self.win_exec = []
        self.userdir = args.userdir
        self.playbook = join(self.userdir, WIN_EXEC_YAML)

    def create(self, pvars):
        """Setup data structure and create win exec YAML."""
        playbook = {}
        playbook['gather_facts'] = 'False'
        playbook['hosts'] = '{{ hosts }}'
        playbook['name'] = 'Preparing to run powershell on remote Windows'

        if pvars is "file":
            # PowerShell variables is defined by a file
            playbook['vars'] = {
                'win_var_path': 'c:/my_vars.json'
            }

            playbook['tasks'] = [
                {
                    'name': 'Print PSV content',
                    'debug': "msg={{ lookup('file', psv) }}"
                },
                {
                    'name': 'Copy JSON vars to remote Windows',
                    'win_copy': 'src={{ psv }} dest={{ win_var_path }}'
                },
                {
                    'name': 'Execute powershell on remote Windows',
                    'script': '{{ ps }} {{ win_var_path }}',
                    'register': 'powershell_stdout'
                }
            ]
        elif pvars is "str":
            # PowerShell variables is defined as a string
            playbook['tasks'] = [
                {
                    'name': 'Execute powershell on remote Windows',
                    'script': '{{ ps }} {{ psv }}',
                    'register': 'powershell_stdout'
                }
            ]
        elif pvars is None:
            # No PowerShell variables is defined
            playbook['tasks'] = [
                {
                    'name': 'Execute powershell on remote Windows',
                    'script': '{{ ps }}',
                    'register': 'powershell_stdout'
                }
            ]

        playbook['tasks'].append({'debug': 'var=powershell_stdout'})

        self.win_exec.append(playbook)
        # Write Ansible Playbook
        file_mgmt('w', self.playbook, self.win_exec)
        LOG.debug("Playbook %s created.", self.playbook)
        return self.playbook
