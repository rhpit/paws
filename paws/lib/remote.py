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

"""Module containing classes and functions regarding remote connections."""

import sys
from logging import getLogger
from pprint import pformat

import os
from click_spinner import spinner
from collections import namedtuple

try:
    # < 2.4
    from ansible.inventory import Inventory
    from ansible.vars import VariableManager
except ImportError:
    # > 2.4
    from ansible.inventory.manager import InventoryManager as Inventory
    from ansible.vars.manager import VariableManager

from ansible.errors import AnsibleRuntimeError
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase

from paws.compat import RawConfigParser
from paws.constants import ANSIBLE_INVENTORY_FILENAME as ANSIBLE_INVENTORY
from paws.helpers import retry
from paws.helpers import file_mgmt

LOG = getLogger(__name__)

__all__ = ['inventory_init', 'inventory_reuse', 'create_inventory',
           'PawsCallback', 'ResultsHandler', 'PlayCall', 'PlaybookCall',
           'GenModuleResults', 'ParsePSResults']


def inventory_init(filename):
    """Initialize a inventory file.

    This will just touch an empty inventory file in the user directory. It is
    primarily called to ignore ansible warning messages when running commands
    on the local host.

    :param filename: inventory file
    """
    file_mgmt('w', filename, '')


def inventory_reuse(filename, resources):
    """Determine if we can re-use an existing inventory file.

    This will check if the resources given exist within the existing inventory
    file. If they are we can reuse the file!

    :param filename: inventory file
    :param resources: windows resources
    """
    if not os.path.exists(filename):
        # inventory not found
        return False

    try:
        # load existing inventory
        data = file_mgmt('r', filename)

        count = 0

        # do the active resources exist within the inventory?
        for res in resources['resources']:
            sec = res['name']
            sec_vars = res['name'] + ':vars'
            user = 'ansible_user = %s' % res['win_username']
            password = 'ansible_password = %s' % res['win_password']

            if sec in data and sec_vars in data and user in data and \
                    password in data:
                count += 1

            if count == len(resources['resources']):
                LOG.debug('Reusing inventory file.')
                return True
    except KeyError as ex:
        LOG.error('Required resource key %s missing!', ex)
        raise SystemExit(1)
    except IOError:
        return False


def create_inventory(filename, resources=None):
    """Create a inventory file.

    :param filename: inventory file
    :param resources: windows resources
    """

    # can we reuse a existing inventory file?
    if inventory_reuse(filename, resources):
        return

    config = RawConfigParser()

    for item in resources['resources']:
        section = item['name'].replace(" ", "")
        config.add_section(section)

        try:
            config.set(section, str(item['public_v4']))
        except KeyError:
            config.set(section, item['ip'])

        section = section + ":vars"
        config.add_section(section)
        config.set(section, "ansible_user", item['win_username'])
        config.set(section, "ansible_password", item['win_password'])
        config.set(section, "ansible_port", "5986")
        config.set(section, "ansible_connection", "winrm")
        config.set(section, "ansible_winrm_server_cert_validation",
                   "ignore")

        file_mgmt('w', filename, cfg_parser=config)

        # clean file, remove '= None'
        inv_data = file_mgmt('r', filename)
        inv_data = inv_data.replace(' = None', '')
        file_mgmt('w', filename, inv_data)

        LOG.debug("Inventory file %s created.", filename)


class PawsCallback(CallbackBase):
    """Paws own ansible custom callback class."""

    def __init__(self):
        """Constructor."""
        super(PawsCallback, self).__init__()
        self.contacted = []
        self.unreachable = False

    def v2_runner_on_ok(self, result):
        """Handle 'ok' results.

        :param result: module or playbook call results
        """
        super(PawsCallback, self).v2_runner_on_ok(result)
        self.contacted.append(
            dict(
                host=getattr(result, '_host').get_name(),
                success=True,
                results=getattr(result, '_result')
            )
        )

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Handle 'failed' results.

        :param result: module or playbook call results
        :param ignore_errors: flag to control ignoring errors
        """
        super(PawsCallback, self).v2_runner_on_failed(result, ignore_errors)
        self.contacted.append(
            dict(
                host=getattr(result, '_host').get_name(),
                success=False,
                results=getattr(result, '_result')
            )
        )

    def v2_runner_on_unreachable(self, result):
        """Handle 'unreachable results.

        :param result: module or playbook call results
        '"""
        super(PawsCallback, self).v2_runner_on_unreachable(result)
        self.unreachable = True


