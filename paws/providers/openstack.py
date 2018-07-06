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

from time import sleep
from uuid import uuid4

import random
import urllib3
from click_spinner import spinner
from copy import deepcopy
from libcloud import security
from libcloud.common.types import InvalidCredsError
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from os import getenv
from os.path import exists
from requests.exceptions import ConnectionError

from paws.constants import ADMINISTRADOR_PWD, ADMINISTRATOR, \
    OPENSTACK_ENV_VARS, PROVISION_RESOURCE_KEYS
from paws.core import LoggerMixin
from paws.exceptions import SSHError, ProvisionError, \
    NotFound, BootError, BuildError, NetworkError, TeardownError
from paws.helpers import file_mgmt
from paws.lib.remote import PlayCall
from paws.lib.remote import create_inventory
from paws.lib.windows import set_administrator_password, ipconfig_release

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAX_ATTEMPTS = 3
MAX_WAIT_TIME = 100


class LibCloud(LoggerMixin):
    """Apache LibCloud OpenStack provider implementation."""

    security.VERIFY_SSL_CERT = False

    def __init__(self, credentials):
        """Constructor.

        :param credentials: provider credentials
        """
        self.driver = get_driver(Provider.OPENSTACK)(
            credentials['os_username'],
            credentials['os_password'],
            ex_tenant_name=credentials['os_project_name'],
            ex_force_auth_url=credentials['os_auth_url'].split('/v')[0],
            ex_force_auth_version='2.0_password',
            ex_force_service_region=credentials.get('os_region', 'regionOne')
        )

        # verify connection
        try:
            self.driver.ex_list_networks()
        except (ConnectionError, InvalidCredsError):
            raise ProvisionError('Connection to OpenStack provider failed.')

    def get_image(self, name):
        """Get the LibCloud image object.

        :param name: image name or id
        """
        images = self.driver.list_images()

        by_name = list(filter(lambda elm: elm.name == name, images))
        by_id = list(filter(lambda elm: elm.id == name, images))

        if by_name.__len__() != 0:
            return by_name[0]
        elif by_id.__len__() != 0:
            return by_id[0]
        else:
            raise NotFound('Not found image: %s.' % name)

    def get_flavor(self, name):
        """Get the LibCloud size 'flavor' object.

        :param name: flavor name or id
        """
        sizes = self.driver.list_sizes()

        by_name = list(filter(lambda elm: elm.name == name, sizes))
        by_id = list()

        for size in sizes:
            try:
                if name == int(size.id):
                    by_id.append(size)
                    break
            except ValueError:
                # base 10
                continue

        if by_name.__len__() != 0:
            return by_name[0]
        elif by_id.__len__() != 0:
            return by_id[0]
        else:
            raise NotFound('Not found flavor: %s.' % name)

    def get_key_pair(self, name):
        """Get the LibCloud key pair object.

        :param name: key pair name
        """
        pairs = self.driver.list_key_pairs()

        data = list(filter(lambda elm: elm.name == name, pairs))

        if data.__len__() == 0:
            raise NotFound('Not found key pair: %s.' % name)
        else:
            return data[0]

    def get_float_ip_pool(self, name):
        """Get the LibCloud floating ip pool object.

        :param name: floating ip pool name
        """
        pool = self.driver.ex_list_floating_ip_pools()

        data = list(filter(lambda elm: elm.name == name, pool))

        if data.__len__() == 0:
            raise NotFound('Not found floating ip pool: %s.' % name)
        else:
            return data[0]

    def get_node(self, name):
        """Get the LibCloud node object.

        :param name: vm name
        """
        nodes = self.driver.list_nodes()

        data = list(filter(lambda elm: elm.name == name, nodes))

        if data.__len__() == 0:
            raise NotFound('Not found vm: %s.' % name)
        else:
            return data[0]

    def boot_vm(self, name, image, flavor, key_pair, network=None):
        """Boot a virtual machine.

        :param name: vm name
        :param image: image name
        :param flavor: flavor name
        :param key_pair: key pair name
        :param network: network name
        """
        attempt = 1

        while attempt <= MAX_ATTEMPTS:
            try:
                self.logger.info('Booting vm %s.', name)
                if network is None:
                    node = self.driver.create_node(
                        name=name,
                        image=image,
                        size=flavor,
                        ex_keyname=key_pair
                    )
                else:
                    node = self.driver.create_node(
                        name=name,
                        image=image,
                        size=flavor,
                        ex_keyname=key_pair,
                        networks=[network]
                    )
                self.logger.info('Successfully booted vm %s.', name)
                return node
            except KeyError as ex:
                self.logger.error(ex.message)
                delay = random.randint(10, MAX_WAIT_TIME)
                self.logger.info('%s:%s: retrying in %s seconds.',
                                 attempt, MAX_ATTEMPTS, delay)
                sleep(delay)
                attempt += 1
        raise BootError('Maximum attempts reached to boot vm %s.' % name)

    def wait_for_building_finish(self, node, res):
        """Wait for a vm to finish building.

        :param node: libcloud node object
        :param res: resource definition
        """
        self.logger.info('Wait for vm %s to finish building.', node.name)

        attempt = 1
        max_attempts = 30

        # check if resource requested to override the default max attempts
        if 'provision_attempts' in res:
            provision_attempts = int(res['provision_attempts'])
            if provision_attempts <= 0:
                self.logger.warning(
                    'Invalid amount for provision attempts: %s. Using default:'
                    ' %s.' % (provision_attempts, max_attempts))
            elif provision_attempts > 0:
                max_attempts = provision_attempts

        while attempt <= max_attempts:
            node = self.driver.ex_get_node_details(node.id)
            state = getattr(node, 'state')
            msg = '%s:%s. VM %s, STATE=%s' % (attempt, max_attempts,
                                              node.name, state)

            if state.lower() != 'running':
                self.logger.info('%s, rechecking in 20 seconds.', msg)
                with spinner():
                    sleep(20)
            else:
                self.logger.info(msg)
                self.logger.info('VM %s successfully finished building!',
                                 node.name)
                return node
            attempt += 1

        raise BuildError('VM %s was unable to finish building.' % node.name)

    def attach_floating_ip(self, node, network):
        """Attach floating IP to vm.

        :param node: libcloud node object
        :param network: external network address
        """
        try:
            self.logger.info('Attach floating ip to vm %s.', node.name)

            ip_obj = network.create_floating_ip()

            self.logger.info('VM %s FIP %s.', node.name, ip_obj.ip_address)

            self.driver.ex_attach_floating_ip_to_node(node, ip_obj)
            self.logger.info('Successfully attached floating ip to vm %s',
                             node.name)
            return str(ip_obj.ip_address)
        except Exception as ex:
            raise NetworkError(ex)

    @staticmethod
    def get_floating_ip(node):
        """Get the floating ip for a vm.

        :param node: libcloud node object
        """
        for key in node.extra['addresses']:
            for network in node.extra['addresses'][key]:
                if network['OS-EXT-IPS:type'] != 'floating':
                    continue
                return network['addr']

    def get_network(self, name):
        """Get the LibCloud network object.

        :param name: network name
        """
        networks = self.driver.ex_list_networks()

        data = list(filter(lambda elm: elm.name == name, networks))

        if data.__len__() == 0:
            raise NotFound('Not found network: %s.' % name)
        else:
            return data[0]


