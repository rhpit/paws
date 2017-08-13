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
Paws exceptions.
"""


class PawsError(Exception):
    """Base class for paws exceptions."""
    pass


class PawsMsgError(Exception):
    """Base class for paws exceptions with messages."""

    def __init__(self, msg):
        """Constructor."""
        self.msg = msg

    def __str__(self):
        """Return the string given at time of exception raised."""
        return repr(self.msg)


class ProvisionError(PawsError):
    """Exception raised for errors with provision task."""
    pass


class ShowError(PawsError):
    """Exception raised for errors with show task."""
    pass


class SSHError(PawsMsgError):
    """Exception raised for errors with SSH connections."""

    def __init__(self, msg):
        """Constructor."""
        super(SSHError, self).__init__(msg)


class NovaPasswordError(PawsMsgError):
    """Exception raised for errors with getting nova password."""

    def __init__(self, msg):
        """Constructor."""
        super(NovaPasswordError, self).__init__(msg)


class PawsPreTaskError(PawsError):
    """Exception raised for errors with paws tasks pre_task actions."""