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

from logging import getLogger
from os import getenv
from os.path import join, exists
from re import search, IGNORECASE
from time import sleep
from uuid import uuid4

from novaclient.client import Client as nclient
from novaclient.exceptions import ClientException, NotFound
from glanceclient.v2.client import Client as gclient
from keystoneclient.v2_0.client import Client as kclient

from paws.constants import ADMIN, GET_OPS_FACTS_YAML, ADMINISTRADOR_PWD, LINE
from paws.constants import OPENSTACK_ENV_VARS, PROVISION_RESOURCE_KEYS
from paws.constants import PROVISION_YAML, TEARDOWN_YAML, ADMINISTRATOR
from paws.exceptions import NovaPasswordError, SSHError
from paws.util import cleanup, file_mgmt, get_ssh_conn, update_resources_paws
from paws.util.decorators import retry
from paws.remote.prep import WinPrep
from paws.remote.results import CloudModuleResults
from paws.remote.driver import Ansible

"""
Openstack provider module
"""

LOG = getLogger(__name__)


class Openstack(object):
    """ Openstack Provider """

    def __init__(self, args):
        self.provider_name = 'openstack'
        self.args = args.args
        self.resources_paws = args.resources_paws
        self.util = Util(self)
        self.credential_file = args.credential_file
        self.conductor = Conductor()
        self.ansible = Ansible(args.userdir)
        self.credential = None
        self.res_paws = None
        self.res = None

    def garbage_collector(self):
        """Garbage collector method. it knows which files to collect for this
        provider and when asked/invoked it return all files to be deletec
        in a list

        :return garbage: all files to be deleted from this provider
        :rtypr garbage: list
        """
        garbage = [self.ansible.ansible_inventory,
                   join(self.args.userdir, TEARDOWN_YAML),
                   join(self.args.userdir, PROVISION_YAML),
                   join(self.args.userdir, GET_OPS_FACTS_YAML)]

        return garbage

    def clean_files(self):
        """Clean files genereated by paws for Openstack provider. It will only
        clean generated files when in non verbose mode.
        """
        if not self.args.verbose:
            cleanup(self.garbage_collector())

    def provision(self, res):
        """ Provision system resource(s) in Openstack provider

        :param res: content of resources file. For Openstack it is expected
        to have the content of resources.yaml but the parameter might have
        both files
        :type res: list of dict
        """
        # set resources
        self.res = res['res']

        # Check/get Openstack credentials
        self.credential = self.get_credential(self.credential_file)

        # Create empty inventory file for localhost calls
        self.ansible.create_hostfile()

        # Resources key check
        self.conductor.resource_keys_exist(PROVISION_RESOURCE_KEYS, self.res)

        # Resources openstack key check
        self.conductor.valid_openstack_keys(self.res, self.credential)

        # Create playbook to provision resources
        provision_playbook = ProvisionYAML(self).create()

        # Playbook call - provision resources
        self.ansible.run_playbook(
            provision_playbook,
            extra_vars=self.credential,
            results_class=CloudModuleResults
        )

        # TODO: generate_resources_paws move out from Openstack module
        # Create resources.paws
        res = self.util.generate_resources_paws(self.ansible, self.res,
                                                self.resources_paws)

        if res['resources'].__len__() > 0:
            for elem in res['resources']:
                # Get the default admin username and password
                elem = self.util.get_admin_password(elem)

            # Update resources paws file with admin username and password
            update_resources_paws(self.resources_paws, res)

            # Create updated inventory file
            self.ansible.create_hostfile(tp_obj=res)

        # Set Administrator account password
        win_prep = WinPrep(self.ansible, self.resources_paws)
        win_prep.set_administrator_password()

        # Load updated resources.paws into memory
        res = file_mgmt('r', self.resources_paws)

        # Create snapshot
        self.snapshots(res, task="provision")

        self.clean_files()

    def teardown(self, res):
        """ Teardown system resource(s) in Openstack provider

        :param res: content of resources file. For Openstack it is expected
        to have the content of resources.yaml but the parameter might have
        both files
        :type res: list of dict
        """
        # set resources (yaml and paws)
        self.res = res['res']
        self.res_paws = res['res_paws']

        # Create empty inventory file for localhost calls
        self.ansible.create_hostfile()

        # Check/get Openstack credentials
        self.credential = self.get_credential(self.credential_file)

        # Get instances facts from provider
        GetServerFacts(self).get_facts()

        # Create or update/override resources.paws
        self.res_paws = self.util.generate_resources_paws(
            self.ansible, self.res,
            self.resources_paws)

        # Update username/password
        for elem in self.res_paws['resources']:
            if ADMINISTRADOR_PWD in elem:
                elem['win_username'] = ADMINISTRATOR
                elem['win_password'] = elem[ADMINISTRADOR_PWD]
            else:
                elem['win_username'] = 'undefined'
                elem['win_password'] = 'undefined'

        # Create playbook to teardown resources
        teardown_yaml = TeardownYAML(self).create()

        # Create updated inventory file
        self.ansible.create_hostfile(tp_obj=self.res_paws)

        # Create snapshot
        self.snapshots(self.res_paws, task="teardown")

        # Playbook call - teardown resources
        self.ansible.run_playbook(
            teardown_yaml,
            extra_vars=self.credential,
            results_class=CloudModuleResults
        )

        self.clean_files()

    def show(self, res):
        """ Show system resource(s) in Openstack provider

        :param res: content of resources file. For Openstack it is expected
        to have the content of resources.yaml but the parameter might have
        both files
        :type res: list of dict
        """
        # set resources
        self.res = res['res']

        # Create empty inventory file for localhost calls
        self.ansible.create_hostfile()

        # Check/get Openstack credentials
        self.credential = self.get_credential(self.credential_file)

        # Get instances facts from provider
        GetServerFacts(self).get_facts()

        # Create resources.paws
        res = self.util.generate_resources_paws(self.ansible, self.res,
                                                self.resources_paws)

        if res['resources'].__len__() > 0:
            for elem in res['resources']:
                # password is defined up-front in resources.yaml
                if ADMINISTRADOR_PWD in elem:
                    elem['win_username'] = ADMINISTRATOR
                    elem['win_password'] = elem[ADMINISTRADOR_PWD]
                else:
                    # password is not defined up-front in resources.yaml
                    # get default password and user ADMIN
                    elem = self.util.get_admin_password(elem)

            # Update resources paws file with administrator password
            update_resources_paws(self.resources_paws, res)

        self.clean_files()

    def get_credential(self, credential_file):
        """It is a wrapper for get_credentails function from Openstack Util
        class. The reason for this method is to facilitate the re-usability
        by others methods and the data transfer object transparency passed
        by self"""
        return self.util.get_credentials(credential_file)

    def snapshots(self, resources, task):
        """Handles creating and deleting snapshots of instances provisioned.

        UC1. Take snapshot after provision & clean old instance snapshots.
            resources:
              - name: Windows
                snapshot:
                  - task: provision

        UC2. Take snapshot after teardown & ! clean old instance snapshots.
            resources:
              - name: Windows
                snapshot:
                  - task: teardown
                    clean: False

        UC3. Do not take snapshot, just clean old instance snapshots.
            resources:
              - name: Windows
                snapshot:
                  - task: teardown
                    create: False

        UC4. Take snapshot after provision & before teardown. Also clean all
        old instance snapshots.
            resources:
              - name: Windows
                snapshot:
                  - task: provision
                  - task: teardown

        :param resources: A list of resources.
        :param task: Task name calling this method.
        """
        LOG.debug('START: Create snapshot of running server')
        for res in resources['resources']:
            if "snapshot" not in res:
                LOG.debug('Skipping creating snapshot, snapshot key undefined')
                continue

            # Snapshot feature requires administrator username/password
            if 'Administrator' not in res['win_username']:
                LOG.error('Administrator username/password is required to '
                          'create snapshots.')
                raise SystemExit(1)

            # Get snapshot details for specific paws task
            snapdata = {}
            for item in res['snapshot']:
                if task.lower() == item['task']:
                    snapdata = item
                    break
                else:
                    LOG.warn('Task: %s declared by user when to take snapshot'
                             ' does not match the actual paws task running!',
                             item['task'])
            if not snapdata:
                continue

            # Default will create snapshot (override by create=False)
            try:
                create = snapdata['create']
            except KeyError:
                create = True

            # Default will clean old snapshots (override by clean=False)
            try:
                clean = snapdata['clean']
            except KeyError:
                clean = True

            nova = Nova(self.credential)

            # Create snapshot
            snapshot_id = ""
            if create:
                snapshot = res['name'] + "_paws_%s" % str(uuid4())[:5]
                snapshot_id = nova.create_image(res, snapshot, self.ansible)

            # Clean old snapshots for instance
            if clean:
                glance = Glance(self.credential)
                paws_images = glance.get_images_by_paws()

                if paws_images.__len__() == 0:
                    LOG.debug("No prior snapshots exist to be deleted for %s "
                              % res['name'])
                    continue

                for image in paws_images:
                    if snapshot_id == image.id:
                        continue
                    if image.created_from == res['name']:
                        nova.delete_image(image_id=image.id)
        LOG.debug('END: Create snapshot of running server')


