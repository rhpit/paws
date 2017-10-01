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
"""Paws core module."""
from os.path import join

from paws.constants import PAWS_NAME, RESOURCES_PAWS
from paws.util import LoggerMixin, TimeMixin


class PawsTask(LoggerMixin, TimeMixin):
    """Paws task.

    Every paws task should inherit this parent paws task class.
    """

    def __init__(self, userdir, verbose):
        """Constructor.

        :param userdir: User directory.
        :type userdir: str
        :param verbose: Verbosity level.
        :type verbose: int
        """
        self.userdir = userdir
        self.verbose = verbose
        self.resources_paws = None
        self.resources_paws_file = join(self.userdir, RESOURCES_PAWS)

        # create logger
        self.create_logger(PAWS_NAME, self.verbose)

    @property
    def name(self):
        """Return paws task class name."""
        return self.__class__.__name__
