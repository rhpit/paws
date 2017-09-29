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

from ansible.errors import AnsibleRuntimeError
from novaclient.exceptions import ClientException

from paws import __name__ as __paws_name__
from paws.constants import LINE
from paws.exceptions import ProvisionError, PawsPreTaskError, SSHError
from paws.exceptions import ShowError
from paws.util import LoggerMixin, TimeMixin


class Paws(LoggerMixin, TimeMixin):
    """Paws class."""

    def __init__(self, task, task_module, args):
        """Constructor.

        :param task: Name of paws task to call
        :param task_module: Paws task absolute path
        :param args: Paws task options (Python namespace object)
        """
        self.task = task
        self.task_module = task_module
        self.args = args

        # create logger
        self.create_logger(__paws_name__, self.args.verbose)

    def run(self):
        """Run a paws task."""
        # Result
        result = 0

        try:
            # Save start time
            self.start()

            # Log commands options
            self.logger.info("Begin paws execution")
            self.logger.debug(LINE)
            self.logger.debug("Paws options".center(45))
            self.logger.debug(LINE)
            for key, value in vars(self.args).items():
                self.logger.debug("%s: %s", key, value)
            self.logger.debug(LINE)

            # Import paws task
            module = import_module(self.task_module)

            # Get the class attribute
            task_cls = getattr(module, self.task.title())

            # Create an object from the class
            task = task_cls(self.args)

            # Run paws pre tasks
            task.pre_tasks()

            # Run paws task
            task.run()
        except Exception as ex:
            if ex.message:
                self.logger.error(ex)
        except PawsPreTaskError:
            result = 1
        except (AnsibleRuntimeError, ClientException, SSHError, SystemExit,
                ShowError):
            task.post_tasks()
            result = 1
        except ProvisionError:
            task.post_tasks()
            self.teardown_resources()
            result = 1
        except KeyboardInterrupt:
            self.logger.warning("CRTL+C detected, interrupting execution")
            task.post_tasks()
            result = 1
        finally:
            # Save stop time
            self.end()

            self.logger.info("End paws execution in %dh:%dm:%ds",
                             self.hours, self.minutes, self.seconds)

            raise SystemExit(result)

    def teardown_resources(self):
        """Teardown system resources when applicable."""
        from paws.tasks.teardown import Teardown
        teardown = Teardown(self.args)

        try:
            # Run pre tasks
            teardown.pre_tasks()

            # Run task
            teardown.run()
        except (AnsibleRuntimeError, KeyboardInterrupt, SystemExit):
            teardown.post_tasks()