class Nova(object):
    """Class to group interactions with Openstack nova client or api.
    http://docs.openstack.org/developer/python-novaclient/
    """

    def __init__(self, user_credential):
        self.version = "2"
        self.user_cred = user_credential
        self.nova = nclient(
            self.version,
            username=self.user_cred['OS_USERNAME'],
            password=self.user_cred['OS_PASSWORD'],
            auth_url=self.user_cred['OS_AUTH_URL'],
            project_name=self.user_cred['OS_PROJECT_NAME']
        )

    @retry(NovaPasswordError, tries=20)
    def get_password(self, server_name, keypair):
        """Return the password for a server using the private key.

        :param server_name: Name of the server to check password
        :type server_name: str
        :param keypair: SSH private key
        :type keypair: str
        :return: Admin password
        :rtype: str
        """
        try:
            server = self.get_server(server_name)
            password = server.get_password(keypair)

            if not password:
                raise NovaPasswordError("Password is empty!")
            if not isinstance(password, str):
                raise NovaPasswordError("Password: %s is not a string type!" %
                                        password)
            LOG.debug("Admin password for %s is %s", server_name, password)
        except NovaPasswordError as ex:
            raise NovaPasswordError(ex.msg)

        return password

    def get_server(self, instance_name):
        """Get nova server and return all info"""
        try:
            return self.nova.servers.find(name=instance_name)
        except Exception:
            return None

    def delete_instance(self, instance_id):
        """Delete a server."""
        self.nova.servers.delete(instance_id)

    def image_exist(self, image):
        """Check to see if image exists in tenant.

        :param image: Image to use to create vm.
        """
        try:
            try:
                self.nova.images.find(name=image)
            except NotFound:
                self.nova.images.find(id=image)
        except NotFound:
            LOG.error("Image: %s does not exist!", image)
            raise ClientException(1)

    def flavor_exist(self, flavor):
        """Verify flavor exists in tenant.

        :param flavor: Size of vm to create.
        """
        try:
            self.nova.flavors.find(id=flavor)
        except ClientException:
            LOG.error("Flavor: %s size does not exist!", flavor)
            raise ClientException(1)

    def network_exist(self, network):
        """Verify network exists in tenant.

        :param network: Network to create vms on.
        """
        try:
            self.nova.networks.find(label=network)
        except ClientException:
            LOG.error("Network: %s does not exist!", network)
            raise ClientException(1)

    def keypair_exist(self, keypair):
        """Verify key pair exists in tenant.

        :param keypair: SSH keypair.
        """
        try:
            self.nova.keypairs.find(name=keypair)
        except ClientException:
            LOG.error("Keypair: %s does not exist!", keypair)
            raise ClientException(1)

    def start_server(self, server):
        """Start a server.

        :param server: Server name.
        """
        _status = "active"
        count = 0
        max_attempts, wait = (5,) * 2
        sflag = True

        # Start server
        novares = self.get_server(server)
        novares.start()

        # Verify server was started
        while count <= max_attempts:
            count += 1
            status = self.server_status(server)
            if status != _status:
                LOG.error("Attempt (%s:%s): Unable to start server: %s, "
                          "status=%s. Retrying in %s seconds.." %
                          (count, max_attempts, server, status, wait))
                sflag = False
                sleep(wait)
                continue
            else:
                LOG.debug("Successfully started server: %s" % server)
                sflag = True
                break

        if not sflag:
            raise SystemExit(1)

    def stop_server(self, server):
        """Stop a server.

        :param server: Server name.
        """
        _status = "shutoff"
        count = 0
        max_attempts, wait = (5,) * 2
        sflag = True

        # Stop server
        novares = self.get_server(server)
        novares.stop()

        # Verify server was stopped
        while count <= max_attempts:
            count += 1
            status = self.server_status(server)
            if status != _status:
                LOG.error("Attempt (%s:%s): Unable to stop server: %s, "
                          "status=%s. Retrying in %s seconds.." %
                          (count, max_attempts, server, status, wait))
                sflag = False
                sleep(wait)
                continue
            else:
                LOG.debug("Successfully stopped server: %s" % server)
                sflag = True
                break

        if not sflag:
            raise SystemExit(1)

    def server_status(self, server):
        """Return the status of a server.

        :param server: Server name.
        """
        return self.get_server(server).status.lower()

    def create_image(self, server, image_name, ansible):
        """Create an image (snapshot) based on an server.

        :param server: Server information.
        :param image_name: Name of the snapshot to create.
        :param ansible: Ansible driver object.
        :return: Image id
        """
        server_name = server['name']

        # Metadata to inject
        metadata = {
            "author": "paws",
            "created_from": server_name
        }

        # Rearm server and release IPv4 connections
        win_prep = WinPrep(ansible, None)
        # win_prep.rearm_server(server)
        win_prep.ipconfig_release(server)

        # Shutdown server
        self.stop_server(server_name)

        # Take cold snapshot
        novares = self.get_server(server_name)
        novares.create_image(image_name, metadata)

        # Get image id
        image_id = self.nova.images.find(name=image_name).id

        LOG.info("Server: %s, Image: %s, ID: %s created." %
                 (server_name, image_name, image_id))

        try:
            try:
                # Is image uploaded?
                self.is_image_uploaded(image_name, image_id)
            finally:
                # Start server
                self.start_server(server_name)
        except SystemExit:
            raise SystemExit(1)

        return image_id

    def delete_image(self, image_name=None, image_id=None):
        """Delete an image. Image name takes order over id.

        :param image_name: Name of the image.
        :param image_id: Id of the image.
        """
        if image_name is None and image_id is None:
            LOG.error("Neither a image name or id was given. Cannot proceed.")
            raise SystemExit(1)

        try:
            if image_name:
                novaimg = self.nova.images.find(name=image_name)
            elif image_id:
                novaimg = self.nova.images.find(id=image_id)
        except NotFound as ex:
            LOG.error(ex.message)
            raise SystemExit(1)

        # Delete image
        novaimg.delete()
        LOG.info("Image: %s, ID: %s, deleted." % (novaimg.name, novaimg.id))

    def is_image_uploaded(self, image_name, image_id):
        """Is the image uploaded. Image uploading takes a couple minutes.

        :param image_name: Image name.
        :param image_id: ID of image.
        """
        count = 0
        max_attempts = 25
        wait = 20

        LOG.info("Verifying the image was successfully uploaded.")

        while True:
            try:
                result = self.nova.images.find(name=image_name)
                status = result.status.lower()

                if status == "active":
                    LOG.info("Image: %s, ID: %s uploaded successfully!" %
                             (image_name, image_id))
                    break
                else:
                    LOG.debug("Attempt (%s of %s): Image: %s status=%s. "
                              "Sleeping %s seconds.." %
                              (count, max_attempts, image_name, status, wait))
                    sleep(wait)
                    count += 1
                    continue
            except AttributeError:
                LOG.error("Unable to proceed, status key is missing!")
                self.delete_image(image_name, image_id)
                raise SystemExit(1)

            if count == max_attempts:
                LOG.error("Image: %s, ID: %s failed to become active!")
                self.delete_image(image_name, image_id)
                raise SystemExit(1)


