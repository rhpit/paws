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
Decorator functions to use in PAWS
"""

from logging import getLogger
from time import sleep
from functools import wraps

from paws.exceptions import PawsPreTaskError

LOG = getLogger(__name__)


def retry(exception_to_check, tries=4, delay=10, backoff=1, logger=LOG):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param exception_to_check: the exception to check. may be a tuple of
        exceptions to check
    :type exception_to_check: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(function_name):

        @wraps(function_name)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return function_name(*args, **kwargs)
                except exception_to_check, ex:
                    try:
                        msg = "%s, retrying in %d seconds..." %\
                            (str(ex), mdelay)
                        if logger:
                            logger.debug(msg)
                        else:
                            print msg
                        sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
            return function_name(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def handle_pre_tasks(func):
    """A decorator which will handle all exceptions raised in any paws
    pre_tasks methods.
    """
    def func_wrapper(*args, **kwargs):
        """Wrapper function."""
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            LOG.warning("CTRL+C detected, interrupting execution")
            raise PawsPreTaskError
        except Exception as ex:
            LOG.error(ex)
            raise PawsPreTaskError
        return func
    return func_wrapper
