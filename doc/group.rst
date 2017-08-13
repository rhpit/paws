Group
-----

**DESCRIPTION**

Group task gives users the ability to bulk multiple paws task calls into a
single paws call.

**ARGUMENTS**

.. csv-table::
	:header: "Argument", "Default", "Required", "Description"
	:widths: 100, 100, 100, 100

	"-ud, --userdir", "/usr/share/paws", "Yes", "User directory where files
	used by paws are stored."
	"-n, --name", "", "Yes", "Group template filename."
	"-v, --verbose", "", "No", "Enable to have verbose logging."
	"-h, --help", "", "No", "Enable to see help menu."

**EXAMPLES**

.. code:: bash

	# Group using default user directory and specific group file
	$ paws group -n group/my_group.yaml

	# Group using specific user directory, specific group file and verbose logging
	$ paws -v -ud /home/user group -n group/my_group.yaml

	# Show group help menu
	$ paws group -h

**OUTPUT**

Group output will be the same as all other paws tasks just combined.

.. note::
	To learn how to create a group visit the following: `Create group file
	<create_group.html>`_.
