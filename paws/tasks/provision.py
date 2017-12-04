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

"""Provision task."""
from ansible.errors import AnsibleRuntimeError

from paws.core import PawsTask, Namespace
from paws.exceptions import NovaPasswordError, SSHError
from paws.helpers import log_resources
from paws.providers import Provider


class Provision(PawsTask):
    """Paws provision task.

    This class will handle provisioning Windows resources in their provided
    provider.
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

            $ paws <options> provision <options>

            -- API --

        .. code-block:: python

            from paws.tasks import Provision

            provision = Provision(
                userdir,
                resources,
                credentials
            )
            provision.run()
        """
        super(Provision, self).__init__(userdir, verbose)
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
        """The main method for provision. This method will call the providers
        module class to start calling provision method for the resources
        corresponding provider.
        """
        try:
            self.logger.info("START: %s", self.name)

            # Save start time
            self.start()

            # Run provider action
            self.resources_paws = self.provider.run_action(self.name.lower())
        except (AnsibleRuntimeError, NovaPasswordError, SSHError,
                KeyboardInterrupt, SystemExit) as ex:
            # set exit code
            self.exit_code = 1

            if isinstance(ex, KeyboardInterrupt):
                self.logger.warning("CTRL+C detected, interrupting execution")
            # teardown system resources
            self.provider.run_action('teardown')
        finally:
            # save end time
            self.end()

            # log system resources details to console
            log_resources(self.resources_paws, 'provisioned')

            self.logger.info("END: %s, TIME: %dh:%dm:%ds",
                             self.name, self.hours, self.minutes, self.seconds)

        return self.exit_code
