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
Constants used throughout paws.
"""

from os.path import expanduser, join

from paws import __name__ as __paws_name__

PAWS_NAME = __paws_name__

DEFAULT_USERDIR = join(expanduser('~'), 'ws')

# CLI definitions
TASK_ARGS = {
    'userdir': {
        'dest': 'userdir',
        'default': DEFAULT_USERDIR,
        'options': ('-ud', '--userdir')
    },
    'topology': {
        'dest': 'topology',
        'default': 'resources.yaml',
        'options': ('-t', '--topology')
    },
    'credentials': {
        'dest': 'credentials',
        'default': 'credentials.yaml',
        'options': ('-c', '--credentials')
    },
    'script': {
        'dest': 'script',
        'options': ('-s', '--script')
    },
    'script_vars': {
        'dest': 'script_vars',
        'options': ('-sv', '--script_vars')
    },
    'powershell': {
        'dest': 'powershell',
        'options': ('-ps', '--powershell')
    },
    'powershell_vars': {
        'dest': 'powershell_vars',
        'options': ('-psv', '--powershell_vars')
    },
    'group': {
        'dest': 'name',
        'options': ('-n', '--name')
    },
    'systems': {
        'dest': 'system',
        'options': ('-s', '--system')
    }
}

# Default Windows Admin and Administrator accounts
ADMIN = "Admin"
ADMINISTRATOR = "Administrator"
ADMINISTRADOR_PWD = "administrator_password"

# Files name
WIN_EXEC_YAML = ".powershell_exec.yaml"

SSH_IGNORE_ERROR = [
    "time out",
    "unable to connect to port 22",
    "authentication failed",
    "connection reset by peer"]

# Group constants
GROUP_SECTIONS = ["header", "vars", "tasks"]
GROUP_SCHEMA = {'header': {}, 'vars': {}, 'tasks': []}
# regular expressions to validate content of group yaml file
GROUP_REQUIRED = {
    'header': [
        {'name': '.*.'},
        {'description': '.*.'},
        {'maintainer': "[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+"}],
    'vars': [{'topology': '(.*.yaml)$|(.*.yml)$'}]}

# Openstack authentication env variables
OPENSTACK_ENV_VARS = [
    'OS_AUTH_URL',
    'OS_PROJECT_NAME',
    'OS_USERNAME',
    'OS_PASSWORD'
]

# Ansible constants
ANSIBLE_INVENTORY_FILENAME = "hosts"

# Required resources keys to create vms by provision task
PROVISION_RESOURCE_KEYS = [
    'count',
    'name',
    'image',
    'flavor',
    'network',
    'keypair',
    'ssh_private_key',
    'administrator_password'
]

# line divisor
LINE = "*" * 45

# Path to paws task modules
PAWS_TASK_MODULES_PATH = "paws.tasks."

# Documentation links
DOC = "https://rhpit.github.io/paws"
GROUP_HELP = "%s/create_group.html" % DOC
LIBVIRT_AUTH_HELP = "%s/providers.html#libvirt" % DOC

# Register a new supported provider to PAWS
PROVIDERS = [{'name': 'openstack',
              'module': 'paws.providers.openstack',
              'class': 'OpenStack'},
             {'name': 'libvirt_kvm',
              'module': 'paws.providers.libvirt_kvm',
              'class': 'Libvirt'}]

# Libvirt vm definition saved temporally to be imported during creation
LIBVIRT_OUTPUT = '.output.xml'

# Resources paws file name
RESOURCES_PAWS = 'resources.paws'