class Glance(object):
    """Class to group interactions with Openstack glance client or api.
    http://docs.openstack.org/developer/glance/
    """

    def __init__(self, user_credential):
        self.user_cred = user_credential
        self.images = []
        self.keystonecli = kclient(
            username=self.user_cred['OS_USERNAME'],
            password=self.user_cred['OS_PASSWORD'],
            tenant_name=self.user_cred['OS_PROJECT_NAME'],
            auth_url=self.user_cred['OS_AUTH_URL'])
        self.glance_ep = self.keystonecli.service_catalog.url_for(
            service_type='image')
        self.glance = gclient(self.glance_ep,
                              token=self.keystonecli.auth_token)

    def get_win_images(self):
        """Get all available Windows images."""
        try:
            if self.images:
                return 0

            public_images = self.glance.images.list(
                filter={'visibility': 'public'})
            owner_id = "bf4de4c330bb47d6937af31fd5c71a18"

            for image in public_images:
                if search('win', image.name, IGNORECASE) and\
                        image.owner != owner_id:
                    self.images.append(image.name)

            if len(self.images) == 0:
                raise Exception("can't find Windows image")

            LOG.info("Available Windows images")
            LOG.info("-" * 80)
            for counter, img in enumerate(self.images, start=1):
                LOG.info("%s. %s" % (counter, img))
            LOG.info("-" * 80)

            return self.images

        except Exception as ex:
            raise Exception(ex)

    def get_images(self):
        """Get all available images."""
        return self.glance.images.list()

    def get_images_by_paws(self):
        """Get all available images authored by paws."""
        paws_images = []
        images = self.get_images()

        for image in images:
            try:
                if getattr(image, "author") != "paws":
                    continue
            except AttributeError:
                continue
            paws_images.append(image)
        return paws_images


