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
Python build distribution for PAWS
"""

from os.path import exists
from setuptools import setup

VERSION = "paws/version.txt"


def get_version():
    """Get version and release"""
    # version.txt file is copied during build process
    if exists(VERSION):
        with open(VERSION, "r") as version_file:
            version = version_file.read()
            return version
    else:
        return "dev"


setup(
    name='paws-cli',
    version=get_version(),
    description='A tool used to provision Windows systems and configure '
                'Windows services.',
    long_description='Paws is a Linux based tool to provision Windows systems '
                     'and configure Windows services. Providing a simple '
                     'way to test hybrid environments (Linux and Windows).',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Quality Assurance'
    ],
    keywords='Provision Automation Windows Quality Assurance Tests Hybrid',
    url='https://rhpit.github.io/paws/',
    author='Eduardo Cerqueira,Ryan Williams',
    author_email='eduardomcerqueira@gmail.com,rwilliams5262@gmail.com',
    maintainer='Eduardo Cerqueira,Ryan Williams',
    maintainer_email='eduardomcerqueira@gmail.com,rwilliams5262@gmail.com',
    platforms='RHEL >= 7.2 Fedora >= 24 CentOS >= 7.2',
    license='GPL',
    include_package_data=True,
    zip_safe=False,
    packages=[
              'paws',
              'paws.lib',
              'paws.providers',
              'paws.tasks'
    ],
    install_requires=['paramiko==2.2.1',
                      'pywinrm',
                      'click',
                      'click_spinner',
                      'apache-libcloud',
                      'ansible'],
    extras_require={
        'libvirt': ['libvirt-python']
    },
    entry_points={'console_scripts': ['paws=paws.cli:paws']}
)
