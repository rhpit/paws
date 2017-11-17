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
Python module to process Ansible results.
"""

from logging import getLogger
from pprint import pformat

from ansible.errors import AnsibleRuntimeError

LOG = getLogger(__name__)


class ResultsBase(object):
    """
    Base results class to process callback content. This will use the
    pprint library pformat method to display the content.
    """

    def __init__(self, result, callback, def_callback):
        """Constructor.

        :param results: Return code from Ansible call
        :type results: int
        :param callback: Ansible callback object
        :type callback: object
        :param def_callback: Whether to display results using default callback
            or not
        :type def_callback: bool
        """
        self.result = result
        self.callback = callback
        self.def_callback = def_callback

    def msg(self):
        """Log status of Ansible call."""
        if self.result != 0:
            status = "execution failed"
        else:
            status = "executed successfully"

        LOG.debug("Ansible call %s!", status)

        if self.callback.contacted and self.callback.\
                contacted[0]['success'] is False:
            LOG.error(self.callback.contacted[0]['results']['msg'])

    def quit(self):
        """Quit paws based on results of Ansible call."""
        if self.result != 0:
            raise AnsibleRuntimeError

    def process(self):
        """Process results."""
        if not self.def_callback:
            LOG.debug(pformat(self.callback.contacted, indent=2))

        self.msg()
        self.quit()


class GenModuleResults(ResultsBase):
    """
    Generic module results class to process callback content in a nice
    format.
    """

    def __init__(self, result, callback, def_callback):
        """Constructor.

        :param results: Return code from Ansible call
        :type results: int
        :param callback: Ansible callback object
        :type callback: object
        :param def_callback: Whether to display results using default callback
            or not
        :type def_callback: bool
        """
        ResultsBase.__init__(self, result, callback, def_callback)

    def process(self):
        """Process results."""
        if not self.def_callback:
            LOG.info("-" * 15)
            LOG.info("Results")
            LOG.info("-" * 15)

            for item in self.callback.contacted:
                try:
                    if 'results' in item and item['results']['changed'] \
                            and 'rc' in item['results']:
                        LOG.info("** %s **", item['host'])

                        # Standard output
                        if self.result == 0:
                            LOG.info("Standard output:")
                            for line in item['results']['stdout_lines']:
                                LOG.info(line)

                        # Standard error
                        if self.result != 0:
                            LOG.info("Standard error:")
                            LOG.error(item['results']['stderr'])
                            for line in item['results']['stdout_lines']:
                                LOG.error(line)
                except KeyError:
                    pass

            if self.callback.contacted.__len__() == 0:
                LOG.error("Failed to contact remote hosts.")
                self.result = 1

        self.msg()
        self.quit()


class CloudModuleResults(ResultsBase):
    """
    Cloud module results class to process callback contents in a nice format.
    """

    def __init__(self, result, callback, def_callback):
        """Constructor.

        :param results: Return code from Ansible call
        :type results: int
        :param callback: Ansible callback object
        :type callback: object
        :param def_callback: Whether to display results using default callback
            or not
        :type def_callback: bool
        """
        ResultsBase.__init__(self, result, callback, def_callback)

    def process(self):
        """Process results."""
        if not self.def_callback:
            stop = False

            if self.result != 0:
                # Failure
                LOG.info("-" * 15)
                LOG.info("Results")
                LOG.info("-" * 15)

                for item in self.callback.contacted:
                    if not item['success']:
                        try:
                            LOG.info("Standard error:")
                            _error_msg = item['results']['msg']
                            LOG.error(_error_msg)
                            # Stop on http errors
                            if 'HTTP' in _error_msg:
                                stop = True
                        except KeyError:
                            LOG.error("Failed to retrieve error message.")

        self.msg()

        if stop and self.result != 0:
            raise SystemExit(1)
        else:
            self.quit()
