Teardown
--------

**DESCRIPTION**

Teardown task will teardown system resources in your supplied provider. It will
teardown the resources you have defined inside your resources.yaml if they are
active instances.

**ARGUMENTS**

.. csv-table::
	:header: "Argument", "Default", "Required", "Description"
	:widths: 100, 100, 100, 100

	"-c, --credentials", "`credentials.yaml <files.html#credentials-yaml>`_", "Yes", "Providers credential file
	which contains authentication information."
	"-t, --topology", "`resources.yaml <files.html#resources-yaml>`_", "Yes", "System resources file which
	contains systems you want to teardown."
	"-h, --help", "", "No", "Enable to see help menu."

**EXAMPLES**

.. code:: bash

	# Teardown using default arguments
	$ paws teardown

	# Teardown using default arguments and verbose logging
	$ paws -v teardown

	# Teardown using specific user directory and verbose logging
	$ paws -v -ud /home/user teardown

	# Show teardown help menu
	$ paws teardown -h

**OUTPUT**

You will see similar output as below when a system resource has been deleted.

.. code:: bash

	2016-12-13 20:57:59 INFO [paws.util.log_resources:305] *********************************************
	2016-12-13 20:57:59 INFO [paws.util.log_resources:306]           System Resources (deleted)         
	2016-12-13 20:57:59 INFO [paws.util.log_resources:307] *********************************************
	2016-12-13 20:57:59 INFO [paws.util.log_resources:311] 1.
	2016-12-13 20:57:59 INFO [paws.util.log_resources:312]     Name         : CI_PAWS_win-2012-r2
	2016-12-13 20:57:59 INFO [paws.util.log_resources:314]     Public IPv4  : 10.8.173.232
	2016-12-13 20:57:59 INFO [paws.util.log_resources:319] *********************************************
	2016-12-13 20:57:59 INFO [paws.tasks.teardown.post_tasks:136] END: Teardown, TIME: 0h:0m:7s
	2016-12-13 20:57:59 INFO [paws.main:94] End paws execution in 0h:0m:7s
