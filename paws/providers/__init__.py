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

import importlib
from logging import getLogger
from os.path import exists
from paws.constants import PROVIDERS
from paws.util import file_mgmt

"""
Providers for PAWS
"""

LOG = getLogger(__name__)


class Provider(object):
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

    def __init__(self, args):
        self.topology_file = args.topology_file
        self.resources_paws = args.resources_paws
        self.credentials = args.credential_file
        self.provider_list = self.get_provider()
        self.args = args

    def is_valid(self):
        """ Verify if provider given is supported by PAWS

        :return result of validation
        :rtype Boolean
        """
        if self.provider_list not in PROVIDERS:
            return False

    def get_provider(self):
        """ Get provider from all elements declared in resources.yaml or
        topology file and return a list with non-duplicated elements

        :return list with providers extracted from topology file
        :rtype set
        """
        self.resources = file_mgmt('r', self.topology_file)
        provider_list = set()

        for resource in self.resources['resources']:
            provider_list.add(resource['provider'])

        return provider_list

    @staticmethod
    def get_resources_by_provider(res_file, provider):
        """Get system resources by provider name from a given file.
        Open the file and search for all system resources defined by
        the provider passed as parameter

        :param res_file: file usually resources.yaml or resources.paws
        :type res_file: str
        :param provider: name of registered provider supported by PAWS
        :type provider: str
        :return res: content from resources.yaml and .paws files
        :rtype res: list contains one or more lists of dicts
        """
        resource_list = []
        if exists(res_file):
            resources = file_mgmt('r', res_file)
            for elem in resources['resources']:
                if provider in elem['provider']:
                    resource_list.append(elem)

        return resource_list

    @staticmethod
    def get_creds_by_provider(creds_file, provider):
        """Get credentials by provider name from a given file.
        Open the file and search by provider passed as parameter

        :param creds_file: credentials.yaml
        :type creds_file: str
        :param provider: name of registered provider supported by PAWS
        :type provider: str
        :return res: content from credentials.yaml
        :rtype res: dict
        """
        if exists(creds_file):
            creds = file_mgmt('r', creds_file)
            for elem in creds['credentials']:
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

    def get_instance(self, provider_name):
        """Based on dynamic object creation technique this method uses
        python native importlib module to create objects based on
        parameters passed as string type

        :param provider_name: name of provider
        :type name: str
        :return instance: object of provider class
        :rtype instace: object
        """

        prov_info = self.get_provider_info_by_name(provider_name)
        my_module = importlib.import_module(prov_info['module'])
        klass = getattr(my_module, prov_info['class'])
        instance = klass(self.args)
        return instance

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
            # Read resources.yaml filtered by provider
            res = self.get_resources_by_provider(
                self.topology_file, provider_name)
            # Read resources.paws filtered by provider
            res_paws = self.get_resources_by_provider(
                self.resources_paws, provider_name)
            # Read credentials filtered by provider
            creds = self.get_creds_by_provider(self.credentials, provider_name)
            prov_files = {'res': res, 'res_paws': res_paws, 'creds': creds}

            # create an instance of provider name class
            inst = self.get_instance(provider_name)
            call_method = getattr(inst, action)
            call_method(prov_files)
