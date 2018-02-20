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

import sys
from logging import getLogger
from subprocess import PIPE
from xml.etree import ElementTree as ET

import libvirt
from click import style
from click.termui import progressbar
from libvirt import libvirtError
from os import environ, getenv
from os.path import join, exists
from requests import HTTPError, RequestException, get

from paws.compat import urlopen
from paws.constants import LIBVIRT_OUTPUT, LIBVIRT_AUTH_HELP, \
    ANSIBLE_INVENTORY_FILENAME
from paws.helpers import get_ssh_conn, file_mgmt, subprocess_call, cleanup, \
    retry
from paws.lib.remote import create_inventory, inventory_init

"""
    Libvirt provider, It is a wrapper interacting with Libvirt
    QEMU-KVM through API based on official documentation
    http://libvirt.org/html/libvirt-libvirt-domain.html

    _kvm was appended to the module name to avoid conflict with official
    libvirt-python module

    PAWS assumptions to use libvirt provider in your system:

    * libvirt is already installed
    * qemu driver is installed (ibvirt-daemon-driver-qemu)
    * libvirt service is running
    * libvirt authentication rule or policy is in place
    * windows*.qcow file exists at path specified in resources.yaml
    * windows*.xml file exists at path specified in resources.yaml

    @attention: Libvirt requires permissions to execute some API calls and
    to write new domains/vms. if you run PAWS with root or sudo than you can
    skip Libvirt authentication from notes below otherwise choose one of the
    2 alternatives and setup in your system where PAWS will be executed.

    @note: Alternative 1 (RECOMMENDED) - polkit rule

    Configure libvirt virt-manager without asking password. It is needed
    to paws be able to communicate with libvirt without need
    to run PAWS as sudo/root

    --create new polkit rule
        sudo vim /etc/polkit-1/rules.d/80-libvirt-manage.rules

        polkit.addRule(function(action, subject) {
          if (action.id == "org.libvirt.unix.manage"
          && subject.local && subject.active && subject.isInGroup("wheel")) {
            return polkit.Result.YES;
          }
        });

    --add your user to wheel group
        usermod -a -G wheel $USER

    source: https://goldmann.pl/blog/2012/12/03/\
    configuring-polkit-in-fedora-18-to-access-virt-manager/

    @note: Alternative 2 - Configuring libvirtd.conf

    Change the configuration in /etc/libvirt/libvirtd.conf as follows:

    1.In case it does not exist, create the group which should own the socket:
    $ sudo groupadd libvirt

    2. Add the desired users to the group:
    $ sudo usermod -a -G libvirt username
    or example using wheel group;
    $ sudo usermod -a -G wheel username

    3. Change the configuration in /etc/libvirt/libvirtd.conf as follows:
    unix_sock_group = "libvirt"    # or wheel if you prefer
    unix_sock_rw_perms = "0770"
    auth_unix_rw = "none"

    4. Restart libvirtd:
    $ sudo systemctl restart libvirtd

    5. set LIBVIRT_DEFAULT_URI variable. It is handled by PAWS so you can skip
    this step if you are interacting with libvirt by PAWS
    $ export LIBVIRT_DEFAULT_URI=qemu:///system

    6. testing, if there is any domain/vm in your system you should see after
    run the command below without sudo:
    $ virsh list --all
"""

LOG = getLogger(__name__)

# TODO: add variables back in constants
API_GET = ''
API_FIND = ''


