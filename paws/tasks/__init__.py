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
Package containing paws task modules.
"""

from os.path import join, splitext

from paws.util import LoggerMixin, TimeMixin


class Tasks(LoggerMixin, TimeMixin):
    """Parent tasks class inherited by child tasks classes."""

    def __init__(self, args):
        """Constructor.

        Defines all common attributes.
        """
        self.args = args
        self.userdir = args.userdir
        self.topology = args.topology
        self.topology_file = join(self.userdir, self.topology)
        self.resources_paws = join(splitext(self.topology_file)[0] + ".paws")