class OpenStack(LibCloud):
    """OpenStack provider class."""

    __provider_name__ = 'openstack'

    _credentials = dict()
    _resources = list()

    def __init__(self, args):
        """Constructor."""
        # set credentials
        self.credentials = args.credentials

        self.user_dir = args.userdir
        self.resources_paws_file = args.resources_paws_file
        self.verbose = args.verbose

        # set resources
        self.set_resources(args.resources)

        super(OpenStack, self).__init__(self.credentials)

    @property
    def name(self):
        """Return provider name."""
        return self.__provider_name__

    @property
    def resources(self):
        """Resources property.

        :return: windows resources
        """
        return self._resources

    @resources.setter
    def resources(self, value):
        """Set resources.

        :param value: windows resources
        """
        self._resources = value

    def set_resources(self, resources):
        """Handle setting resources when count > 1.

        :param resources: windows resources
        """
        # empty out resources
        self.resources = list()

        for res in resources:
            count = 1

            # first lets verify the resource has the req. keys
            self.resource_check(res)

            # count 1
            if res['count'] == 1:
                self._resources.append(res)
                continue

            if res['count'] > 1:
                for pos in range(count, res['count'] + 1):
                    res_copy = deepcopy(res)
                    res_copy['name'] = res_copy['name'] + '_%s' % pos
                    self._resources.append(res_copy)

    @property
    def credentials(self):
        """Credentials property.

        :return: provider credentials
        """
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        """Set the credentials property.

        This will set the credentials from either file or env vars.

        :param value: provider credentials
        """
        auth = dict()

        self.logger.debug('%s credentials check.', self.name)

        if value:
            self.logger.debug('%s credentials are set by file.', self.name)
            for key in OPENSTACK_ENV_VARS:
                key = key.lower()
                if key not in value:
                    raise NotFound('%s credential: %s is not set.' %
                                   (self.name, key))
                elif value[key] == '' or value[key] is None:
                    raise NotFound('%s credential: %s is not set '
                                   'properly.' % (self.name, key))
                auth[key] = value[key]
        else:
            self.logger.debug('%s credentials are set by env vars.', self.name)

            for key in OPENSTACK_ENV_VARS:
                if key.lower() == 'os_project_name':
                    auth[key.lower()] = getenv(key)
                    if auth[key.lower()] is None:
                        auth[key.lower()] = getenv('OS_TENANT_NAME')
                        if auth[key.lower()] is None:
                            raise NotFound(
                                'Neither [os_project_name|os_tenant_name] env'
                                ' vars is not set.'
                            )
                else:
                    auth[key.lower()] = getenv(key)
                    if auth[key.lower()] is None:
                        raise NotFound('Env variable: %s is not found.' % key)
        self._credentials = auth

    def garbage_collector(self):
        """Garbage collector."""
        return [self.resources_paws_file]

    def provision(self):
        """Provision OpenStack resources."""
        for res in self.resources:
            node = None

            try:
                self.get_node(res['name'])
                raise ProvisionError(
                    'Resource %s exits. Skipping provision!' % res['name']
                )
            except NotFound:
                self.logger.debug('Resource %s does not exist. Lets '
                                  'provision!', res['name'])

            # lets handle getting libcloud objects
            ext_net = res['network']
            int_net = None
            if 'network' in res and 'floating_ip_pools' in res:
                # more than one internal network
                # network=internal & floating_ip_pools=external
                try:
                    int_net = self.get_network(res['network'])
                    ext_net = self.get_float_ip_pool(res['floating_ip_pools'])
                except NotFound as ex:
                    raise ProvisionError(ex.message + ' for %s.' % res['name'])
            else:
                try:
                    ext_net = self.get_float_ip_pool(res['network'])
                except NotFound as ex:
                    raise ProvisionError(ex.message + ' for %s.' % res['name'])

            try:
                image = self.get_image(res['image'])
                flavor = self.get_flavor(res['flavor'])
                self.get_key_pair(res['keypair'])
            except NotFound as ex:
                raise ProvisionError(ex.message + ' for %s.' % res['name'])

            try:
                # boot vm
                node = self.boot_vm(res['name'], image, flavor, res['keypair'],
                                    network=int_net)

                # wait for vm to finish building
                self.wait_for_building_finish(node, res)

                # create/attach floating ip
                res['public_v4'] = self.attach_floating_ip(node, ext_net)
            except BootError as ex:
                raise ProvisionError(ex.message)
            except (BuildError, NetworkError, SSHError) as ex:
                self.logger.error(ex.message)
                self.logger.info('Tearing down vm: %s.', res['name'])
                self.driver.destroy_node(node)
                raise ProvisionError('Provision task failed.')

        # set administrator password
        self.resources = set_administrator_password(
            self.resources,
            self.user_dir
        )

        # create inventory file
        resources_paws = dict(resources=self.resources)
        create_inventory(
            PlayCall(self.user_dir).inventory_file,
            resources_paws
        )

        # create resources.paws
        resources_paws = dict(resources=deepcopy(self.resources))
        file_mgmt('w', self.resources_paws_file, resources_paws)

        return resources_paws

    def teardown(self):
        """Teardown OpenStack resources."""
        for index, res in enumerate(self.resources):
            self.logger.info('Deleting vm %s.', res['name'])

            try:
                node = self.get_node(res['name'])
            except NotFound as ex:
                self.logger.warning(ex.message + ' Skipping teardown.')
                self.resources.pop(index)
                continue

            try:
                # create snapshot
                res['public_v4'] = self.get_floating_ip(node)
                self.take_snapshot(res)

                # detach the floating ip from vm
                fip = self.get_floating_ip(node)

                if fip is not None:
                    fip_obj = self.driver.ex_get_floating_ip(fip)
                    self.driver.ex_detach_floating_ip_from_node(node, fip_obj)
                    self.driver.ex_delete_floating_ip(fip_obj)

                # delete the vm
                self.driver.destroy_node(node)

                self.logger.info('Successfully deleted vm %s!', res['name'])
            except Exception as ex:
                raise TeardownError(ex.message)

        resources_paws = dict(resources=deepcopy(self.resources))
        return resources_paws

    def show(self):
        """Show OpenStack resources."""
        resources = list()

        for index, res in enumerate(self.resources):
            try:
                node = self.get_node(res['name'])
            except NotFound as ex:
                self.logger.warning(ex.message)
                continue

            # get the ip
            res['public_v4'] = str(self.get_floating_ip(node))

            if ADMINISTRADOR_PWD in res:
                res['win_username'] = ADMINISTRATOR
                res['win_password'] = res[ADMINISTRADOR_PWD]
            resources.append(res)

        # create resources.paws
        resources_paws = dict(resources=deepcopy(resources))
        file_mgmt('w', self.resources_paws_file, resources_paws)

        return resources_paws

    def resource_check(self, res):
        """Check that the req. resource keys exist.

        :param res: windows resource
        """
        self.logger.info('Checking resource: %s keys.', res['name'])
        for key in PROVISION_RESOURCE_KEYS:
            if key not in res:
                raise NotFound(
                    'Resource: %s is missing required key: %s.' %
                    (res['name'], key)
                )
            elif res[key] == '' or res[key] is None:
                raise NotFound(
                    'Resource: %s required key: %s has an invalid value.' %
                    (res['name'], key)
                )
            if key == 'ssh_private_key':
                if not exists(res[key]):
                    raise NotFound(
                        'SSH private key: %s not found.' % res[key]
                    )

    def take_snapshot(self, res):
        """Take a snapshot before terminating a vm.

        Use cases:
            1. Take snapshot before delete vm and do not clean old snapshots
            resources:
              - name: windows
                snapshot:
                  create: True
                  clean: False

            2. Take snapshot before delete vm and clean old snapshots
            resources:
              - name: windows
                snapshot:
                  create: True
                  clean: True

            3. Do not take snapshot and only clean old snapshots
            resources:
              - name: windows
                snapshot:
                  create: False
                  clean: True

        :param res: windows resource
        """
        if 'snapshot' not in res:
            return

        self.logger.info('Taking snapshot for vm: %s.', res['name'])

        snap_details = res['snapshot']

        if ADMINISTRADOR_PWD not in res:
            self.logger.warning(
                'Administrator account is required to take snapshots. Take '
                'snapshot skipped.'
            )
            return

        if snap_details is None:
            self.logger.warning(
                'Snapshot key not set correctly. Please refer to docs.'
            )
            return

        # default settings for snapshot checking values
        attempts = 30
        delay = 20

        # user override default snapshot checking values
        if 'attempts' in snap_details:
            attempts = int(snap_details['attempts'])

        if 'delay' in snap_details:
            delay = int(snap_details['delay'])

        # create image
        image_id = ''
        if snap_details['create']:
            # release ip addresses
            res['win_username'] = ADMINISTRATOR
            res['win_password'] = res[ADMINISTRADOR_PWD]
            ipconfig_release(res)

            # take snapshot
            image_name = res['name'] + '_paws_%s' % (str(uuid4()))[:5]
            metadata = dict(author='paws', created_from=res['name'])
            node = self.get_node(res['name'])
            image_node = self.driver.create_image(
                node,
                image_name,
                metadata
            )
            image_id = image_node.id
            self.logger.info(
                'Snapshot: %s, id: %s successfully created!', image_name,
                image_id
            )

            # wait for image upload to complete
            attempt = 1
            while attempt <= attempts:
                image = self.driver.get_image(image_id)
                if image.extra['status'].lower() == 'active':
                    self.logger.info('Image: %s, id: %s upload complete!',
                                     image.name, image.id)
                    break
                else:
                    self.logger.info('%s:%s. Image: %s, id: %s status: %s. '
                                     'Rechecking in %s seconds.', attempt,
                                     attempts, image.name, image.id,
                                     image.extra['status'], delay)
                    sleep(delay)
                    attempt += 1
                if attempt == attempts:
                    self.logger.error('Image: %s, id: %s failed to become '
                                      'active!', image.name, image.id)
                    self.driver.ex_hard_reboot_node(node)
                    return

            # reboot vm to come back online
            sleep(25)
            self.driver.ex_hard_reboot_node(node)

        # clean previous images
        if snap_details['clean']:
            self.logger.info('Attempting to clean previous snapshot images '
                             'for vm: %s.', res['name'])
            _images = list()
            images = self.driver.list_images(ex_only_active=False)

            for image in images:
                try:
                    image.extra['metadata']['author']
                except KeyError:
                    continue
                if image.extra['metadata']['author'] == 'paws':
                    _images.append(image)

            if _images.__len__() == 0:
                self.logger.warn('No images to clean for vm: %s.', res['name'])
                return

            for image in _images:
                if snap_details['create']:
                    if image.id == image_id:
                        continue
                try:
                    image.extra['metadata']['created_from']
                except KeyError:
                    continue

                if image.extra['metadata']['created_from'] == res['name']:
                    self.driver.delete_image(self.driver.get_image(image.id))
                    self.logger.info('Image: %s, id: %s deleted.', image.name,
                                     image.id)