class Util(object):
    """
    Util methods for Openstack provider
    """

    def __init__(self, args):
        self.args = args

    @staticmethod
    def get_credentials(credential_file):
        """
        Check for Openstack credentials from file or user env variables
        credentials.json file is optional but if it exists at userdir
        PAWS uses this to authenticate with Openstack otherwise
        will check OS_ environment variables.
        Get Openstack credential values

        :return credential: contains url, username, password and project
        :type dict: class providers.openstack.Openstack
        """
        help_msg = "Please refer to documentation on how to set your "\
            "providers credentials."
        _creds_file = False
        _creds_env_vars = False
        _creds = {}
        _creds_file = True if exists(credential_file) else False

        LOG.debug("Getting Openstack credentials.")

        # Credentials exist in form of environment variables?
        for var in OPENSTACK_ENV_VARS:
            if getenv(var) is not None:
                _creds_env_vars = True

        # Exit if either credential type does not exist
        if _creds_env_vars is False and _creds_file is False:
            LOG.error("Unable to find credentials from either a credentials "
                      "file or environment variables.")
            LOG.error(help_msg)
            raise SystemExit(1)

        # Get credentials by file
        if _creds_file:
            LOG.info("Openstack providers credentials are set by a credentials"
                     " file.")
            cdata = file_mgmt('r', credential_file)

            pos = next(index for index, key in enumerate(cdata['credentials'])
                       if 'openstack' in key['provider'])

            try:
                # Verify credential keys are set correctly and not empty
                for key in OPENSTACK_ENV_VARS:
                    key = key.lower()
                    if key not in cdata['credentials'][pos]:
                        LOG.error("Required credentials key: %s is missing!" %
                                  key)
                        LOG.error(help_msg)
                        raise SystemExit(1)
                    elif cdata['credentials'][pos][key] == "":
                        LOG.error("Credentials key: %s is not set properly!" %
                                  key)
                        LOG.error(help_msg)
                        raise SystemExit(1)
                    _creds[key.upper()] = cdata['credentials'][pos][key]
                return _creds
            except KeyError:
                LOG.error("Unable to read credentials file properly.")
                LOG.error(help_msg)
                raise SystemExit(1)

        # Get credentials by environment variables
        if _creds_env_vars:
            LOG.info("Openstack providers credentials are set by environment"
                     " variables.")
            for var in OPENSTACK_ENV_VARS:
                _creds[var] = getenv(var)
                if _creds[var] is None:
                    LOG.error("Environment variable: %s does not exist!" % var)
                    LOG.error(help_msg)
                    raise SystemExit(1)
            return _creds

    @staticmethod
    def gen_res_list(servers, rlist):
        """Return a list of provisioned resources information."""
        for server in servers:
            sut = {}
            sut['id'] = server['id'].encode('utf8')
            sut['name'] = server['name'].encode('utf8')
            sut['element'] = server['metadata']['element'].encode('utf8')
            sut['public_v4'] = server['public_v4'].encode('utf8')
            sut['private_v4'] = server['private_v4'].encode('utf8')
            rlist.append(sut)
        return rlist

    @staticmethod
    def generate_resources_paws(ansible, resources, resources_paws):
        """
        Read Ansible callback resultset to get elements from vm provisioned.
        Complement the data from resources.yaml matching the vm provisioned to
        build resources.paws.

        content for resources.paws and [source where they come from]
            id [ansible]
            name [ansible]
            ip [ansible]
            keypair [resources.yaml]
            ssh_private_key [resources.yaml]
        """
        LOG.debug("Generating %s" % resources_paws)
        results = ansible.callback.contacted
        _rlist = []

        # Generate list of resources from Ansible openstack server facts
        for item in results:
            if 'ansible_facts' in item['results']:
                # count == 1
                child = item['results']['ansible_facts']
                if 'openstack_servers' in child:
                    _rlist = Util.gen_res_list(
                        child['openstack_servers'], _rlist)
            elif 'results' in item['results']:
                # count > 1
                for server in item['results']['results']:
                    if 'ansible_facts' in server:
                        child = server['ansible_facts']
                        _rlist = Util.gen_res_list(
                            child['openstack_servers'], _rlist)

        # Resources are complemented with their data by matching metadata key
        # (element) which refers to resource elements inside topology file
        for elem in _rlist:
            for curr_elem in resources:
                if elem['element'] == curr_elem['name']:
                    elem['keypair'] = curr_elem['keypair']
                    try:
                        elem['ssh_key_file'] = curr_elem['ssh_private_key']
                    except KeyError:
                        elem['ssh_key_file'] = curr_elem['ssh_key_file']
                    elem['provider'] = curr_elem['provider']
                    if ADMINISTRADOR_PWD in curr_elem:
                        elem[ADMINISTRADOR_PWD] = \
                            curr_elem[ADMINISTRADOR_PWD]
                    if 'snapshot' in curr_elem:
                        elem['snapshot'] = curr_elem['snapshot']
                    del elem['element']
                    break

        # Write resources.paws
        if _rlist.len() > 0:
            file_mgmt('w', resources_paws, {"resources": _rlist})
            LOG.debug("Successfully created %s", resources_paws)

        return {"resources": _rlist}

    def get_admin_password(self, elem):
        """
        Get pre-defined password for Admin account, it is part of
        Windows QCOW image build process and password is random.
        Paws uses Nova client to retrieve the password
        """
        # Create nova object
        nova = Nova(self.args.credential)

        LOG.info("Attempting to establish SSH connection to %s",
                 elem['public_v4'])
        LOG.info(LINE)
        LOG.info("This could take several minutes to complete.")
        LOG.info(LINE)

        # Test system connectivity
        try:
            get_ssh_conn(
                elem['public_v4'],
                ADMIN,
                ssh_key=elem["ssh_key_file"]
            )
        except SSHError:
            LOG.error("Unable to establish SSH connection to %s",
                      elem['public_v4'])
            raise SSHError(1)

        try:
            LOG.info("Retrieving Admin password for %s:%s", elem['name'],
                     elem['public_v4'])
            elem["win_username"] = ADMIN
            elem["win_password"] = None

            # Retrieve admin password
            elem['win_password'] = str(nova.get_password(
                elem['name'],
                elem['ssh_key_file']
            ))

            LOG.info("Successfully retrieved Admin password for %s:%s",
                     elem['name'], elem['public_v4'])
        except NovaPasswordError:
            LOG.error("Unable to retrieve Admin password for %s:%s",
                      elem['name'], elem['public_v4'])
            raise NovaPasswordError(1)

        return elem


