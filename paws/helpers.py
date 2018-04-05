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
"""Helpers module."""

from functools import wraps
from json import dump as json_dump
from json import load as json_load
from logging import getLogger
from socket import error, timeout
from subprocess import Popen
from time import sleep

import warnings
from click_spinner import spinner
from os import remove, listdir
from os.path import join, exists, splitext
from paramiko import AutoAddPolicy, SSHClient
from paramiko.ssh_exception import SSHException
from yaml import dump as yaml_dump
from yaml import load as yaml_load

from paws.constants import LINE, PAWS_TASK_MODULES_PATH
from paws.exceptions import SSHError

LOG = getLogger(__name__)

__all__ = [
    'retry', 'cleanup', 'file_mgmt', 'update_resources_paws',
    'log_resources', 'check_file', 'get_ssh_conn', 'exec_cmd_by_ssh',
    'subprocess_call'
]


def retry(exception_to_check, tries=4, delay=10, backoff=1, logger=LOG):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param exception_to_check: the exception to check. may be a tuple of
        exceptions to check
    :type exception_to_check: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(function_name):

        @wraps(function_name)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return function_name(*args, **kwargs)
                except exception_to_check as ex:
                    try:
                        msg = "%s Retrying in %d seconds.." %\
                              (str(ex.message), mdelay)
                        # msg = "%s, retrying in %d seconds..." %\
                        #    (str(ex), mdelay)
                        if logger:
                            logger.debug(msg)
                        else:
                            print(msg)
                        sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
            return function_name(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def ignore_warnings(method):
    """Decorator to suppress warning messages.

    :param method: method to be called
    """
    @wraps(method)
    def ignore(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return method(*args, **kwargs)
    return ignore


def cleanup(purge_list, userdir=None):
    """Delete files.

    :param purge_list: Files to be deleted
    :type purge_list: list
    :param userdir: User directory
    :type userdir: str
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
    :type cfg_parser: object
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
                content = ''
                # text
                with open(file_path) as f_raw:
                    if cfg_parser is not None:
                        # Config parser file
                        content = cfg_parser.readfp(f_raw)
                    else:
                        content = f_raw.read()
                return content
        else:
            raise IOError("%s not found!" % file_path)
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
    resources.paws at user directory.

    :param resources_paws_path: File path to resources.paws
    :type resources_paws_path: str
    :param resources_paws_content: File content
    :type resources_paws_content: list
    """
    file_mgmt('w', resources_paws_path, resources_paws_content)
    LOG.debug("Successfully updated %s", resources_paws_path)


def log_resources(resources_paws, action):
    """Log paws resources to console.

    :param resources_paws: Resources.paws file content
    :type resources_paws: dict
    :param action: Paws action performed
    :type action: str
    """
    # case when resources.paws was not created maybe because nothing was
    # provisioned.
    if not resources_paws:
        if 'deleted' in action:
            return True
        LOG.info(LINE)
        msg = "Nothing to show, did you try provision?"
        LOG.info(msg)
        LOG.info(LINE)
        return True

    msg = "System Resources"
    LOG.info(LINE)
    LOG.info(msg.center(45))
    LOG.info(LINE)

    for index, resource in enumerate(resources_paws['resources']):
        index += 1
        LOG.info("%s.", index)
        LOG.info("    Name         : %s", resource['name'])
        LOG.info("    Provider     : %s", resource['provider'])
        if 'public_v4' in resource and resource['public_v4'] != "":
            LOG.info("    Public IPv4  : %s", resource['public_v4'])
        if 'ip' in resource and resource['ip'] != "":
            LOG.info("    Ip           : %s", resource['ip'])
        if action != "teardown":
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
    :type file_path: str
    :param error_msg: custom error message to print
    :type error_msg: str
    """
    if not exists(file_path):
        if error_msg:
            raise IOError("%s file not found! %s" % (file_path, error_msg))
        else:
            raise IOError("%s file not found!" % file_path)


@ignore_warnings
@retry(SSHError, tries=60)
def get_ssh_conn(host, username, password=None, ssh_key=None):
    """Connect to a remote system by SSH port 22.

    By default it will retry 60 times until it establishes an ssh connection.

    :param host: Remote systems IP address
    :type host: str
    :param username: Username
    :type username: str
    :param password: Password
    :type password: str
    :param ssh_key: SSH private key for authentication
    :type ssh_key: str
    """
    with spinner():
        try:
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            if ssh_key:
                ssh.connect(hostname=host,
                            username=username,
                            key_filename=ssh_key,
                            timeout=5)
            if password:
                ssh.connect(hostname=host,
                            username=username,
                            password=password,
                            timeout=5)
            ssh.close()
            LOG.info("Successfully established SSH connection to %s", host)
        except (error, SSHException, timeout):
            raise SSHError('Port 22 is unreachable.')


@ignore_warnings
@retry(SSHError, tries=60)
def exec_cmd_by_ssh(host, username, cmd, password=None, ssh_key=None,
                    fire_forget=False):
    """Connect to a remote system by SSH port 22 and run a command.

    By default it will retry 60 times until it establishes an ssh connection.

    :param host: Remote systems IP address
    :type host: str
    :param cmd: Command to execute
    :type cmd: str
    :param username: Username
    :type username: str
    :param password: Password
    :type password: str
    :param ssh_key: SSH private key for authentication
    :type ssh_key: str
    :param fire_forget: fire and forget the command
    :type fire_forget: bool
    """
    with spinner():
        try:
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            if ssh_key:
                ssh.connect(hostname=host,
                            username=username,
                            key_filename=ssh_key,
                            timeout=30)
            if password:
                ssh.connect(hostname=host,
                            username=username,
                            password=password,
                            timeout=30)

            if fire_forget:
                # fire and forget the command given, will return no output
                _timeout = 0.5
                channel = ssh.get_transport().open_session(timeout=_timeout)
                channel.settimeout(_timeout)
                channel.exec_command(cmd)
                LOG.info('Successfully executed command: %s' % cmd)
            else:
                results = ssh.exec_command(cmd)
                return_code = results[1].channel.recv_exit_status()
                if return_code:
                    LOG.error('Command %s failed to execute.' % cmd)
                    LOG.error(results[2].read())
                    ssh.close()
                    raise SystemExit(return_code)
                else:
                    LOG.debug(results[1].read().strip())
                    LOG.info("Successfully executed command: %s", cmd)
                    ssh.close()
        except (error, SSHException, timeout):
            raise SSHError('Port 22 is unreachable.')


def subprocess_call(cmd, fatal=True, cwd=None, stdout=None, stderr=None,
                    env=None):
    """Run a shell command by a subprocess call using Popen.

    :param cmd: Command to run
    :type cmd: str
    :param fatal: Whether to raise exception with failure
    :type fatal: bool
    :param cwd: Directory path to switch to before running command
    :type cwd: str
    :param stdout: Pass subprocess PIPE if you want to pipe output from
        console
    :type stdout: int
    :param stderr: Pass subprocess PIPE if you want to pipe output
        from console
    :type stderr: int
    :param env: Environment
    :type env: dict
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


def get_task_module_path(name):
    """Return the task module path.

    :param name: task name
    :type name: str
    :return: task module path
    :rtype: str
    """
    _path = PAWS_TASK_MODULES_PATH + name
    if name in ['provision', 'teardown', 'show']:
        _path = PAWS_TASK_MODULES_PATH + 'action'
    return _path