class ResultsHandler(object):
    """Base results handler to handle play or playbook results."""

    def __init__(self, exit_code, callback, def_callback):
        """Constructor.

        :param exit_code: module or playbook exit code
        :param callback: module or playbook callback object
        :param def_callback: flag to control when to use the default callback
        """
        self.exit_code = exit_code
        self.callback = callback
        self.def_callback = def_callback

    def message(self):
        """Message about the results."""
        if self.exit_code != 0:
            status = "execution failed"
        else:
            status = "executed successfully"

        LOG.info("Ansible call %s!", status)

        if self.callback.contacted and self.callback.\
                contacted[0]['success'] is False:
            LOG.error(self.callback.contacted[0]['results']['msg'])

    def abort(self):
        """Abort the program."""
        if self.exit_code:
            raise AnsibleRuntimeError

    def process(self):
        """Process results."""
        if not self.def_callback:
            LOG.debug(pformat(self.callback.contacted, indent=2))

        self.message()
        self.abort()


class ParsePSResults(ResultsHandler):
    """Parse Windows PowerShell script results run via Ansible."""

    def __init__(self, exit_code, callback, def_callback):
        """Constructor."""
        super(ParsePSResults, self).__init__(exit_code, callback, def_callback)

    def process(self):
        """Process results."""
        length = 25
        for item in self.callback.contacted:
            LOG.info('-' * length)
            LOG.info('System : %s' % item['host'])
            LOG.info('-' * length)

            if 'stdout' in item['results'] and item['results']['stdout']:
                    LOG.info("-" * length)
                    LOG.info('Standard Output'.center(length))
                    LOG.info("-" * length)
                    LOG.info(item['results']['stdout'])

            if 'stderr' in item['results'] and item['results']['stderr']:
                LOG.info("-" * length)
                LOG.info('Standard Error'.center(length))
                LOG.info("-" * length)
                LOG.info(item['results']['stderr'])

        if self.callback.contacted.__len__() == 0:
            LOG.error("Failed to contact remote hosts.")
            self.exit_code = 1

        self.message()
        self.abort()


class GenModuleResults(ResultsHandler):
    """Process generic ansible modules results.

    DEPRECATED with 0.5.0 release. This class aligns with winsetup task.
    """

    def __init__(self, exit_code, callback, def_callback):
        """Constructor."""
        ResultsHandler.__init__(self, exit_code, callback, def_callback)

    def process(self):
        """Process results."""
        LOG.info("-" * 15)
        LOG.info("Results")
        LOG.info("-" * 15)

        for item in self.callback.contacted:
            try:
                if 'results' in item and item['results']['changed']\
                        and 'rc' in item['results']:
                    LOG.info("** %s **", item['host'])

                    # Standard output
                    if self.exit_code == 0:
                        LOG.info("Standard output:")
                        for line in item['results']['stdout_lines']:
                            LOG.info(line)

                    # Standard error
                    if self.exit_code != 0:
                        LOG.info("Standard error:")
                        LOG.error(item['results']['stderr'])
                        for line in item['results']['stdout_lines']:
                            LOG.error(line)
            except KeyError:
                pass

        if self.callback.contacted.__len__() == 0:
            LOG.error("Failed to contact remote hosts.")
            self.exit_code = 1

        self.message()
        self.abort()


class BaseCall(object):
    """Base class for play and playbooks."""

    def __init__(self, user_dir):
        """Constructor.

        :param user_dir: user directory
        """
        self.loader = DataLoader()
        self.inventory_file = os.path.join(user_dir, ANSIBLE_INVENTORY)
        self.callback = PawsCallback()
        self.inventory = None
        self.var_mgr = None

    def _set_inventory(self):
        """Set inventory class req. by ansible api."""
        try:
            # < 2.4
            self.var_mgr = VariableManager()
            self.inventory = Inventory(
                loader=self.loader,
                variable_manager=self.var_mgr,
                host_list=self.inventory_file
            )
        except TypeError:
            # > 2.4
            self.var_mgr = VariableManager(loader=self.loader)
            self.inventory = Inventory(
                loader=self.loader,
                sources=self.inventory_file
            )
        finally:
            self.var_mgr.set_inventory(self.inventory)


