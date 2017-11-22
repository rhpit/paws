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
Main class
"""

from importlib import import_module

from os.path import join

from paws.constants import LINE, PAWS_NAME
from paws.util import LoggerMixin, TimeMixin, file_mgmt


class Paws(LoggerMixin, TimeMixin):
    """Paws class."""

    def __init__(self, task, task_module, args):
        """Constructor.

        :param task: Name of paws task to call
        :type task: str
        :param task_module: Paws task absolute path
        :type task_module: str
        :param args: Paws task options (Python namespace object)
        :type args: object
        """
        self.task = task
        self.task_module = task_module
        self.args = args

        # create logger
        self.create_logger(PAWS_NAME, self.args.verbose)

    def run(self):
        """Run a paws task."""
        # save start time
        self.start()

        # log commands options
        self.logger.info("Begin paws execution")
        self.logger.debug(LINE)
        self.logger.debug("Paws options".center(45))
        self.logger.debug(LINE)
        for key, value in vars(self.args).items():
            self.logger.debug("%s: %s", key, value)
        self.logger.debug(LINE)

        # import paws task
        pmodule = import_module(self.task_module)

        # get the class attribute
        task_cls = getattr(pmodule, self.task.title())

        # create an object from the class
        if self.task.lower() == 'group':
            # read files
            try:
                group = file_mgmt('r', join(self.args.userdir, self.args.name))
            except IOError as ex:
                self.logger.error('Group file %s' % ex.message)
                raise SystemExit(1)

            # create task object
            task = task_cls(
                self.args.userdir,
                group,
                self.args.verbose,
                args=self.args
            )
        else:
            # read files
            try:
                credentials = file_mgmt(
                    'r',
                    join(self.args.userdir, self.args.credentials)
                )
            except (AttributeError, IOError):
                credentials = None

            resources = file_mgmt(
                'r',
                join(self.args.userdir, self.args.topology)
            )

            # create task object
            task = task_cls(
                self.args.userdir,
                resources,
                credentials,
                self.args.verbose,
                args=self.args
            )

        # run task
        exit_code = task.run()

        # save end time
        self.end()

        self.logger.info("End paws execution in %dh:%dm:%ds",
                         self.hours, self.minutes, self.seconds)

        raise SystemExit(exit_code)