class Libvirt(object):
    """ Libvirt PAWS main class"""

    __provider_name__ = 'libvirt'

    def __init__(self, args):
        self.args = args
        self.userdir = args.userdir
        self.resources = args.resources
        self.credentials = args.credentials
        self.resources_paws_file = args.resources_paws_file
        self.verbose = args.verbose

        self.util = Util(self)
        self.inventory = join(self.userdir, ANSIBLE_INVENTORY_FILENAME)

        self.resources_paws = None

        # Libvirt domain/VM states
        self.states = {
            libvirt.VIR_DOMAIN_NOSTATE: 'no state',
            libvirt.VIR_DOMAIN_RUNNING: 'running',
            libvirt.VIR_DOMAIN_BLOCKED: 'blocked on resource',
            libvirt.VIR_DOMAIN_PAUSED: 'paused by user',
            libvirt.VIR_DOMAIN_SHUTDOWN: 'being shut down',
            libvirt.VIR_DOMAIN_SHUTOFF: 'shut off',
            libvirt.VIR_DOMAIN_CRASHED: 'crashed',
        }

    @property
    def name(self):
        """Return provider name."""
        return self.__provider_name__

    def set_libvirt_env_var(self):
        """Set LIBVIRT_DEFAULT_URI system variable. It is required for some
        API calls"""
        if getenv('LIBVIRT_DEFAULT_URI', False) is False:
            environ['LIBVIRT_DEFAULT_URI'] = self.credentials['qemu_instance']

    def garbage_collector(self):
        """Garbage collector method. it knows which files to collect for this
        provider and when asked/invoked it return all files to be deletec
        in a list

        :return garbage: all files to be deleted from this provider
        :rtypr garbage: list
        """
        garbage = [self.inventory,
                   join(self.userdir, LIBVIRT_OUTPUT)]
        return garbage

    def clean_files(self):
        """Clean files genereated by paws for Openstack provider. It will only
        clean generated files when in non verbose mode.
        """
        if not self.verbose:
            cleanup(self.garbage_collector())

    def provision(self):
        """ Provision system resource(s) in Libvirt provider"""
        # -- basic flow --
        # assume qcow and xml files required already exist as declared in
        # resources.yaml file
        # check if files exists (windows*.qcow and windows*.xml)
        # check if VM name based on resources.yaml already exists
        # Start VM
        # show VM info (network, etc)

        self.set_libvirt_env_var()

        # Create empty inventory file for localhost calls
        inventory_init(self.inventory)

        # check libvirt connection - validating authentication
        conn = self.util.get_connection()

        for elem in self.resources:
            LOG.info('Working to provision %s VM on %s' % (elem['name'],
                                                           elem['provider']))
            # check for required files
            LOG.debug("Checking %s exist" % elem['disk_source'])
            if not exists(elem['disk_source']):
                LOG.error('File %s not found' % elem['disk_source'])
                LOG.warn('check PAWS documentation %s' %
                         LIBVIRT_AUTH_HELP)
                raise SystemExit(1)

            # check for VM and delete/undefine in case already exist
            if self.util.vm_exist(conn, elem['name']):
                vm = self.util.find_vm_by_name(conn, elem['name'])
                if vm:
                    self.util.stop_vm(vm)
                    self.util.delete_vm(conn, vm, flag=None)

            self.util.create_vm_virtinstall(elem)

            # get VM
            vm = self.util.find_vm_by_name(conn, elem['name'])

            try:
                # get vm info
                vm_info = self.util.get_vm_info(conn, elem)

                # loop to get SSH connection with auto-retry
                try:
                    get_ssh_conn(vm_info['ip'], elem['win_username'],
                                 elem['win_password'])
                except Exception as ex:
                    LOG.error(ex)
            except Exception:
                LOG.debug("An error happened during provision VM %s trying \
                forced teardown" % elem['name'])
                self.teardown()

            # @attention Libvirt provider doesn't need hosts inventory file but
            # it is required by Winsetup and Group.
            # preparing resource to be compatible with ansible create inventory
            elem['ip'] = vm_info['ip']  # append ip to resource
            res = {}
            list_resources = [elem]
            res['resources'] = list_resources
            create_inventory(self.inventory, res)

        self.util.generate_resources_paws(conn)

        return self.resources_paws

    def teardown(self):
        """ Provision system resource(s) in Openstack provider"""
        self.set_libvirt_env_var()

        conn = self.util.get_connection()
        for elem in self.resources:
            # get vm object and continue with teardown process (stop and del)
            if self.util.vm_exist(conn, elem['name']):
                vm = self.util.find_vm_by_name(conn, elem['name'])
                if vm:
                    self.util.stop_vm(vm)
                    self.util.delete_vm(conn, vm, flag=None)

        self.clean_files()

        return {'resources': self.resources}

    def show(self):
        """ Provision system resource(s) in Openstack provider"""
        self.set_libvirt_env_var()
        conn = self.util.get_connection()
        self.util.generate_resources_paws(conn)
        return self.resources_paws