class ProvisionYAML(object):
    """
    Class which handles setting up the playbook data structure for
    provisioning resources.
    """

    def __init__(self, args):
        """Constructor."""
        self.provision = []
        self.resources = args.res
        self.playbook = join(args.args.userdir, PROVISION_YAML)

    def create(self):
        """Setup data structure and create the provision YAML.

        :param resources: Resources to provision
        :type resources: list
        """
        playbook = {}
        playbook['hosts'] = 'localhost'
        playbook['tasks'] = []

        for index, machine in enumerate(self.resources):
            index += 1

            # Setup task = os_server
            sut = {
                'name': 'Provision Resources',
                'os_server': {
                    'auth': {
                        'auth_url': '{{ OS_AUTH_URL }}',
                        'username': '{{ OS_USERNAME }}',
                        'password': '{{ OS_PASSWORD }}',
                        'project_name': '{{ OS_PROJECT_NAME }}'
                    },
                    'state': 'present',
                    'name': machine['name'].encode('utf8'),
                    'flavor': int(machine['flavor']),
                    'image': machine['image'].encode('utf8'),
                    'key_name': machine['keypair'].encode('utf8'),
                    'timeout': 900,
                    'wait': 'yes',
                    'meta': {
                        'hostname': machine['name'].encode('utf8'),
                        'element': machine['name'].encode('utf8'),
                        'provisioned': 'by PAWS'
                    }
                },
                'register': 'vm%s' % index
            }

            # floating_ip_pools is required when a public network has two
            # networks connected to it via routers.
            if 'floating_ip_pools' in machine:
                sut['os_server']['floating_ip_pools'] = \
                    machine['floating_ip_pools'].encode('utf8')
                sut['os_server']['network'] = machine['network'].encode('utf8')
            else:
                sut['os_server']['auto_ip'] = 'false'

            # Setup task = os_floating_ip
            sut_ip = {
                'name': 'Assign Floating IP',
                'os_floating_ip': {
                    'auth': {
                        'auth_url': '{{ OS_AUTH_URL }}',
                        'username': '{{ OS_USERNAME }}',
                        'password': '{{ OS_PASSWORD }}',
                        'project_name': '{{ OS_PROJECT_NAME }}'
                    },
                    'state': 'present',
                    'server': '{{ vm%s.openstack.name }}' % index,
                    'reuse': 'yes',
                    'network': machine['network'].encode('utf8'),
                    'wait': 'yes'
                },
                'when':
                'vm{0}|succeeded and vm{0}.openstack.public_v4 == ""'.format(
                    index)
            }

            # Setup task = os_server_facts
            sut_facts = {
                'name': 'retrieve server facts',
                'os_server_facts': {
                    'auth': {
                        'auth_url': '{{ OS_AUTH_URL }}',
                        'username': '{{ OS_USERNAME }}',
                        'password': '{{ OS_PASSWORD }}',
                        'project_name': '{{ OS_PROJECT_NAME }}'
                    },
                    'server': '{{ vm%s.openstack.name }}' % index,
                }
            }

            # Modify tasks keys when machine count > 1
            if int(machine['count']) > 1:
                # os_server module
                sut['os_server']['name'] = machine['name'].encode(
                    'utf8') + '_{{ item }}'
                sut['os_server']['meta']['hostname'] = machine['name'].encode(
                    'utf8') + '_{{ item }}'
                sut['with_sequence'] = 'count=' + str(machine['count'])

                # os_floating_ip
                sut_ip['os_floating_ip']['server'] = \
                    '{{ item.openstack.name }}'
                sut_ip['when'] = \
                    'item|succeeded and item.openstack.public_v4 == ""'
                sut_ip['with_items'] = '{{ vm%s.results }}' % index

                # os_server_facts
                sut_facts['os_server_facts']['server'] = \
                    '{{ item.openstack.name }}'
                sut_facts['with_items'] = '{{ vm%s.results }}' % index

            # Append tasks
            playbook['tasks'].append(sut)
            playbook['tasks'].append(sut_ip)
            playbook['tasks'].append(sut_facts)

        self.provision.append(playbook)

        # Write Ansible Playbook
        file_mgmt('w', self.playbook, self.provision)
        LOG.debug("Playbook %s created.", self.playbook)
        return self.playbook


