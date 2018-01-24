Teardown
--------

**DESCRIPTION**

Teardown task will teardown system resources in your supplied provider. It will
teardown the resources you have defined inside your resources.yaml if they are
active instances.

**ARGUMENTS**

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Argument
        - Default
        - Required
        - Description

    *   - -c, --credentials
        - credentials.yaml
        - Yes
        - Providers credentials settings

    *   - -t, --topology
        - resources.yaml
        - Yes
        - System resources definition

    *   - -h, --help
        -
        - No
        - Enable to show help menu

**EXAMPLES**

.. code-block:: bash
    :linenos:

    # teardown using default options
    paws teardown

    # teardown using default options with verbose logging
    paws -v teardown

    # teardown overriding user directory
    paws -ud /tmp/ws teardown

    # show help menu
    paws teardown --help

**OUTPUT**

You will see similar output as below when a system resource has been deleted.

.. code-block:: bash

	2016-12-13 20:57:59 INFO [paws.util.log_resources:305] *********************************************
	2016-12-13 20:57:59 INFO [paws.util.log_resources:306]           System Resources (deleted)         
	2016-12-13 20:57:59 INFO [paws.util.log_resources:307] *********************************************
	2016-12-13 20:57:59 INFO [paws.util.log_resources:311] 1.
	2016-12-13 20:57:59 INFO [paws.util.log_resources:312]     Name         : CI_PAWS_win-2012-r2
	2016-12-13 20:57:59 INFO [paws.util.log_resources:314]     Public IPv4  : 10.8.173.232
	2016-12-13 20:57:59 INFO [paws.util.log_resources:319] *********************************************
	2016-12-13 20:57:59 INFO [paws.tasks.teardown.post_tasks:136] END: Teardown, TIME: 0h:0m:7s
	2016-12-13 20:57:59 INFO [paws.main:94] End paws execution in 0h:0m:7s
