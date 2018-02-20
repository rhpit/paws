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

from paws.core import Namespace, PawsTask
from paws.exceptions import NotFound, ProvisionError, TeardownError
from paws.helpers import log_resources
from paws.providers import Provider


class Action(PawsTask):
    """Paws action task.

    This class is the base action class for all paws tasks. Paws has tasks
    that are very similar in the way they need to be called. This base class
    can be inherited by each child class to remove code duplication.
    """

    def __init__(self, user_dir, resources, credentials, verbose=0, **kwargs):
        """Constructor.

        :param user_dir: user directory
        :type user_dir: str
        :param resources: windows resources
        :type resources: dict
        :param credentials: provider credentials
        :type credentials: dict
        :param verbose: verbose mode
        :type verbose: int
        :param kwargs: extra parameters (key:value) form
        :type kwargs: dict
        """
        super(Action, self).__init__(user_dir, verbose)
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
        """Process the action at stake.

        It will work with the provider class to process the action given.
        """
        try:
            self.logger.info('Starting %s task', self.name)
            self.start()
            self.resources_paws = self.provider.run_action(self.name.lower())
            if self.resources_paws['resources']:
                log_resources(self.resources_paws, self.name.lower())
        except (NotFound, ProvisionError, TeardownError) as ex:
            self.logger.error(ex.message)
            self.exit_code = 1
        except KeyboardInterrupt:
            self.logger.warning('Execution interrupted by crtl+c!')
            self.exit_code = 1
        finally:
            self.end()
            self.logger.info(
                'Ending %s task in %dh:%dm:%ds', self.name.lower(),
                self.hours, self.minutes, self.seconds
            )

        return self.exit_code


class Provision(Action):
    """Paws provision task.

    This class will handle provisioning windows resources in their defined
    provider.
    """

    def __init__(self, user_dir, resources, credentials, verbose=0, **kwargs):
        """Constructor.

        Usage:

            -- CLI --

        .. code-block: bash

            $ paws <options> provision <options>

            -- API --

        .. code-block: python

            from paws.tasks import Provision

            provision = Provision(
                user_dir,
                resources,
                credentials
            )
            provision.run()
        """
        super(Provision, self).__init__(
            user_dir, resources, credentials, verbose=verbose, **kwargs)


class Teardown(Action):
    """Paws teardown task.

    This class will handle tearing down windows resources in their defined
    provider.
    """

    def __init__(self, user_dir, resources, credentials, verbose=0, **kwargs):
        """Constructor.

        Usage:

            -- CLI --

        .. code-block: bash

            $ paws <options> teardown <options>

            -- API --

        .. code-block: python

            from paws.tasks import Teardown

            teardown = teardown(
                user_dir,
                resources,
                credentials
            )
            teardown.run()
        """
        super(Teardown, self).__init__(
            user_dir, resources, credentials, verbose=verbose, **kwargs)


class Show(Action):
    """Paws show task.

    This class will handling showing all windows resources provisioned.
    """

    def __init__(self, user_dir, resources, credentials, verbose=0, **kwargs):
        """Constructor.

        Usage:

            -- CLI --

        .. code-block: bash

            $ paws <options> show <options>

            -- API --

        .. code-block: python

            from paws.tasks import Show

            Show = Show(
                user_dir,
                resources,
                credentials
            )
            show.run()
        """
        super(Show, self).__init__(
            user_dir, resources, credentials, verbose=verbose, **kwargs)