class TeardownYAML(object):
    """
    Class which handles setting up the playbook data structure for
    tearing down resources.
    """

    def __init__(self, args):
        """Constructor."""
        self.teardown = []
        self.resources = args.res_paws
        self.playbook = join(args.args.userdir, TEARDOWN_YAML)

    def create(self):
        """Setup data structure and create the teardown YAML.

        :param resources: resources.paws after provisioned
        :type resources: list
        """
        playbook = {}
        playbook['hosts'] = 'localhost'
        playbook['tasks'] = []

        for machine in self.resources['resources']:
            # Setup task = os_floating_ip
            sut_ip = {
                'name': 'Un-assign Floating IP',
                'os_floating_ip': {
                    'auth': {
                        'auth_url': '{{ OS_AUTH_URL }}',
                        'username': '{{ OS_USERNAME }}',
                        'password': '{{ OS_PASSWORD }}',
                        'project_name': '{{ OS_PROJECT_NAME }}'
                    },
                    'state': 'absent',
                    'purge': 'yes',
                    'floating_ip_address': machine['public_v4'].encode('utf8'),
                    'server': machine['name'].encode('utf8')
                }
            }

            # Setup task = os_server
            sut = {
                'name': 'Teardown Resources',
                'os_server': {
                    'auth': {
                        'auth_url': '{{ OS_AUTH_URL }}',
                        'username': '{{ OS_USERNAME }}',
                        'password': '{{ OS_PASSWORD }}',
                        'project_name': '{{ OS_PROJECT_NAME }}'
                    },
                    'state': 'absent',
                    'name': machine['name'].encode('utf8'),
                    'key_name': machine['keypair'].encode('utf8'),
                    'timeout': 600,
                    'wait': 'yes'
                },
                'register': 'vm'
            }

            # Append tasks
            playbook['tasks'].append(sut_ip)
            playbook['tasks'].append(sut)

        self.teardown.append(playbook)

        # Write Ansible Playbook
        file_mgmt('w', self.playbook, self.teardown)
        LOG.debug("Playbook %s created.", self.playbook)
        return self.playbook


