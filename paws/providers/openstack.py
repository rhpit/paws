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

import random
from copy import deepcopy
from time import sleep
from uuid import uuid4

import urllib3
from libcloud import security
from libcloud.common.types import InvalidCredsError
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from novaclient.client import Client as NovaClient
from os import getenv
from os.path import exists

from paws.constants import ADMIN, ADMINISTRADOR_PWD, ADMINISTRATOR, \
    OPENSTACK_ENV_VARS, PROVISION_RESOURCE_KEYS
from paws.core import LoggerMixin
from paws.exceptions import NovaPasswordError, SSHError, ProvisionError, \
    NotFound, BootError
from paws.helpers import retry, get_ssh_conn, file_mgmt
from paws.lib.remote import PlayCall
from paws.lib.windows import create_inventory, set_administrator_password, \
    ipconfig_release

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
        except InvalidCredsError:
            raise ProvisionError('Connection to OpenStack provider failed.')

    def get_image(self, name):
        """Get the LibCloud image object.

        :param name: image name or id
        """
        images = self.driver.list_images()

        by_name = filter(lambda elm: elm.name == name, images)
        by_id = filter(lambda elm: elm.id == name, images)

        if by_name.__len__() != 0:
            return by_name[0]
        elif by_id.__len__() != 0:
            return by_id[0]
        else:
            self.logger.error('Image %s does not exist.', name)
            raise SystemExit(1)

    def get_flavor(self, name):
        """Get the LibCloud size 'flavor' object.

        :param name: flavor name or id
        """
        sizes = self.driver.list_sizes()

        by_name = filter(lambda elm: elm.name == name, sizes)
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
            self.logger.error('Flavor %s does not exist.', name)
            raise SystemExit(1)

    def get_key_pair(self, name):
        """Get the LibCloud key pair object.

        :param name: key pair name
        """
        pairs = self.driver.list_key_pairs()

        data = filter(lambda elm: elm.name == name, pairs)

        if data.__len__() == 0:
            self.logger.error('Key pair %s does not exist.', name)
            raise SystemExit(1)
        else:
            return data[0]

    def get_float_ip_pool(self, name):
        """Get the LibCloud floating ip pool object.

        :param name: floating ip pool name
        """
        pool = self.driver.ex_list_floating_ip_pools()

        data = filter(lambda elm: elm.name == name, pool)

        if data.__len__() == 0:
            raise NotFound('Not found floating ip pool: %s.' % name)
        else:
            return data[0]

    def get_node(self, name):
        """Get the LibCloud node object.

        :param name: vm name
        """
        nodes = self.driver.list_nodes()

        data = filter(lambda elm: elm.name == name, nodes)

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
                        image=self.get_image(image),
                        size=self.get_flavor(flavor),
                        ex_keyname=key_pair
                    )
                else:
                    node = self.driver.create_node(
                        name=name,
                        image=self.get_image(image),
                        size=self.get_flavor(flavor),
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

    def wait_for_building_finish(self, node):
        """Wait for a vm to finish building.

        :param node: libcloud node object
        """
        self.logger.info('Wait for vm %s to finish building.', node.name)

        attempt = 1
        while attempt <= 30:
            node = self.driver.ex_get_node_details(node.id)
            state = getattr(node, 'state')
            msg = '%s. VM %s, STATE=%s' % (attempt, node.name, state)

            if state.lower() != 'running':
                self.logger.info('%s, rechecking in 20 seconds.', msg)
                sleep(20)
            else:
                self.logger.info(msg)
                self.logger.info('VM %s successfully finished building!',
                                 node.name)
                return node
            attempt += 1

        raise BootError('VM %s was unable to finish building.' % node.name)

    def attach_floating_ip(self, node, network):
        """Attach floating IP to vm.

        :param node: libcloud node object
        :param network: external network address
        """
        try:
            self.logger.info('Attach floating ip to vm %s.', node.name)
            pool = self.get_float_ip_pool(network)

            ip_obj = pool.create_floating_ip()

            self.logger.info('VM %s FIP %s.', node.name, ip_obj.ip_address)

            self.driver.ex_attach_floating_ip_to_node(node, ip_obj)
            self.logger.info('Successfully attached floating ip to vm %s',
                             node.name)
            return str(ip_obj.ip_address)
        except NotFound as ex:
            raise BootError(ex)

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

        data = filter(lambda elm: elm.name == name, networks)

        if data.__len__() == 0:
            raise NotFound('Not found network: %s.' % name)
        else:
            return data[0]


class Nova(LoggerMixin):
    """OpenStack nova component implementation."""

    def __init__(self, credentials):
        """Constructor.

        :param credentials: provider credentials
        """
        self.nova = NovaClient(
            '2',
            username=credentials['os_username'],
            password=credentials['os_password'],
            auth_url=credentials['os_auth_url'],
            project_name=credentials['os_project_name']
        )

    @retry(NovaPasswordError, tries=20)
    def get_password(self, name, key_pair):
        """Get the admin password for a server.

        :param name: server name
        :param key_pair: key pair associated to server
        """
        try:
            server = self.nova.servers.find(name=name)
            password = server.get_password(key_pair)

            if not password:
                raise NovaPasswordError('Password is empty!')
            if not isinstance(password, str):
                raise NovaPasswordError('Password %s is not string type!' %
                                        password)
            self.logger.debug('VM %s admin password %s', name, password)
        except NovaPasswordError as ex:
            raise NovaPasswordError(ex.message)
        return password

    def get_admin_password(self, res):
        """Get the pre-defined password for the admin account.

        This is part of the Windows QCOW image build process. The password is
        random each time. Nova client is used to retrieve the password.

        :param res: vm resource
        """
        self.logger.info('Attempting to SSH into vm %s.', res['name'])
        try:
            get_ssh_conn(
                res['public_v4'],
                ADMIN,
                ssh_key=res['ssh_private_key']
            )
        except SSHError:
            self.logger.error('Unable to SSH into vm %s.', res['name'])
            raise SSHError(1)

        self.logger.info('Fetching vm %s admin account password.', res['name'])

        res['win_username'] = ADMIN
        res['win_password'] = None

        try:
            res['win_password'] = self.get_password(
                res['name'],
                res['ssh_private_key']
            )
            self.logger.info('Successfully retrieved VM %s admin password.',
                             res['name'])
        except NovaPasswordError:
            self.logger.error('Unable to fetch admin password for vm %s.',
                              res['name'])
            raise NovaPasswordError(1)
        return res


class OpenStack(LibCloud, Nova):
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

        LibCloud.__init__(self, self.credentials)
        Nova.__init__(self, self.credentials)

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
                    self.logger.error('%s credential %s is undeclared.',
                                      self.name, key)
                    raise SystemExit(1)
                elif value[key] == '' or value[key] is None:
                    self.logger.error('%s credential %s not set properly.',
                                      self.name, key)
                    raise SystemExit(1)
                auth[key] = value[key]
        else:
            self.logger.debug('%s credentials are set by env vars.', self.name)

            for key in OPENSTACK_ENV_VARS:
                if key.lower() == 'os_project_name':
                    auth[key.lower()] = getenv(key)
                    if auth[key.lower()] is None:
                        auth[key.lower()] = getenv('OS_TENANT_NAME')
                        if auth[key.lower()] is None:
                            self.logger.error(
                                'Neither [os_project_name, os_tenant_name] env'
                                ' vars is not found.'
                            )
                            raise SystemExit(1)
                else:
                    auth[key.lower()] = getenv(key)
                    if auth[key.lower()] is None:
                        self.logger.error(
                            'Env variable: %s is not found.', key
                        )
                        raise SystemExit(1)
        self._credentials = auth

    @staticmethod
    def garbage_collector():
        """Garbage collector."""
        return []

    def provision(self):
        """Provision OpenStack resources."""
        for res in self.resources:
            try:
                self.get_node(res['name'])
                raise ProvisionError(
                    'Resource %s already exists in %s. Provision '
                    'skipped.' % (res['name'], self.name)
                )
            except NotFound:
                pass

            # lets handle the networking details here..
            ext_network = res['network']
            int_network = None
            if 'network' in res and 'floating_ip_pools' in res:
                # network=internal
                # floating_ip_pools=external
                int_network = self.get_network(res['network'])
                ext_network = res['floating_ip_pools']

            # boot vm
            node = self.boot_vm(
                res['name'],
                res['image'],
                res['flavor'],
                res['keypair'],
                network=int_network
            )

            # wait for vm to finish building
            self.wait_for_building_finish(node)

            # create/attach floating ip
            res['public_v4'] = self.attach_floating_ip(
                node,
                ext_network
            )

            # get the admin password
            self.get_admin_password(res)

        # create inventory file
        resources_paws = dict(resources=self.resources)
        create_inventory(
            PlayCall(self.user_dir).inventory_file,
            resources_paws
        )

        # set administrator password
        self.resources = set_administrator_password(
            self.resources,
            self.user_dir
        )

        # create resources.paws
        resources_paws = dict(resources=self.resources)
        file_mgmt('w', self.resources_paws_file, resources_paws)

        return resources_paws

    def teardown(self):
        """Teardown OpenStack resources."""
        for res in self.resources:
            self.logger.info('Deleting vm %s.', res['name'])

            # get the vm object
            try:
                node = self.get_node(res['name'])
            except NotFound as ex:
                self.logger.warning(ex.message)
                continue

            # create snapshot
            res['public_v4'] = self.get_floating_ip(node)
            self.take_snapshot(res)

            # detach the floating ip from vm
            fip = self.get_floating_ip(node)

            fip_obj = self.driver.ex_get_floating_ip(fip)
            self.driver.ex_detach_floating_ip_from_node(node, fip_obj)
            self.driver.ex_delete_floating_ip(fip_obj)

            # delete the vm
            self.driver.destroy_node(node)

            self.logger.info('Successfully deleted vm %s!', res['name'])

        resources_paws = dict(resources=self.resources)
        return resources_paws

    def show(self):
        """Show OpenStack resources."""
        for res in self.resources:
            # get the vm object
            node = self.get_node(res['name'])

            # get the ip
            res['public_v4'] = str(self.get_floating_ip(node))

            # define the account
            if ADMINISTRADOR_PWD in res:
                res['win_username'] = ADMINISTRATOR
                res['win_password'] = res[ADMINISTRADOR_PWD]
            else:
                self.get_admin_password(res)

        # create resources.paws
        resources_paws = dict(resources=self.resources)
        file_mgmt('w', self.resources_paws_file, resources_paws)

        return resources_paws

    def resource_check(self, res):
        """Check that the req. resource keys exist.

        :param res: windows resource
        """
        self.logger.info('Checking resource: %s keys.', res['name'])
        for key in PROVISION_RESOURCE_KEYS:
            if key not in res:
                raise ProvisionError(
                    'Resource: %s is missing required key: %s.' %
                    (res['name'], self.name)
                )
            elif res[key] == '' or res[key] is None:
                raise ProvisionError(
                    'Resource: %s required key: %s has an invalid value.' %
                    (res['name'], key)
                )
            if key == 'ssh_private_key':
                if not exists(res[key]):
                    raise ProvisionError(
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
            max_attempts = 30
            while attempt <= max_attempts:
                image = self.driver.get_image(image_id)
                if image.extra['status'].lower() == 'active':
                    self.logger.info('Image: %s, id: %s upload complete!',
                                     image.name, image.id)
                    break
                else:
                    self.logger.info('%s:%s. Image: %s, id: %s status: %s. '
                                     'Rechecking in 20 seconds.', attempt,
                                     max_attempts, image.name, image.id,
                                     image.extra['status'])
                    sleep(20)
                    attempt += 1
                if attempt == max_attempts:
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
