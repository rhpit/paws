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

"""Show module will retrieve instances info (via Ansible) against the
provider in user and based on machines pre-defined within a YAML file and
resulting at message displayed at console output.
"""
from ansible.errors import AnsibleRuntimeError

from paws.core import PawsTask, Namespace
from paws.exceptions import NovaPasswordError, SSHError
from paws.helpers import log_resources
from paws.providers import Provider


class Show(PawsTask):
    """Paws show task.

    This class will handling showing Windows systems information.
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

            $ paws <options> show <options>

            -- API --

        .. code-block:: python

            from paws.tasks import Show

            show = Show(
                userdir,
                resources,
                credentials
            )
            show.run()
        """
        super(Show, self).__init__(userdir, verbose)
        self.resources = resources
        self.credentials = credentials

        try:
            if isinstance(kwargs['args'], Namespace):
                self.args = kwargs['args']
        except KeyError:
            self.args = Namespace(kwargs)

        self.provider = Provider(
            self.userdir,
            self.resources,
            self.credentials,
            self.resources_paws_file,
            self.verbose
        )

    def run(self):
        """Show task is a informative command for end-user. When show is
        invoked by paws command line it will read the resources.json from
        userdir, generate the get_facts ansible playbook and execute the
        ansible call against the provider retreiving all info about the
        system resources that match from resources.json and provider. The
        result will be the update of resources.paws and a message displayed
        to user console with resource information.
        """
        try:
            self.logger.info("START: %s", self.name)

            # Save start time
            self.start()

            # Run provider action
            self.resources_paws = self.provider.run_action(self.name.lower())

            # Log system resources details to console
            log_resources(self.resources_paws, "show")
        except (AnsibleRuntimeError, NovaPasswordError, SSHError,
                KeyboardInterrupt, SystemExit) as ex:
            # set exit code
            self.exit_code = 1

            if isinstance(ex, KeyboardInterrupt):
                self.logger.warning("CTRL+C detected, interrupting execution")
        finally:
            # save end time
            self.end()

            self.logger.info("END: %s, TIME: %dh:%dm:%ds",
                             self.name, self.hours, self.minutes, self.seconds)

        return self.exit_code