class PlayCall(BaseCall):
    """Play execution."""

    def __init__(self, user_dir):
        """Constructor.

        :param user_dir: user directory
        """
        super(PlayCall, self).__init__(user_dir)
        self.options = namedtuple(
            'Options', [
                'connection',
                'module_path',
                'forks',
                'become',
                'become_method',
                'become_user',
                'check',
                'remote_user',
                'private_key_file',
                'diff'
            ]
        )

    @retry(AnsibleRuntimeError, tries=3)
    def run(self, play, remote_user="root", become=False,
            become_method="sudo", become_user="root",
            private_key_file=None, default_callback=False,
            results_class=ResultsHandler):
        """Run the given play.

        :param play: play source
        :param remote_user: remote user used during connection
        :param become: run as sudo
        :param become_method: method to use for become
        :param become_user: user to run play
        :param private_key_file: ssh private key for auth
        :param default_callback: enable default callback
        :param results_class: which results class to process results

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

        # create callback object
        self.callback = PawsCallback()

        # create inventory object
        self._set_inventory()

        # set options
        options = self.options(
            connection='smart',
            module_path='',
            forks=100,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=False,
            remote_user=remote_user,
            private_key_file=private_key_file,
            diff=False
        )

        # load play
        play = Play().load(
            play,
            variable_manager=self.var_mgr,
            loader=self.loader
        )

        LOG.info('Running play:\n%s' % getattr(play, '_ds'))

        if default_callback:
            callback = None
        else:
            callback = self.callback

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.var_mgr,
                loader=self.loader,
                options=options,
                passwords=dict(),
                stdout_callback=callback
            )

            # run play
            with spinner():
                result = tqm.run(play)

            # process results
            if not default_callback:
                res = results_class(result, self.callback, default_callback)
                res.process()
        except SystemExit:
            raise SystemExit(1)
        except AnsibleRuntimeError as ex:
            raise ex
        finally:
            if tqm is not None:
                tqm.cleanup()


class PlaybookCall(BaseCall):
    """Playbook execution."""

    def __init__(self, user_dir):
        """Constructor.

        :param user_dir: user directory
        """
        super(PlaybookCall, self).__init__(user_dir)
        self.options = namedtuple(
            'Options', [
                'connection',
                'module_path',
                'forks',
                'become',
                'become_method',
                'become_user',
                'check',
                'listtags',
                'listtasks',
                'listhosts',
                'syntax',
                'remote_user',
                'private_key_file',
                'diff'
            ]
        )

    @retry(AnsibleRuntimeError, tries=3)
    def run(self, playbook, extra_vars=None, become=False,
            become_method="sudo", become_user="root",
            remote_user="root", private_key_file=None,
            default_callback=False, results_class=ResultsHandler):
        """Run the given playbook.

        :param playbook: playbook file
        :param extra_vars: additional variables for playbook
        :param remote_user: remote user used during connection
        :param become: run as sudo
        :param become_method: method to use for become
        :param become_user: user to run play
        :param private_key_file: ssh private key for auth
        :param default_callback: enable default callback
        :param results_class: which results class to process results
        """

        # create callback object
        self.callback = PawsCallback()

        # create inventory object
        self._set_inventory()

        # set options
        options = self.options(
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

        # set additional playbook variables
        if extra_vars is not None:
            self.var_mgr.extra_vars = extra_vars

        LOG.info('Running playbook: %s' % playbook)
        if 'ps' in extra_vars:
            LOG.info('Executing PowerShell %s' % extra_vars['ps'])
        if 'psv' in extra_vars:
            LOG.debug("PowerShell vars %s", extra_vars['psv'])

        # load playbook
        runner = PlaybookExecutor(
            playbooks=[playbook],
            inventory=self.inventory,
            variable_manager=self.var_mgr,
            loader=self.loader,
            options=options,
            passwords=dict()
        )

        # set stdout_callback to use custom callback class
        # LOG.info(runner._tqm._stats)
        if not default_callback:
            runner._tqm._stdout_callback = self.callback

        # save standard error stream
        org_stderr = sys.stderr
        # Redirect standard error stream to null
        sys.stderr = open(os.devnull, 'w')

        try:
            # run playbook
            with spinner():
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
