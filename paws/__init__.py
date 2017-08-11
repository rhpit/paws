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
PAWS custom Logging
"""

from logging import DEBUG, INFO, getLogger, Formatter, StreamHandler


class Logging(object):
    """A class to handle paws logging."""

    def __init__(self, verbose):
        """Constructor.

        :param verbose: Logging level
        :type verbose: int
        """
        self.verbose = verbose

        # Create logger, handlers, formatter
        self.logger = getLogger(__name__)
        self.console_handler = StreamHandler()
        self.configure()

    def configure(self):
        """Setup the logging configuration."""
        # Determine log level
        if self.verbose >= 1:
            # Verbose >= 1 = DEBUG
            loglevel = DEBUG
            console = ("%(asctime)s %(levelname)s "
                       "[%(name)s.%(funcName)s:%(lineno)d] %(message)s")
        else:
            # Verbose < 1 = INFO
            loglevel = INFO
            console = ("%(message)s")

        # Set logging formatter
        self.formatter = Formatter(console, datefmt='%Y-%m-%d %H:%M:%S')

        # Set logging levels
        self.logger.setLevel(loglevel)
        self.console_handler.setLevel(loglevel)

        # Add formatters to handlers
        self.console_handler.setFormatter(self.formatter)

        # Add handlers to logger
        self.logger.addHandler(self.console_handler)
