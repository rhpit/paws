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

from setuptools import setup
from os.path import exists

VERSION = "../rpmbuild/SOURCES/version.txt"

def get_version():
    """Get version and release"""
    # version.txt file is copied during build process    
    if exists(VERSION):
        with open(VERSION, "r") as version_file:
            version = version_file.read()
            return version
    else:
        return "0"

setup(
    name='paws',
    version=get_version(),
    description='PAWS is a command line tool to provision, install and \
configure Windows systems anyone who needs to perform some actions with a \
Windows system or test on hybrid environment ( Linux and Windows )',
    long_description="see https://rhpit.github.io/paws/",
    classifiers=['Development Status :: 4 - Beta',
                 'License :: OSI Approved :: GPL License',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Software Development :: Quality Assurance',
                 ],
    keywords='Provision Automation Windows Quality Assurance',
    url='https://rhpit.github.io/paws/',
    author='Eduardo Cerqueira, Ryan Williams',
    author_email='eduardomcerqueira@gmail.com, rwilliams5262@gmail.com',
    platforms='RHEL >= 7.2, Fedora >= 24, CentOS >= 7.2',
    license='GPL',
    include_package_data=True,
    zip_safe=False,
    packages=[
              'paws',
              'paws.providers',
              'paws.remote',
              'paws.tasks',
              'paws.util'
    ],
    test_suite="nose.collector",
    tests_require="nose",
    entry_points={'console_scripts': ['paws=paws.cli:paws']}
)

print "Python build target complete"