class GetServerFacts(object):
    """
    Class generate ansible playbook to retrieve servers ansible facts
    for openstack os_server and os_floating_ip modules
    Main usage when execution is interrupted by user like CTRL+C and
    this ansible playbook double check openstack resources provisioned
    before to run teardown
    """

    def __init__(self, args):
        """Constructor."""
        self.getfacts = []
        self.resources = args.res
        self.playbook = join(args.args.userdir, GET_OPS_FACTS_YAML)
        if args.ansible:
            self.ansible = args.ansible
        self.credential = args.credential

    def create(self):
        """Setup data structure and create the get_servers_facts YAML.

        :param resources: Resources to provision
        :type resources: list
        """
        playbook = {}
        playbook['hosts'] = 'localhost'
        playbook['tasks'] = []

        for index, machine in enumerate(self.resources):
            index += 1

            sut_facts = {
                'name': 'retrieve server facts',
                'os_server_facts': {
                    'auth': {
                        'auth_url': '{{ OS_AUTH_URL }}',
                        'username': '{{ OS_USERNAME }}',
                        'password': '{{ OS_PASSWORD }}',
                        'project_name': '{{ OS_PROJECT_NAME }}'
                    },
                    'server': machine['name'].encode('utf8'),
                }
            }

            # Modify tasks keys when machine count > 1
            if int(machine['count']) > 1:
                sut_facts['os_server_facts']['server'] = \
                    machine['name'].encode('utf8') + "_{{ item }}"
                sut_facts['with_sequence'] = 'count=' + str(machine['count'])

            # Append tasks
            playbook['tasks'].append(sut_facts)

        self.getfacts.append(playbook)

        # Write Ansible Playbook
        file_mgmt('w', self.playbook, self.getfacts)
        LOG.debug("Playbook %s created.", self.playbook)
        return self.playbook

    def get_facts(self):
        """Create Ansible playbook to get instance facts and execute against
        provider."""
        # Create playbook to get server facts
        getfacts_playbook = self.create()

        # Playbook call - get system facts
        self.ansible.run_playbook(
            getfacts_playbook,
            extra_vars=self.credential,
            results_class=CloudModuleResults
        )


