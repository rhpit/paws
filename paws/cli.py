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
Paws cli
"""

from os import environ
from os.path import dirname, join

import click

from paws import __file__ as paws_pathfile
from paws.constants import DEFAULT_USERDIR, PAWS_TASK_MODULES_PATH, TASK_ARGS
from paws.main import Paws
from paws.util import file_mgmt, Namespace


# Allow CLI to accept short or long options for help
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# CLI options
USERDIR_SHORT = TASK_ARGS['userdir']['options'][0]
USERDIR_LONG = TASK_ARGS['userdir']['options'][1]

CREDS_SHORT = TASK_ARGS['credentials']['options'][0]
CREDS_LONG = TASK_ARGS['credentials']['options'][1]
CREDS_DEFAULT = TASK_ARGS['credentials']['default']

TOP_SHORT = TASK_ARGS['topology']['options'][0]
TOP_LONG = TASK_ARGS['topology']['options'][1]
TOP_DEFAULT = TASK_ARGS['topology']['default']

GROUP_SHORT = TASK_ARGS['group']['options'][0]
GROUP_LONG = TASK_ARGS['group']['options'][1]

PS_SHORT = TASK_ARGS['powershell']['options'][0]
PS_LONG = TASK_ARGS['powershell']['options'][1]

PSV_SHORT = TASK_ARGS['powershell_vars']['options'][0]
PSV_LONG = TASK_ARGS['powershell_vars']['options'][1]

SYSTEMS_SHORT = TASK_ARGS['systems']['options'][0]
SYSTEMS_LONG = TASK_ARGS['systems']['options'][1]


def get_version(ctx, param, value):
    """Get paws version."""
    _version = ""
    if value and param:
        try:
            # Collect version from version.txt when run by cli
            _version = file_mgmt('r', join(dirname(paws_pathfile),
                                           "version.txt"))
        except IOError:
            # Collect version when run from IDE
            with open('../Makefile') as mkfile:
                fdata = mkfile.readlines()
                for line in fdata:
                    if "VERSION=" in line:
                        version = line.strip("VERSION=").strip()
                    elif "RELEASE=" in line:
                        release = line.strip("RELEASE=").strip()
                _version = version + "-" + release
        finally:
            click.echo(_version.strip())
            ctx.exit()


def run(args, task):
    """Run paws."""
    # Create Python namespace from dict
    args = Namespace(args)

    # Create paws object
    paws_obj = Paws(
        task,
        PAWS_TASK_MODULES_PATH + task,
        args
    )

    # Run paws
    paws_obj.run()


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(USERDIR_SHORT, USERDIR_LONG, default=DEFAULT_USERDIR,
              help="User directory", metavar="")
@click.option("-v", "--verbose", count=True, help="Verbose mode")
@click.option("--version", is_flag=True, callback=get_version,
              expose_value=False, is_eager=True,
              help="Show version and exit.")
@click.pass_context
def paws(ctx=None, userdir=None, verbose=None):
    """PAWS command-line interface"""
    # Custom ansible.cfg
    environ['ANSIBLE_CONFIG'] = DEFAULT_USERDIR
    ctx.obj = {}
    ctx.obj['userdir'] = userdir
    ctx.obj['verbose'] = verbose


@paws.command()
@click.option(CREDS_SHORT, CREDS_LONG, default=CREDS_DEFAULT,
              help="Providers credential information", metavar="")
@click.option(TOP_SHORT, TOP_LONG, default=TOP_DEFAULT,
              help="System resources topology", metavar="")
@click.pass_context
def provision(ctx, credentials, topology):
    """Provision system resources"""
    ctx.obj['credentials'] = credentials
    ctx.obj['topology'] = topology

    run(ctx.obj, "provision")


@paws.command()
@click.option(CREDS_SHORT, CREDS_LONG, default=CREDS_DEFAULT,
              help="Providers credential information", metavar="")
@click.option(TOP_SHORT, TOP_LONG, default=TOP_DEFAULT,
              help="System resources topology", metavar="")
@click.pass_context
def teardown(ctx, credentials, topology):
    """Teardown system resources"""
    ctx.obj['credentials'] = credentials
    ctx.obj['topology'] = topology

    run(ctx.obj, "teardown")


@paws.command()
@click.option(TOP_SHORT, TOP_LONG, default=TOP_DEFAULT,
              help="System resources topology", metavar="")
@click.option(PS_SHORT, PS_LONG, required=True,
              help="PowerShell script filename", metavar="")
@click.option(PSV_SHORT, PSV_LONG, help="PowerShell variables", metavar="")
@click.option(SYSTEMS_SHORT, SYSTEMS_LONG,
              help="System to configure (default=All Resources)", metavar="",
              multiple=True)
@click.pass_context
def winsetup(ctx, topology, powershell, powershell_vars, system):
    """Configure Windows systems"""
    ctx.obj['topology'] = topology
    ctx.obj['powershell'] = powershell
    ctx.obj['powershell_vars'] = powershell_vars
    if system.__len__() > 0:
        # User defined certain systems to configure
        systems = [item for item in system]
        ctx.obj['systems'] = systems

    run(ctx.obj, "winsetup")


@paws.command()
@click.option(GROUP_SHORT, GROUP_LONG, required=True,
              help="Group template filename", metavar="")
@click.pass_context
def group(ctx, name):
    """Run a group template"""
    ctx.obj['name'] = name

    run(ctx.obj, "group")


@paws.command()
@click.option(CREDS_SHORT, CREDS_LONG, default=CREDS_DEFAULT,
              help="Providers credential information", metavar="")
@click.option(TOP_SHORT, TOP_LONG, default=TOP_DEFAULT,
              help="System resources topology", metavar="")
@click.pass_context
def show(ctx, credentials, topology):
    """Show system(s) already provisioned"""
    ctx.obj['credentials'] = credentials
    ctx.obj['topology'] = topology

    run(ctx.obj, "show")


if __name__ == "__main__":
    paws()
