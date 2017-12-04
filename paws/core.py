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
from inspect import getmodule, stack
from logging import DEBUG, INFO, getLogger, Formatter, StreamHandler
from time import time

from os.path import join

from paws.constants import PAWS_NAME, RESOURCES_PAWS

__all__ = ['LoggerMixin', 'TimeMixin', 'PawsTask', 'Namespace']


class LoggerMixin(object):
    """Create logging loggers.

    Provides a method to easily create a new python logging logger. A property
    is available which returns back the paws logger.
    """

    @classmethod
    def create_logger(cls, name, verbose):
        """Create logger.

        :param name: Logger name.
        :type name: str
        :param verbose: Verbosity level.
        :type verbose: int
        """
        # get logger
        logger = getLogger(name)

        # skip creating logger if handler exists
        if logger.handlers.__len__() > 0:
            return

        # determine log formatting
        if verbose >= 1:
            log_level = DEBUG
            console = ("%(asctime)s %(levelname)s "
                       "[%(name)s.%(funcName)s:%(lineno)d] %(message)s")
        else:
            log_level = INFO
            console = ("%(message)s")

        # create stream handler
        handler = StreamHandler()

        # configure handler
        handler.setLevel(log_level)
        handler.setFormatter(Formatter(console, datefmt='%Y-%m-%d %H:%M:%S'))

        # configure logger
        logger.setLevel(log_level)
        logger.addHandler(handler)

    @property
    def logger(self):
        """Return paws logger."""
        return getLogger(getmodule(stack()[1][0]).__name__)


class TimeMixin(object):
    """Capture time delta between two points.

    Provides two methods to save start and end times. When the end time is
    saved, it will calculate the time delta between the two points. You can
    access that information by the classes atrributes.

    i.e.
        self.start()
        times.sleep(60)
        self.end()
        print('%dh:%dm:%ds' % (self.hours, self.minutes, self.seconds))
    """

    start_time = None
    end_time = None
    hours = 0
    minutes = 0
    seconds = 0

    def start(self):
        """Save the start time."""
        self.start_time = time()

    def end(self):
        """Save the end time."""
        self.end_time = time()

        # calculate time delta
        delta = self.end_time - self.start_time
        self.hours = delta // 3600
        delta = delta - 3600 * self.hours
        self.minutes = delta // 60
        self.seconds = delta - 60 * self.minutes


class PawsTask(LoggerMixin, TimeMixin):
    """Paws task.

    Provides commonly used attributes, methods, properties used by all paws
    task classes.
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

        # task exit code
        self._exit_code = 0

    @property
    def name(self):
        """Return paws task class name."""
        return self.__class__.__name__

    @property
    def exit_code(self):
        """Return paws task exit code."""
        return self._exit_code

    @exit_code.setter
    def exit_code(self, value):
        """Set paws task exit code.

        :param value: Task exit code.
        :type value: int
        """
        self._exit_code = value


class Namespace(object):
    """Convert a dictionary into a python namespace."""

    def __init__(self, kwargs):
        """Constructor.

        :param kwargs: Key:values
        :type kwargs: dict
        """
        self.__dict__.update(kwargs)
