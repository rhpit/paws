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
Purpose:
----------
To provide a simplified way to easily test paws on its supported platforms
(vms, containers) for its operating systems matrix.

Requirements
------------
The following python packages are needed:
    - ansible
    - docker
    - docker-py *

* You may need to install this package at the system level if running in a
virtual environment.

How to run
----------
    1. Fill in the playbooks/vars.yml file with the required variables.
        - $ vi playbooks/vars.yml
    2. Install two required paws roles
        - $ ansible-galaxy install rywillia.paws-install
        - $ ansible-galaxy install rywillia.paws-run
    3. Edit the tests ansible.cfg to point to the location where your ansible
       roles are stored.
        - $ vi tests/ansible.cfg
   5. Call the test case you would like to run.
        - $ python paws_ci_tests.py run -tc tc_01
"""

import argparse
import random
import subprocess


class TestPaws(object):
    def __init__(self):
        self.inventory = 'playbooks/paws_inventory'
        self.vars_file = 'playbooks/vars.yml'

    @staticmethod
    def runner(cmd):
        proc = subprocess.Popen(
            cmd,
            shell=True
        )

        proc.communicate()
        return proc.returncode

    def create_containers(self):
        cmd = 'ansible-playbook playbooks/create_containers.yml'
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to create containers.')

    def create_paws_containers(self):
        cmd = 'ansible-playbook playbooks/create_paws_containers.yml'
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to create paws image containers.')

    def delete_containers(self):
        cmd = 'ansible-playbook playbooks/delete_containers.yml'
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to delete containers.')

    def create_vms(self):
        cmd = 'ansible-playbook playbooks/create_vms.yml'
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to create vms.')

    def delete_vms(self):
        cmd = 'ansible-playbook playbooks/delete_vms.yml'
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to delete vms.')

    def install_paws(self, install_choice):
        cmd = 'ansible-playbook playbooks/install_paws.yml -e '\
            '"install_type=%s" -i %s' % (install_choice, self.inventory)
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to install paws.')

    def unregister_system(self):
        cmd = 'ansible-playbook playbooks/unregister.yml -i %s' %\
              self.inventory
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to unregister systems.')

    def run_paws(self, task):
        cmd = 'ansible-playbook playbooks/run_paws.yml -e'\
            '"task=%s" -i %s' % (task, self.inventory)
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to run paws task %s.' % task)

    def configure_paws(self):
        cmd = 'ansible-playbook playbooks/configure_paws.yml -i %s' %\
            self.inventory
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to configure paws.')

    def unique_resource(self):
        random_num = random.randrange(0, 10000)
        cmd = 'sed -i "s/{{ random }}/%s/g" %s' % (random_num, self.vars_file)
        exit_code = self.runner(cmd)
        if exit_code != 0:
            raise Exception('Failed to set unique resource name.')

    def tc_01(self):
        """Test case 01.

        Actions:
            1. Create containers
            2. Install paws by pip
            3. Configure paws
            4. Test all paws tasks
            5. Un-register systems (if applicable)
            6. Delete containers
        """
        self.unique_resource()

        try:
            self.create_containers()
            self.install_paws('pip')
            self.configure_paws()
            self.run_paws('provision')
            self.run_paws('winsetup')
            self.run_paws('show')
            self.run_paws('group')
            self.run_paws('teardown')
            self.unregister_system()
            self.delete_containers()
        except Exception:
            self.unregister_system()
            self.delete_containers()
            raise SystemExit(1)

    def tc_02(self):
        """Test case 02.

        Actions:
            1. Create vms
            2. Install paws by pip
            3. Configure paws
            4. Test all paws tasks
            5. Un-register systems (if applicable)
            6. Delete vms
        """
        self.unique_resource()

        try:
            self.create_vms()
            self.install_paws('pip')
            self.configure_paws()
            self.run_paws('provision')
            self.run_paws('winsetup')
            self.run_paws('show')
            self.run_paws('group')
            self.run_paws('teardown')
            self.unregister_system()
            self.delete_vms()
        except Exception:
            self.unregister_system()
            self.delete_vms()
            raise SystemExit(1)

    def tc_03(self):
        """Test case 03.

        Actions:
            1. Create containers
            2. Install paws by rpm
            3. Configure paws
            4. Test all paws tasks
            5. Un-register systems (if applicable)
            6. Delete containers
        """
        self.unique_resource()

        try:
            self.create_containers()
            self.install_paws('rpm')
            self.configure_paws()
            self.run_paws('provision')
            self.run_paws('winsetup')
            self.run_paws('show')
            self.run_paws('group')
            self.run_paws('teardown')
            self.unregister_system()
            self.delete_containers()
        except Exception:
            self.unregister_system()
            self.delete_containers()
            raise SystemExit(1)

    def tc_04(self):
        """Test case 04.

        Actions:
            1. Create vms
            2. Install paws by rpm
            3. Configure paws
            4. Test all paws tasks
            5. Un-register systems (if applicable)
            6. Delete vms
        """
        self.unique_resource()

        try:
            self.create_vms()
            self.install_paws('rpm')
            self.configure_paws()
            self.run_paws('provision')
            self.run_paws('winsetup')
            self.run_paws('show')
            self.run_paws('group')
            self.run_paws('teardown')
            self.unregister_system()
            self.delete_vms()
        except Exception:
            self.unregister_system()
            self.delete_vms()
            raise SystemExit(1)

    def tc_05(self):
        """Test case 05.

        Actions:
            1. Create containers based on paws supported docker images
            2. Test all paws tasks
            3. Un-registery systems (if applicable)
            4. Delete containers
        """
        self.unique_resource()

        try:
            self.create_paws_containers()
            self.run_paws('provision')
            self.run_paws('winsetup')
            self.run_paws('show')
            self.run_paws('group')
            self.run_paws('teardown')
            self.unregister_system()
            self.delete_containers()
        except Exception:
            self.unregister_system()
            self.delete_containers()
            raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PAWS CI TEST CASES')
    sub_parser = parser.add_subparsers()
    tc_01 = sub_parser.add_parser('run', help='Run a test case')
    tc_01.add_argument(
        '-tc',
        action='store',
        choices=('tc_01', 'tc_02', 'tc_03', 'tc_04', 'tc_05'),
        help='List of test cases'
    )

    args = parser.parse_args()
    obj = TestPaws()
    getattr(obj, args.tc)()