class Conductor(object):
    """Conductor which acts like a 'train conductor'. This class will inspect
    files, keys, etc before starting paws tasks 'passengers'.
    """

    @staticmethod
    def valid_openstack_keys(resource, credentials):
        """Verify openstack keys values are valid.

        :param resource: content of topology file aka resources.yaml
        :param credentials: Providers credentials.
        """
        try:
            LOG.debug("Checking openstack keys are valid")

            # Create nova class instance
            nova = Nova(credentials)

            for res in resource:
                nova.image_exist(res['image'])
                nova.flavor_exist(str(res['flavor']))
                nova.network_exist(res['network'])
                nova.keypair_exist(res['keypair'])
        except ClientException as cex:
            LOG.error(cex)
            raise ClientException(1)
        except (IOError, Exception) as ex:
            LOG.error(ex)
            raise SystemExit(1)

    @staticmethod
    def ssh_private_key_exist(sshkey):
        """Verify private SSH key exists.

        :param sshkey: Private SSH key (absolute path).
        """
        if not exists(sshkey):
            LOG.error("Unable to find SSH private key: %s", sshkey)
            raise SystemExit(1)

    @staticmethod
    def resource_keys_exist(keys, resource):
        """Verify resource keys exist.

        :param keys: Keys to check.
        :param resource: content of topology file aka resources.yaml
        """
        help_msg = "Please refer to documentation on how to set your "\
            "topology file."
        LOG.debug("Checking resource sections for required keys")
        try:
            # Read resources file
            for res in resource:
                for key in keys:
                    if key not in res:
                        LOG.error("Required key: %s is missing!", key)
                        LOG.error(help_msg)
                        raise SystemExit(1)
                    elif res[key] == "":
                        LOG.error("Resource key: %s is not set properly!", key)
                        LOG.error(help_msg)
                        raise SystemExit(1)
                    if key == "ssh_private_key":
                        Conductor.ssh_private_key_exist(res[key])
        except IOError as ex:
            LOG.error(ex)
            raise SystemExit(1)
