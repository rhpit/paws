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

"""
Utility package contains common classes, functons, etc to be used throughout
paws.
"""

from json import load as json_load
from json import dump as json_dump
from logging import getLogger
from os import getenv, remove, listdir
from os.path import join, exists, splitext
from socket import error, timeout
from subprocess import Popen, PIPE
from time import sleep, time
from yaml import dump as yaml_dump
from yaml import load as yaml_load

from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import SSHException

from paws.constants import SSH_IGNORE_ERROR, TASK_ARGS, LINE
from paws.exceptions import SSHError
from paws.util.decorators import retry

LOG = getLogger(__name__)


class TimeMixin(object):
    """A time mixin class.

    This class will save a start and end time to calculate the time delta
    between the two points.
    """

    start_time = None
    end_time = None
    hours = 0
    minutes = 0
    seconds = 0

    def start(self):
        """Save the start time."""
        self.start_time = time()

    def end(self):
        """Save the end time."""
        self.end_time = time()

        # calculate time delta
        delta = self.end_time - self.start_time
        self.hours = delta // 3600
        delta = delta - 3600 * self.hours
        self.minutes = delta // 60
        self.seconds = delta - 60 * self.minutes


class Namespace(object):
    """
    A class which will create a Python namespace object."""

    def __init__(self, kwargs):
        """Constructor."""
        self.__dict__.update(kwargs)


def subprocess_call(cmd, fatal=True, cwd=None, stdout=None, stderr=None,
                    env=None):
    """Run a shell command subprocess call using Popen.

    :param cmd: Command to run
    :type cmd: str
    :param fatal: Whether to raise exception with failure
    :type fatal: bool
    :param cwd: Directory path to switch to before running command
    :type cwd: str
    :param stdout: Pass subprocess PIPE if you want to pipe output
        from console
    :type stdout: int
    :param stderr: Pass subprocess PIPE if you want to pipe output
        from console
    :type stderr: int
    :return: The results from subprocess call
    :rtype: dict
    """
    results = {}
    proc = Popen(cmd, shell=True, stdout=stdout, stderr=stderr, cwd=cwd,
                 env=env)
    output = proc.communicate()
    if proc.returncode != 0:
        LOG.debug(output)
        msg = "Failed %s" % cmd
        if fatal:
            raise Exception(msg)
        else:
            LOG.error(msg)

    results['rc'] = proc.returncode
    results['stdout'] = output[0]
    results['stderr'] = output[1]

    return results


def get_conn_param(data):
    """ Get IP and Credentials """
    ipaddr, username, password = (None,) * 3
    for elem in data['resources']:
        # Get credentials
        # Administrator account
        if "ssh_user" and "ssh_password" in elem:
            username = elem['ssh_user']
            password = elem['ssh_password']
        else:
            # Admin account
            username = elem['user']
            password = elem['password']
        # Get public IP
        if "ip" in elem:
            ipaddr = elem['ip']
    return ipaddr, username, password


@retry(SSHError, tries=60)
def get_ssh_conn(ipaddr, username, password=None, ssh_key=None):
    """ Connect to remote machine through SSH Port 22 """
    try:
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        if ssh_key:
            ssh.connect(hostname=ipaddr,
                        username=username,
                        key_filename=ssh_key,
                        timeout=5)
        if password:
            ssh.connect(hostname=ipaddr,
                        username=username,
                        password=password,
                        timeout=5)
        ssh.close()
        LOG.info("Successfully established SSH connection to %s", ipaddr)
    except timeout as ex:
        raise SSHError(ex.message)
    except SSHException as ex:
        raise SSHError(ex.message)
    except error as ex:
        raise SSHError(ex.strerror)


@retry(SSHError, tries=60)
def exec_cmd_by_ssh(ipaddr, username, cmd, password=None, ssh_key=None):
    """ Connect to remote machine through SSH Port 22 and execute a command"""
    try:
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        if ssh_key:
            ssh.connect(hostname=ipaddr,
                        username=username,
                        key_filename=ssh_key,
                        timeout=30)
        if password:
            ssh.connect(hostname=ipaddr,
                        username=username,
                        password=password,
                        timeout=30)

        ssh.exec_command(cmd)

        ssh.close()
        LOG.info("Successfully executed command: %s", cmd)
    except timeout as ex:
        raise SSHError(ex.message)
    except SSHException as ex:
        raise SSHError(ex.message)
    except error as ex:
        raise SSHError(ex.strerror)


def cleanup(purge_list, userdir=None):
    """
    Delete remaining files from previous execution
    """
    for to_delete in purge_list:
        if exists(to_delete):
            remove(to_delete)
            LOG.debug("File %s deleted.", to_delete)
    # for now we want to delete .retry ansible files
    if userdir:
        lfiles = listdir(userdir)
        for to_delete in lfiles:
            if ".retry" in to_delete:
                remove(join(userdir, to_delete))
                LOG.debug("File %s deleted.", to_delete)


