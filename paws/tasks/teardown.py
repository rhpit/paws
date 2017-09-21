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

"""Teardown task."""

from logging import getLogger
from os.path import join

from ansible.errors import AnsibleRuntimeError

from paws.constants import GET_OPS_FACTS_YAML
from paws.tasks import Tasks
from paws.util import cleanup, log_resources
from paws.util.decorators import handle_pre_tasks
from paws.providers import Provider

LOG = getLogger(__name__)


class Teardown(Tasks):
    """Teardown."""

    def __init__(self, args):
        """Constructor.

        :param args: Argparse arguments
        :type arg: class argparse.Namespace
        """
        super(Teardown, self).__init__(args)
        self.credential_file = join(self.userdir, args.credentials)
        self.getfacts_playbook = join(args.userdir, GET_OPS_FACTS_YAML)
        self.provider = Provider(self)

    @handle_pre_tasks
    def pre_tasks(self):
        """Perform any necessary pre task actions."""
        # Clean files generated by paws
        for provider_name in self.provider.provider_list:
            inst = self.provider.get_instance(provider_name)
            garbage = inst.garbage_collector()
            garbage.append(self.resources_paws)
            garbage.append(self.getfacts_playbook)
            cleanup(garbage, self.userdir)

    def run(self):
        """The main method for teardown. This method will call the providers
        module class to start calling teardown method for the resources
        corresponding provider.
        """
        try:
            LOG.info("START: %s", self.__class__.__name__)

            # Save start time
            self.start()

            # Run provider action
            self.provider.run_action(self.__class__.__name__.lower())

            # Perform post tasks
            self.post_tasks()
        except SystemExit:
            raise SystemExit(1)
        except AnsibleRuntimeError:
            raise AnsibleRuntimeError
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def post_tasks(self):
        """Perform any necessary post task actions."""
        # Save end time
        self.end()

        # Log system resources details to console
        log_resources(self.resources_paws, "deleted")

        LOG.info("END: Teardown, TIME: %dh:%dm:%ds",
                 self.hours, self.minutes, self.seconds)
