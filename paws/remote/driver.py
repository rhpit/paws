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
Python Ansible API module.
"""

import sys

from collections import namedtuple
from ConfigParser import ConfigParser
from logging import getLogger
from os import devnull
from os.path import join
from pprint import pformat

from ansible.errors import AnsibleRuntimeError
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play

try:
    # supports ansible < 2.4
    from ansible.inventory import Inventory
    from ansible.vars import VariableManager
except ImportError:
    # supports ansible > 2.4
    from ansible.inventory.manager import InventoryManager as Inventory
    from ansible.vars.manager import VariableManager

from paws.constants import ANSIBLE_INVENTORY_FILENAME, LINE
from paws.constants import PROVISION_YAML, WIN_EXEC_YAML
from paws.remote import PawsCallbackBase
from paws.remote.results import ResultsBase
from paws.util.decorators import retry
from paws.util import file_mgmt

LOG = getLogger(__name__)


class Ansible(object):
    """
    This class gives the ability to execute Ansible module or playbook calls
    using the Python API 2.0 and above."""

    def __init__(self, userdir):
        """Constructor.

        Instantiate all required Ansible classes.

        :param userdir: User directory file path
        :type userdir: str
        """
        self.userdir = userdir
        self.loader = DataLoader()
        self.callback = PawsCallbackBase()
        self.ansible_inventory = join(self.userdir, ANSIBLE_INVENTORY_FILENAME)
        self.inventory = None
        self.variable_manager = None

        # Module options
        self.module_options = namedtuple(
            "Options", ["connection",
                        "module_path",
                        "forks",
                        "become",
                        "become_method",
                        "become_user",
                        "check",
                        "remote_user",
                        "private_key_file",
                        "diff"]
        )

        # Playbook options
        self.playbook_options = namedtuple(
            "Options", ["connection",
                        "module_path",
                        "forks",
                        "become",
                        "become_method",
                        "become_user",
                        "check",
                        "listtags",
                        "listtasks",
                        "listhosts",
                        "syntax",
                        "remote_user",
                        "private_key_file",
                        "diff"]
        )

    def set_inventory(self):
        """Instantiate the inventory class with the inventory file in-use."""
        try:
            # supports ansible < 2.4
            self.variable_manager = VariableManager()
            self.inventory = Inventory(
                loader=self.loader,
                variable_manager=self.variable_manager,
                host_list=self.ansible_inventory
            )
        except TypeError:
            # supports ansible > 2.4
            self.variable_manager = VariableManager(loader=self.loader)
            self.inventory = Inventory(
                loader=self.loader,
                sources=self.ansible_inventory
            )
        finally:
            self.variable_manager.set_inventory(self.inventory)

    def create_hostfile(self, tp_obj=None):
        """Create Ansible inventory file to replace default (/etc/ansible/hosts).

        :param tp_obj: Resources object
        :type tp_obj: object
        """
        # Create empty file if inputs are not defined
        if tp_obj is None:
            file_mgmt('w', self.ansible_inventory, '')
            return 0

        # Can we re-use existing ansible hosts file?
        try:
            # Read hosts file
            hosts_data = file_mgmt('r', self.ansible_inventory)

            # Check that resources have entries in hosts file
            resources_count = len(tp_obj['resources'])
            counter = 0
            for item in tp_obj['resources']:
                sec = item['name']
                sec_vars = item['name'] + ':vars'
                user_match = "ansible_user = %s" % item['win_username']
                passwd_match = "ansible_password = %s" % item['win_password']
                if sec in hosts_data and sec_vars in hosts_data\
                        and passwd_match in hosts_data and user_match in\
                        hosts_data:
                    counter += 1

            if counter == resources_count:
                LOG.debug("Re-using existing Ansible hosts file")
                return 0
        except KeyError as ex:
            LOG.error("Required key: %s is missing!", ex)
            LOG.error("Unable to create Ansible hosts file. Please refer to "
                      "documentation on how to set your topology file.")
            raise SystemExit(1)
        except IOError:
            # Hosts file does not exist, need to create
            pass

        # Create config parser object
        config = ConfigParser()

        for item in tp_obj['resources']:
            # Create section
            section = item['name'].replace(" ", "")
            config.add_section(section)

            # Get resource IP
            try:
                config.set(section, item['public_v4'])
            except KeyError:
                config.set(section, item['ip'])

            # Windows variable section
            section = section + ":vars"
            config.add_section(section)
            config.set(section, "ansible_user", item['win_username'])
            config.set(section, "ansible_password", item['win_password'])
            config.set(section, "ansible_port", "5986")
            config.set(section, "ansible_connection", "winrm")
            config.set(section, "ansible_winrm_server_cert_validation",
                       "ignore")

            # Write file
            file_mgmt('w', self.ansible_inventory, cfg_parser=config)

            # Clean file, remove '= None'
            fdata = file_mgmt('r', self.ansible_inventory)
            fdata = fdata.replace(' = None', '')
            file_mgmt('w', self.ansible_inventory, fdata)

        LOG.debug("Ansible host file created %s", self.ansible_inventory)

    @retry(AnsibleRuntimeError, tries=3)
    def run_playbook(self, playbook, extra_vars=None, become=False,
                     become_method="sudo", become_user="root",
                     remote_user="root", private_key_file=None,
                     default_callback=False, results_class=ResultsBase):
        """Run an Ansible playbook against a remote machine.

        :param playbook: Playbook to call
        :type playbook: str
        :param extra_vars: Additional variables for playbook
        :type extra_vars: dict
        :param become: Whether to run as sudoer
        :type become: bool
        :param become_method: Method to use for become
        :type become_method: str
        :param become_user: User to become to run playbook call
        :type become_user: str
        :param remote_user: Connect as this user
        :type remote_user: str
        :param private_key_file: SSH private key for authentication
        :type private_key_file: str
        :param default_callback: Whether to use the default callback or not
        :type default_callback: bool
        :param results_class: Which results class to use to process results
        :type results_class: class
        """
        # Initialize new callback attribute
        self.callback = PawsCallbackBase()

        # Set ansible inventory/hosts file
        self.set_inventory()

        # Set options
        options = self.playbook_options(
            connection="smart",
            module_path="",
            forks=100,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=False,
            listtags=False,
            listtasks=False,
            listhosts=False,
            syntax=False,
            remote_user=remote_user,
            private_key_file=private_key_file,
            diff=False
        )

        # Set additional variables for use by playbook
        if extra_vars is not None:
            self.variable_manager.extra_vars = extra_vars

        LOG.debug("Running Ansible Playbook %s", playbook)
        if 'ps' in extra_vars:
            LOG.info("PowerShell script to be run %s", extra_vars['ps'])
        if 'psv' in extra_vars:
            LOG.debug("PowerShell vars %s", extra_vars['psv'])

        if PROVISION_YAML in playbook or WIN_EXEC_YAML in playbook:
            LOG.info(LINE)
            LOG.info("PLEASE WAIT WHILE ANSIBLE PLAYBOOK IS RUNNING")
            LOG.info("This could take several minutes to complete.")
            LOG.info(LINE)

        # Instantiate playbook executor object
        runner = PlaybookExecutor(
            playbooks=[playbook],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=options,
            passwords={}
        )

        # Set stdout_callback to use custom callback class
        # LOG.info(runner._tqm._stats)
        if not default_callback:
            runner._tqm._stdout_callback = self.callback

        # Save standard error stream
        org_stderr = sys.stderr
        # Redirect standard error stream to null
        sys.stderr = open(devnull, 'w')

        try:
            # Run playbook
            result = runner.run()

            # Process results
            proc = results_class(result, self.callback, default_callback)
            proc.process()
        except SystemExit:
            raise SystemExit(1)
        except AnsibleRuntimeError as ex:
            raise ex
        finally:
            # Restore standard error stream
            sys.stderr = org_stderr

    @retry(AnsibleRuntimeError, tries=3)
    def run_module(self, play_source, remote_user="root", become=False,
                   become_method="sudo", become_user="root",
                   private_key_file=None, default_callback=False,
                   results_class=ResultsBase):
        """Run an Ansible module against a remote machine.

        :param play_source: Play to be run
        :type play_source: dict
        :param remote_user: Connect as this user
        :type remote_user: str
        :param become: Whether to run as sudoer
        :type become: bool
        :param become_method: Method to use for become
        :type become_method: str
        :param become_user: User to become to run playbook call
        :type become_user: str
        :param private_key_file: SSH private key for authentication
        :type private_key_file: str
        :param default_callback: Whether to use the default callback or not
        :type default_callback: bool
        :param results_class: Which results class to use to process results
        :type results_class: class

        Example play source:
        dict(
            name="Ansible Play",
            hosts=192.168.1.1,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='ping'), register='shell_out')
            ]
        )
        """
        # Initialize new callback attribute
        self.callback = PawsCallbackBase()

        # Set inventory file
        self.set_inventory()

        # Set options
        options = self.module_options(
            connection="smart",
            module_path="",
            forks=100,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=False,
            remote_user=remote_user,
            private_key_file=private_key_file,
            diff=False
        )

        # Load the play
        play = Play().load(
            play_source,
            variable_manager=self.variable_manager,
            loader=self.loader
        )

        # Print play to be run
        amodule = play._ds['tasks'][0]['action']['module']
        LOG.debug("Running Ansible %s module" % amodule)
        LOG.debug("Ansible play: %s", pformat(play._ds))

        if 'password' not in play.name:
            LOG.info(LINE)
            LOG.info("PLEASE WAIT WHILE ANSIBLE MODULE IS RUNNING")
            LOG.info("This could take several minutes to complete.")
            LOG.info(LINE)

        # Set callback
        if default_callback:
            callback = None
        else:
            callback = self.callback

        # Run the tasks
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=options,
                passwords={},
                stdout_callback=callback
            )
            result = tqm.run(play)

            # Process results
            proc = results_class(result, self.callback, default_callback)
            proc.process()
        except SystemExit:
            raise SystemExit(1)
        except AnsibleRuntimeError as ex:
            raise ex
        finally:
            if tqm is not None:
                tqm.cleanup()
