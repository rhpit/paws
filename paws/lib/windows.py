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

"""Module containing classes and functions regarding Windows actions."""

from logging import getLogger

from os.path import join

from paws.constants import ADMINISTRATOR, ADMINISTRADOR_PWD, ADMIN
from paws.constants import WIN_EXEC_YAML
from paws.exceptions import SSHError
from paws.helpers import exec_cmd_by_ssh, get_ssh_conn
from paws.helpers import file_mgmt

LOG = getLogger(__name__)

__all__ = ['create_ps_exec_playbook', 'set_administrator_password',
           'ipconfig_release', 'rearm_server']


def create_ps_exec_playbook(user_dir, play_vars):
    """Creates the playbook to execute Windows PowerShell scripts.

    :param user_dir: user directory
    :param play_vars: determines if playbook vars are required
    """
    filename = join(user_dir, WIN_EXEC_YAML)
    playbook = dict(
        gather_facts='False',
        hosts='{{ hosts }}',
        name='Execute Windows PowerShell'
    )

    if play_vars == 'file':
        playbook['vars'] = dict(win_var_path='c:/my_vars.json')
        playbook['tasks'] = [
            dict(
                name='Copy JSON vars to Windows system',
                win_copy='src={{ psv }} dest={{ win_var_path }}'
            ),
            dict(
                name='Execute PowerShell on Windows system',
                script='{{ ps }} {{ win_var_path }}'
            )
        ]
    elif play_vars == 'str':
        playbook['tasks'] = [
            dict(
                name='Execute PowerShell on Windows system',
                script='{{ ps }} {{ psv }}'
            )
        ]
    elif play_vars is None:
        playbook['tasks'] = [
            dict(
                name='Execute PowerShell on Windows system',
                script='{{ ps }}'
            )
        ]

    file_mgmt('w', filename, [playbook])
    LOG.debug('Playbook %s created.', filename)

    return filename


def set_administrator_password(resources, user_dir):
    """Set the windows administrator account password.

    :param resources: system resources
    :param user_dir: user directory
    """
    for res in resources:
        if ADMINISTRADOR_PWD not in res:
            # administrator password not required for resource, skipping..
            continue

        LOG.info('Setting vm %s administrator password.', res['name'])
        cmd = 'net user Administrator %s' % res[ADMINISTRADOR_PWD]

        try:
            exec_cmd_by_ssh(
                res['public_v4'],
                ADMIN,
                cmd,
                ssh_key=res['ssh_private_key']
            )
        except SSHError:
            LOG.error('Unable to set Administrator password for vm: %s.' %
                      res['name'])
            raise SSHError(1)

        res["win_username"] = ADMINISTRATOR
        res["win_password"] = res[ADMINISTRADOR_PWD]
        res.pop(ADMINISTRADOR_PWD)

        LOG.info('Successfully set vm %s administrator password!', res['name'])

    return resources


def ipconfig_release(res):
    """Release the Windows IPv4 address for all adapters.

    To take a snapshot of a Windows server you need to release all IPv4
    ethernet connections and shutdown the server. This will allow the
    snapshot to not be created with any prior network connections. If this
    is not done, the new server provisioned based on the snapshot created.
    Will not have network connectivity, until you release ethernet
    connections/renew.

    :param res: windows resource
    """
    LOG.info('Attempt SSH connection to vm: %s.', res['name'])

    # connect
    get_ssh_conn(
        res['public_v4'],
        res['win_username'],
        res['win_password']
    )

    LOG.info('Release all IPv4 addresses for vm: %s.', res['name'])

    # release ips
    exec_cmd_by_ssh(
        res['public_v4'],
        res['win_username'],
        'ipconfig /release',
        password=res['win_password'],
        fire_forget=True
    )

    LOG.info('Successfully released IPv4 addresses for vm: %s.', res['name'])


def rearm_server(res):
    """Extend the Windows trial period.

    Windows only allows X amount of days to use their software in the
    trial period. You can extend this up to 3 times. Need to rearm a
    server if planning to take snapshot in order to extend the trial
    period window.

    - slmgr.vbs -rearm (rearm server)
    - slmgr.vbs /dlv (Display software licensing)
    - shutdown.exe /r /f /t 0 (Restart to take effect)

    :param res: windows resource
    """
    LOG.info('Attempt SSH connection to vm: %s.', res['name'])

    # connect
    get_ssh_conn(
        res['public_v4'],
        res['win_username'],
        res['win_password']
    )

    LOG.debug("Extending the rearm count for %s" % res['name'])

    # rearm server
    exec_cmd_by_ssh(
        res['public_v4'],
        res['win_username'],
        'cscript C:\\Windows\\System32\\slmgr.vbs -rearm',
        password=res['win_password']
    )

    LOG.info('Attempt SSH connection to vm: %s.', res['name'])

    # connect
    get_ssh_conn(
        res['public_v4'],
        res['win_username'],
        res['win_password']
    )

    # restart server
    exec_cmd_by_ssh(
        res['public_v4'],
        res['win_username'],
        'shutdown.exe /r /f /t 0',
        password=res['win_password']
    )
    LOG.debug('Successfully extended the rearm count for %s.' % res['name'])
