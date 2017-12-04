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
"""Paws providers."""

import importlib

from paws.constants import PROVIDERS
from paws.core import LoggerMixin, Namespace
from paws.helpers import cleanup


class Provider(LoggerMixin):
    """ Provider

    It is the main class for Provider module. This module manage
    registered providers e.g.: Openstack, Libvirt etc in PAWS and
    there are some important things:

    1. we use importlib for dynamic import and dynamic object creation. It
    allows us to plug new providers easily into PAWS also giving generic
    and reusable methods not tied in a specific provider.

    2. the basic flow communication needs to be between TASKS, PROVIDER and
    PROVIDERS entities to avoid inter

    3. The main principle is a real provider needs to have access to:
        * topology described by user (resources.yaml)
        * provider credentials or content of credentials file for that
        specific provider only
        * if provision has been executed then it needs to know the content
        of resources.paws
        * some arguments initialized during runtime that are expected by
        registered provider.

    4. Provider should know the minimum as possible of registered provider
    letting details be implemented at registered provider side.

    ------
    Legend
    ------

    TASKS: classes from paws.task like provision, show, teardown, group etc
    PROVIDER: this main class
    REGISTERED PROVIDERS: supported by PAWS e.g.: Openstack, Libvirt

                                                            __________
     _______      __________      ______________________   | Openstack|
    |       |    |          |    |                      |--------------
    | TASKS | => | PROVIDER | => | REGISTERED PROVIDERS |   __________
    |_______|    |__________|    |______________________|--|  Libvirt |
                                                           ------------

    """

    def __init__(self, userdir, resources, credentials, resources_paws_file,
                 verbose):
        """Constructor.

        :param userdir: User directory.
        :type userdir: str
        :param resources: System resources.
        :type resources: dict
        :param credentials: Provider credentials.
        :type credentials: dict
        :param resources_paws_file: Resources.paws file name.
        :type resources_paws_file: str
        :param verbose: Verbosity level.
        :type verbose: int
        """
        self.userdir = userdir
        self.resources = resources
        self.credentials = credentials
        self.resources_paws_file = resources_paws_file
        self.verbose = verbose

        self.provider_list = self.get_provider()

    def get_provider(self):
        """ Get provider from all elements declared in resources.yaml or
        topology file and return a list with non-duplicated elements

        :return: list with providers extracted from topology file
        :rtype: set
        """
        provider_list = set()

        for resource in self.resources['resources']:
            provider_list.add(resource['provider'])

        return provider_list

    def get_resources_by_provider(self, provider):
        """Get system resources by provider name from a given file.
        Open the file and search for all system resources defined by
        the provider passed as parameter

        :param provider: name of registered provider supported by PAWS
        :type provider: str
        :return: content from resources.yaml and .paws files
        :rtype: list contains one or more lists of dicts
        """
        resource_list = []

        for elem in self.resources['resources']:
            if provider in elem['provider']:
                resource_list.append(elem)
        return resource_list

    def get_creds_by_provider(self, provider):
        """Get credentials by provider name from a given file.
        Open the file and search by provider passed as parameter

        :param provider: name of registered provider supported by PAWS
        :type provider: str
        :return: content from credentials.yaml
        :rtype: dict
        """
        if self.credentials:
            for elem in self.credentials['credentials']:
                if provider in elem['provider']:
                    return elem

    @staticmethod
    def get_provider_info_by_name(provider_name):
        """Get registration info from provider passed as parameter.
        this method retrieve Code/Object information from Constants
        module and it is used as a helper function for dynamic object
        creation

        :param provider_name: name of provider
        :type provider_name: str
        :return provider registration
        :rtype provider: dict
        """
        for provider in PROVIDERS:
            if provider_name in provider['name']:
                return provider

    def get_provider_class(self, name):
        """Get the provider class.

        :param name: Provider class name.
        :type name: str
        """
        prov_info = self.get_provider_info_by_name(name)
        my_module = importlib.import_module(prov_info['module'])
        klass = getattr(my_module, prov_info['class'])
        return klass

    def run_action(self, action):
        """ Read resources.yaml and get the providers from all element
        declared to be provisioned. Then filter elements by provider
        in a loop and using dynamic class with importlib module
        create a class of provider from list of providers of
        resources.yaml and call the method passed as action parameter

        :param action: name of method to be executed
        :type action: str
        """
        for provider_name in self.provider_list:
            # create new namespace
            namespace = Namespace(dict())

            # set attributes for namespace
            namespace.userdir = self.userdir
            namespace.resources_paws_file = self.resources_paws_file
            namespace.verbose = self.verbose

            # get resources by provider
            namespace.resources = self.get_resources_by_provider(provider_name)

            # get provider credentials for resources
            namespace.credentials = self.get_creds_by_provider(provider_name)

            # get provider class
            klass = self.get_provider_class(provider_name)

            # create instance
            inst = klass(namespace)

            # run provider's garbage collector
            # TODO: what about multiple resources? we should or not
            # delete self.resources_paws ?
            # in a case that resources.paws exists and the provider running
            # is different then what described in resources.paws maybe the
            # providers should be responsible to preserve data and then append
            # new data into the file ? if resources.paws doesn't exist than
            # it is fine to just create and add new data to it?
            cleanup(inst.garbage_collector(), self.userdir)

            self.logger.debug('Executing %s.' % action)

            # call method
            return getattr(inst, action)()
