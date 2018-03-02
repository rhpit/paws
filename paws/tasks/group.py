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

"""Group task."""

from time import sleep

import re
from importlib import import_module
from os.path import join

from paws.constants import GROUP_SECTIONS, GROUP_SCHEMA, TASK_ARGS, \
    GROUP_HELP, GROUP_REQUIRED
from paws.core import PawsTask, Namespace
from paws.helpers import check_file, file_mgmt, get_task_module_path


class Group(PawsTask):
    """Paws group task.

    The main group class. This class will run a paws group file (YAML)
    formatted which contains a list of paws tasks to run. Groups are helpful
    when paws is used within automated tests or to easily share your
    workflow with other folks.

    Groups eliminate the need to run multiple individual paws commands by
    combining them into one pipeline of tasks.
    """

    _header_name = GROUP_SECTIONS[0]
    _vars_name = GROUP_SECTIONS[1]
    _tasks_name = GROUP_SECTIONS[2]

    def __init__(self, userdir, group, verbose=0, **kwargs):
        """Constructor.

        :param userdir: User directory.
        :type userdir: str
        :param group: Group content.
        :type group: dict
        :param verbose: Verbosity level.
        :type verbose: int
        :param kwargs: Extra key:value data.
        :type kwargs: dict

        Usage:

            -- CLI --

        .. code-block: bash

            $ paws <options> group <options>

            -- API --

        .. code-block:: python

            from paws.tasks import Group

            group = Group(
                userdir,
                group
            )
            group.run()
        """
        super(Group, self).__init__(userdir, verbose)
        self.group = group

        try:
            if isinstance(kwargs['args'], Namespace):
                self.args = kwargs['args']
        except KeyError:
            self.args = Namespace(kwargs)

        self.groupdata = self.load()
        self.header_pos = 0
        self.vars_pos = 0
        self.tasks_pos = 0
        self.tasklist = []

    def pre_run(self):
        """Perform any necessary pre task actions."""
        # Group validation
        self.validation()

        # Update task list
        self.tasklist = self.groupdata['tasks']

        # Set common arguments used by all tasks in memory
        self.set_task_attr(
            self.map_task_args(self.groupdata['vars'])
        )

    def validation(self):
        """Group validation function, check group schema and content of each
        individual key based on regex rules specified in GROUP_REQUIRED"""

        self.logger.debug("Group validating")
        _help = "Please refer to %s to setup your group file" % GROUP_HELP
        _req = "Required section:"
        _rule = "Validation rules:"

        # 1st validation, for key elements from group schema
        for kst, vst in self.groupdata.items():
            if not vst or vst is None:
                self.logger.error("%s %s is missing from group" % (_req, kst))
                self.logger.error(_help)
                raise SystemExit(1)

        # 2nd validation, for items required
        for krnd, vrnd in GROUP_REQUIRED.items():
            for kdnd, vdnd in self.groupdata.items():
                # level 1 (header, vars, tasks)
                if krnd == kdnd:
                    # level 2
                    for elem in vrnd:
                        for key, value in elem.iteritems():
                            # key must exist
                            if key not in vdnd:
                                self.logger.error("%s %s is missing from %s" %
                                                  (_req, key, krnd))
                                self.logger.error(_help)
                                raise SystemExit(1)
                            # key must exist
                            if not vdnd[key]:
                                self.logger.error("%s check content of %s in %s. \
A topology file is required." % (_rule, key, krnd))
                                self.logger.error(_help)
                                raise SystemExit(1)
                            # checking content based on regex rules
                            pattern = re.compile(value)
                            if pattern.match(vdnd[key]) is None:
                                self.logger.error("%s check file name and extension \
in %s %s. Expected .yaml or .yml" % (_rule, krnd, key))
                                self.logger.error(_help)
                                raise SystemExit(1)

        # 3rd validation, check files exist in disk
        for kvar, vvar in self.groupdata['vars'].items():
            if kvar and not vvar:
                raise IOError("check %s, %s declared with empty value"
                              % (join(self.userdir, self.args.name),
                                 kvar))

            file_path = join(self.userdir, vvar)
            error_msg = "check %s in %s" % (kvar, self.args.name)
            check_file(file_path, error_msg)

        # 4th validation, check powershell files from tasks
        for task in self.groupdata['tasks']:
            if 'args' in task:
                for arg in task['args']:
                    if 'powershell' in arg and arg['powershell']:
                        file_path = join(self.userdir, arg['powershell'])
                        error_msg = "check args in task name %s" \
                            % (task['name'])
                        check_file(file_path, error_msg)

    @staticmethod
    def map_task_args(options):
        """Returns arg mapped to their correct dest name for CLI arguments.

        This functionality allows users to create groups with either short or
        long keyname formatting.
        """
        results = {}

        for option, value in options.items():
            dest = ""
            # Loop through available CLI args/map to destination name
            for dest_name, values in TASK_ARGS.items():
                if "-" + option in values['options']:
                    dest = dest_name
                    break
                elif "--" + option in values['options']:
                    dest = dest_name
                    break

            if dest:
                results[dest] = value

        return results

    @staticmethod
    def group_normalize(data):
        """Normalize data to group yaml schema"""
        g_normalized = GROUP_SCHEMA

        for gsec in GROUP_SECTIONS:
            for elem in data:
                if gsec in elem:
                    if elem[gsec] is None:
                        elem.pop(gsec, None)
                        g_normalized[gsec] = elem
                    else:
                        g_normalized[gsec] = elem[gsec]

        return g_normalized

    def load(self):
        """Load paws group content."""
        return self.group_normalize(self.group['group'])

    def set_task_attr(self, args):
        """Set task attributes."""
        for key, value in args.items():
            setattr(self.args, key, value)

    def del_task_attr(self, args):
        """Delete task attributes."""
        for key in args:
            delattr(self.args, key)

    def run(self):
        """The main method for group. This method will run a ordered list of
        paws tasks."""
        # pre run tasks
        self.pre_run()

        self.logger.info("START: %s", self.name)

        # save the start time
        self.start()

        for item in self.tasklist:
            task = item['task'].lower()
            self.logger.info("Running: %s (task=%s)" % (item['name'], task))

            # wait
            if task == 'wait':
                try:
                    duration = item['duration']
                    self.logger.info("Delaying %ss" % duration)
                    sleep(int(duration))
                    continue
                except KeyError:
                    self.logger.warning(
                        "Delay duration was not set! Skipping.."
                    )
                    continue

            if 'args' in item:
                # combine list of dict into one dict
                args = {key: value for item in item[
                    'args'] for key, value in item.items()}

                # set task specific arguments into memory
                self.set_task_attr(self.map_task_args(args))

            # import task module
            pmodule = import_module(get_task_module_path(task))

            # get task class
            task_cls = getattr(pmodule, task.title())

            # read files
            _vars = self.groupdata['vars']
            try:
                credentials = file_mgmt(
                    'r',
                    join(self.userdir, _vars['credentials'])
                )
            except (AttributeError, IOError):
                credentials = None

            resources = file_mgmt(
                'r',
                join(self.userdir, _vars['topology'])
            )

            # create object from task class
            task = task_cls(
                self.userdir,
                resources,
                credentials,
                self.verbose,
                args=self.args
            )

            # run task
            exit_code = task.run()

            # quit group execution if exit code is not zero
            if exit_code != 0:
                self.exit_code = exit_code
                break

            if 'args' in item:
                # delete task arguments values from memory
                self.del_task_attr(self.map_task_args(args))

        # save end time
        self.end()

        self.logger.info("END: Group, TIME: %dh:%dm:%ds",
                         self.hours, self.minutes, self.seconds)

        return self.exit_code