class Util(object):
    """
    Util methods for Libvirt provider
    """

    def __init__(self, args):
        self.args = args

    def get_connection(self):
        """ Get connection with libvirt using QEMU driver and system
        context

        :return conn: connection with libvirt
        :rtype conn: libvirt connection
        """
        creds = self.args.credentials

        if 'username' in creds:
            auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_NOECHOPROMPT],
                    creds['username'], None]
            conn = libvirt.openAuth(creds['qemu_instance'], auth, 0)
        else:
            conn = libvirt.open(creds['qemu_instance'])

        if conn is None:
            LOG.error('Failed to open connection to %s',
                      creds['qemu_instance'])
            LOG.warn('check PAWS documentation %s' % LIBVIRT_AUTH_HELP)
            raise SystemExit(1)

        LOG.debug("connected successfully to %s" % creds['qemu_instance'])

        return conn

    @staticmethod
    def vm_exist(conn, vm_name):
        """ check if the domain exists, may or may not be active

        :param conn: Libvirt connection
        :type conn: object
        :param vm_name: name of vm or domain to check
        :type vm_name: str
        :return Boolean True|False
        """
        all_vms = conn.listAllDomains()
        for vm in all_vms:
            if vm_name == vm.name():
                return True
        return False

    @staticmethod
    def download(link, file_dst, label):
        """Create HTTP request to download a file"""
        # delimit labels to be at same size and a better visualization
        # when printing the progres bar
        fill_out = 20 - len(label)
        extra = " " * fill_out
        pbar_label = label + extra
        LOG.debug("Starting download %s" % link)
        try:
            req = urlopen(link)
            remote_file_size = int(req.headers.get('content-length'))
            CHUNK = 16 * 1024
            with open(file_dst, 'wb') as fp:
                with progressbar(length=remote_file_size,
                                 fill_char=style('#', fg='green'),
                                 empty_char=' ',
                                 label=pbar_label,
                                 show_percent=True) as bar:
                    while True:
                        chunk = req.read(CHUNK)
                        if not chunk:
                            break
                        fp.write(chunk)
                        bar.update(len(chunk))

            LOG.debug("Download complete, file %s saved locally" % file_dst)
        except (HTTPError, RequestException, Exception) as ex:
            raise ex

    def donwload_image(self, image_name, dst_path, imgsrv_url):
        """Download QCOW and XML files required by libvirt to import
        as local disc in qemu-kvm

        :param image_name: file name
        :type image_name: str
        :param dst_path:
        :type dst_path: str
        :param imgsrv_url:
        :type imgsrv_url: str
        :return qcow_path, xml_path
        :rtype qcow_path, xml_path
        """
        # Image service base url
        BASE_URL = imgsrv_url.strip('/')

        # find image in imagesrv
        URL_FIND = BASE_URL + API_FIND + image_name
        try:
            resp = get(URL_FIND)
            if 'error' in resp.json():
                raise Exception(resp.json()['error'],
                                resp.json()['url_received'])
        except (RequestException, Exception) as ex:
            LOG.error(ex)

        URL_XML = BASE_URL + API_GET + resp.json()['xml']
        URL_QCOW = BASE_URL + API_GET + resp.json()['qcow']
        DST_XML = dst_path + '/' + resp.json()['xml']
        DST_QCOW = dst_path + '/' + resp.json()['qcow']

        LOG.info('Download Windows libvirt files')
        self.download(URL_XML, DST_XML, resp.json()['xml'])
        self.download(URL_QCOW, DST_QCOW, resp.json()['qcow'])

        # TODO: improve the errors, it doesnt make sense now
        if not exists(DST_XML):
            LOG.error('file %s not found', DST_XML)
            sys.exit(1)

        # TODO: improve the errors, it doesnt make sense now
        if not exists(DST_QCOW):
            LOG.error('file %s not found', DST_QCOW)
            sys.exit(1)

        return DST_QCOW, DST_XML

    @staticmethod
    def update_vm_xml(xml_path, qcow_path, elem, userdir):
        """Read VM definition XML file and update content of some childreen
        with data from resources.yaml file

        :param image_name:
        :type str
        :param dst_path:
        :type str
        :param userdir:
        :type str
        :return qcow_path, xml_path
        :rtype str, str
        """
        LOG.debug("Parse VM XML descriptor %s" % xml_path)
        # load xml
        domain = ET.parse(xml_path)
        xml = domain.getroot()

        # parse elements from resources.yaml
        if xml.find('name') is not None:
            name = xml.find('name')
            name.text = str(elem['name'])

        if xml.find('memory') is not None:
            memory = xml.find('memory')
            memory.text = str(elem['memory'])

        if xml.find('vcpu') is not None:
            vcpu = xml.find('vcpu')
            vcpu.text = str(elem['vcpu'])

        if xml.find('devices') is not None:
            devices = xml.find('devices')
            disk = devices.find('disk')
            source = disk.find('source')
            source.attrib['file'] = qcow_path

        # save temporally vm definition file to be used for creation
        # user_dir + elem-name -- hidden file

        _xml = join(userdir, LIBVIRT_OUTPUT)
        domain.write(_xml)

        # Load xml object in memory
        fp = open(_xml, "r")
        _xml_obj = fp.read()
        fp.close()

        LOG.debug("Parse completed, file %s is ready" % xml_path)
        return _xml_obj

    @staticmethod
    def create_vm_virtinstall(vm, fatal=True):
        """ provision a new virtual machine to the host using virt-install
        cli

        :param vm
        :type obj

        command line:
        virt-install --connect qemu:///system
        --name myVM
        --ram 4000
        --vcpus=1
        --os-type=windows
        --disk path=/tmp/windows_2012.qcow,device=disk,bus=virtio,format=qcow2
        --vnc
        --noautoconsole
        --import

        """
        LOG.debug("Creating your vm %s" % vm['name'])
        cmd = ("virt-install"
               " --connect qemu:///system"
               " --name " + str(vm['name']) +
               " --ram " + str(vm['memory']) +
               " --vcpus " + str(vm['vcpu']) +
               " --os-type=windows"
               " --disk path=" + str(vm['disk_source']) +
               ",device=disk,bus=virtio,format=qcow2"
               " --vnc"
               " --noautoconsole"
               " --import"
               )

        LOG.debug(cmd)
        rs = subprocess_call(cmd, stdout=PIPE, stderr=PIPE)
        if rs == 0:
            LOG.error(rs['stderr'])
            raise SystemExit(1)

        LOG.info("%s provisioned" % vm['name'])

    @staticmethod
    def create_vm(conn, xml_path):
        """Define a new domain in Libvirt, creating new Virtual Machine

        :param conn: Libvirt connection
        :type conn: object
        :param xml_path: full path for XML with VM definition
        :type xml_path: str
        :return True
        :rtype Boolean
        """
        LOG.debug("VM creation, defining new domain in libvirt")
        try:
            conn.defineXMLFlags(xml_path)
            LOG.debug("VM creation, complete")
            return True
        except (SystemExit, libvirtError) as ex:
            LOG.error(ex)
            raise SystemExit(1)

    @staticmethod
    def find_vm_by_name(conn, vm_name):
        """Find VM or domain in Libvirt

        :param conn: Libvirt connection
        :type conn: object
        :param vm_name: name of virtual machine or domain
        :type vm_name: str
        :return vm: Virtual Machine
        :rtype vm: object
        """
        try:
            vm = conn.lookupByName(vm_name)
            LOG.debug("VM %s found" % vm_name)
        except Exception:
            vm = None
            LOG.debug("VM %s doesn't exist" % vm_name)
        return vm

    def is_running(self, vm):
        """Check if VM state is running

        :param vm: virtual machine
        :type vm: object
        :return True|False
        :rtype Boolean
        """
        vm_state = self.args.states.get(vm.info()[0], vm.info()[0])
        if 'running' in vm_state:
            return True
        else:
            return False

    def reboot_vm(self, vm):
        """Reboot virtual machine on libvirt

        :param vm: virtual machine
        :type vm: object
        """
        vm.reboot()

    @retry(Exception, tries=3, delay=5)
    def start_vm(self, vm):
        """Start virtual machine instance on Libvirt

        :param vm: virtual machine
        :type vm: object
        """
        if self.is_running(vm):
            LOG.debug("VM %s is running" % vm.name())
            return True

        try:
            vm.create()
            LOG.debug("Importing VM %s" % vm)
            # the raise exception is to force the vm state be checked again
            raise Exception
        except libvirt.libvirtError as ex:
            raise ex

    @retry(Exception, tries=3, delay=5)
    def stop_vm(self, vm):
        """Stop virtual machine instance on Libvirt

        :param vm: virtual machine
        :type vm: object
        """
        if not self.is_running(vm):
            return True

        try:
            vm.destroy()
            LOG.debug("VM %s stopped" % vm.name())
            raise Exception
        except libvirt.libvirtError as ex:
            raise ex

    @staticmethod
    def delete_vm(conn, vm, flag=None):
        """ """
        # TODO: PAWS-84 flag to delete VM during teardown
        try:
            vm.undefineFlags(1)
            LOG.debug("VM %s deleted" % vm.name())
            if flag:
                storage_pools = conn.listAllStoragePools()

                for pool in storage_pools:
                    stgvols = pool.listVolumes()
                    LOG.error(stgvols)

            return True
        except (libvirt.libvirtError, Exception) as ex:
            LOG.error(ex)

    @retry(Exception, tries=5, delay=30)
    def get_ipv4(self, vm):
        """Get IP V4 from Windows running as Virtual Machine in Libvirt
        QEMU-KVM provider.

        :param vm: virtual machine
        :type vm: domain object
        :return addr['addr']: IP address V4
        :rtype ipv4: str
        """
        try:
            ifaces = vm.interfaceAddresses(
                libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)

            if not ifaces:
                raise Exception("waiting for network interface")

            LOG.debug("{0:10} {1:20} {2:12} {3}".
                      format("Interface", "MAC address", "Protocol",
                             "Address"))

            def toIPAddrType(addrType):
                if addrType == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                    return "ipv4"
                elif addrType == libvirt.VIR_IP_ADDR_TYPE_IPV6:
                    return "ipv6"

            for (name, val) in ifaces.iteritems():
                if val['addrs']:
                    for addr in val['addrs']:
                        LOG.debug("{0:10} {1:19}".format(name, val['hwaddr'])),
                        LOG.debug("{0:12} {1}/{2} ".
                                  format(toIPAddrType(addr['type']),
                                         addr['addr'], addr['prefix'])),
                else:
                    LOG.debug("{0:10} {1:19}".format(name, val['hwaddr'])),
                    LOG.debug("{0:12} {1}".format("N/A", "N/A")),

        except Exception as ex:
            raise ex

        return addr['addr']

    def get_vm_info(self, conn, elem):
        """Get virtual machine info

        :param vm: virtual machine
        :type vm: object
        :return vm_info: relevant info to PAWS for a given virtual machine
        :rtype dict
        """
        LOG.info("Retrieving info from %s" % elem['name'])
        vm = self.find_vm_by_name(conn, elem['name'])

        # in case VM doesnt exist
        if not vm:
            return False

        vm_info = {}

        vm_info['id'] = vm.ID()
        vm_info['name'] = vm.name()
        vm_info['uuid'] = vm.UUIDString()
        vm_info['os_type'] = vm.OSType()
        vm_info['state'] = self.args.states.get(vm.info()[0], vm.info()[0])
        vm_info['max_memory'] = str(vm.info()[1])
        vm_info['used_memory'] = str(vm.info()[2])
        vm_info['vcpu'] = str(vm.info()[3])
        # Determine if the vm has a persistent configuration
        # which means it will still exist after shutting down
        vm_info['persistent'] = vm.isPersistent()
        vm_info['autostart'] = vm.autostart()

        if self.is_running(vm):
            ip = self.get_ipv4(vm)
        else:
            ip = None

        vm_info['ip'] = ip
        vm_info['win_username'] = elem['win_username']
        vm_info['win_password'] = elem['win_password']
        vm_info['provider'] = elem['provider']

        # read VM xml definition or descriptor
        xmldesc = vm.XMLDesc(0)
        xml = ET.fromstring(xmldesc)

        if xml.find('devices') is not None:
            devices = xml.find('devices')
            disk = devices.find('disk')
            source = disk.find('source')
            vm_info['disk_source'] = source.attrib['file']

        LOG.debug("Loaded VM Info for %s" % elem['name'])
        return vm_info

    def generate_resources_paws(self, conn):
        """Generate or Update resources.paws file.

        If resources.paws file exists function will not delete the file or
        even just append new data into this. First of all any element
        decldared into resources.paws from provider different than
        libvirt will be preserved and new data just appended to the file.

        :param conn: Libvirt connection
        :type conn: object
        """
        LOG.debug("Generating %s" % self.args.resources_paws_file)

        vms = []
        for res in self.args.resources:
            if self.vm_exist(conn, res['name']):
                vm_info = self.get_vm_info(conn, res)
                if vm_info:
                    vms.append(vm_info)

        # Write resources.paws
        if len(vms) > 0:
            if exists(self.args.resources_paws_file):
                res_paws = file_mgmt('r', self.args.resources_paws_file)

                for x in res_paws['resources']:
                    if x['provider'] != self.args.name:
                        vms.append(x)

            self.args.resources_paws = {'resources': vms}
            file_mgmt(
                'w',
                self.args.resources_paws_file,
                self.args.resources_paws
            )
            LOG.debug("Successfully created %s", self.args.resources_paws_file)
