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

"""Custom paws exceptions."""


class PawsError(Exception):
    """Base class for all custom paws exceptions."""
    pass


class SSHError(PawsError):
    """Exception raised for errors with SSH connections."""

    def __init__(self, message):
        """Constructor.

        :param message: explanation about the error
        """
        self.message = message


class ProvisionError(PawsError):
    """Exception raised for errors with provisioning."""

    def __init__(self, message):
        """Constructor.

        :param message: explanation about the error
        """
        self.message = message


class TeardownError(PawsError):
    """Exception raised for errors with teardown."""

    def __init__(self, message):
        """Constructor.

        :param message: explanation about the error
        """
        self.message = message


class ShowError(PawsError):
    """Exception raised for errors with show."""

    def __init__(self, message):
        """Constructor.

        :param message: explanation about the error
        """
        self.message = message


class NotFound(PawsError):
    """Exception raised for when objects are not found."""

    def __init__(self, message):
        """Constructor.

        :param message: explanation about the error
        """
        self.message = message


class BootError(PawsError):
    """Exception raised for errors while attempting to boot a vm."""

    def __init__(self, message):
        """Constructor.

        :param message: explanation about the error
        """
        self.message = message


class BuildError(PawsError):
    """Exception raised for errors while vm attempts to finish building."""

    def __init__(self, message):
        """Constructor.

        :param message: explanation about the error
        """
        self.message = message


class NetworkError(PawsError):
    """Exception raised for errors while vm attempts to set networking."""

    def __init__(self, message):
        """Constructor.

        :param message: explanation about the error
        """
        self.message = message