def file_mgmt(operation, file_path, content=None, cfg_parser=None):
    """A generic function to manage files (read/write).

    :param operation: File operation type to perform
    :type operation: str
    :param file_path: File name including path
    :type file_path: str
    :param content: Data to write to a file
    :type content: object
    :param cfg_parser: Config parser object (Only needed if the file being
        processed is a configuration file parser language)
    :type cfg_parser: bool
    :return: Data that was read from a file
    :rtype: object
    """

    # Determine file extension
    file_ext = splitext(file_path)[-1]

    if operation in ['r', 'read']:
        # Read
        if exists(file_path):
            if file_ext == ".json":
                # json
                with open(file_path) as f_raw:
                    return json_load(f_raw)
            elif file_ext in ['.yaml', '.yml', '.paws']:
                # yaml
                with open(file_path) as f_raw:
                    return yaml_load(f_raw)
            else:
                # text
                with open(file_path) as f_raw:
                    if cfg_parser is not None:
                        # Config parser file
                        return cfg_parser.readfp(f_raw)
                    else:
                        return f_raw.read()
        else:
            raise IOError("%s file not found!" % file_path)
    elif operation in ['w', 'write']:
        # Write
        mode = 'w+' if exists(file_path) else 'w'
        if file_ext == ".json":
            # json
            with open(file_path, mode) as f_raw:
                json_dump(content, f_raw, indent=4, sort_keys=True)
        elif file_ext in ['.yaml', '.yml', '.paws']:
            # yaml
            with open(file_path, mode) as f_raw:
                yaml_dump(content, f_raw, default_flow_style=False)
        else:
            # text
            with open(file_path, mode) as f_raw:
                if cfg_parser is not None:
                    # Config parser file
                    cfg_parser.write(f_raw)
                else:
                    f_raw.write(content)
    else:
        raise Exception("Unknown file operation: %s." % operation)


def update_resources_paws(resources_paws_path, resources_paws_content):
    """
    re-write resource.paws with content of object passed as parameter.
    basically the content of object will override the existing file
    resources.paws at userdir
    """
    file_mgmt('w', resources_paws_path, resources_paws_content)
    LOG.debug("Successfully updated %s", resources_paws_path)


def log_resources(resources_paws_path, action):
    """Log paws resources to console."""
    # case when resources.paws was not created maybe because nothing was
    # provisioned.
    if not exists(resources_paws_path):
        if 'deleted' in action:
            return True
        LOG.info(LINE)
        msg = "Nothing to show, did you try provision?"
        LOG.info(msg)
        LOG.info(LINE)
        return True

    fcontent = file_mgmt('r', resources_paws_path)

    msg = "System Resources (%s)" % action
    LOG.info(LINE)
    LOG.info(msg.center(45))
    LOG.info(LINE)

    for index, resource in enumerate(fcontent['resources']):
        index += 1
        LOG.info("%s.", index)
        LOG.info("    Name         : %s", resource['name'])
        LOG.info("    Provider     : %s", resource['provider'])
        if 'public_v4' in resource and resource['public_v4'] != "":
            LOG.info("    Public IPv4  : %s", resource['public_v4'])
        if 'ip' in resource and resource['ip'] != "":
            LOG.info("    Ip           : %s", resource['ip'])
        if action != "deleted":
            LOG.info("    Username     : %s", resource['win_username'])
            LOG.info("    Password     : %s", resource['win_password'])
        if "show" in action and 'libvirt' in resource['provider']:
            LOG.info("    Id           : %s", resource['id'])
            LOG.info("    UUID         : %s", resource['uuid'])
            LOG.info("    OS Type      : %s", resource['os_type'])
            LOG.info("    State        : %s", resource['state'])
            LOG.info("    Max Memory   : %s", resource['max_memory'])
            LOG.info("    Used Memory  : %s", resource['used_memory'])
            LOG.info("    VCPU(s)      : %s", resource['vcpu'])
            LOG.info("    Persistent   : %s", resource['persistent'])
            LOG.info("    Autostart    : %s", resource['autostart'])
            LOG.info("    Disk Source  : %s", resource['disk_source'])

    LOG.info(LINE)


def check_file(file_path, error_msg=None):
    """Generic function to check file exist in disk

    :param file_path: absolute path for file
    :type operation: str
    :param error_msg: custom error message to print
    :type error_msg: str
    """
    if not exists(file_path):
        if error_msg:
            raise IOError("%s file not found! %s" % (file_path, error_msg))
        else:
            raise IOError("%s file not found!" % file_path)
