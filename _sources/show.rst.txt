Show
----

**DESCRIPTION**

Show task will display system resources in your supplied provider. It
assumes the `provision task <guide.html#provision>`_ was called previously and
your system resource was successfully provisioned. If show does not find any
system resources in your supplied provider. A warning message will be
displayed instead.

**ARGUMENTS**

.. csv-table::
	:header: "Argument", "Default", "Required", "Description"
	:widths: 100, 100, 100, 100

	"-c, --credentials", "`credentials.yaml <files.html#credentials-yaml>`_", "Yes", "Providers credentials file
	containing authentication information."
	"-t, --topology", "`resources.yaml <files.html#resources-yaml>`_", "Yes", "System resources file which
	contains systems you want to display information for."
	"-h, --help", "", "No", "Enable to see help menu."

**EXAMPLES**

.. code:: bash

	# Show using default arguments
	$ paws show

	# Show using default arguments and verbose logging
	$ paws -v show

	# Show using specific user directory and verbose logging
	$ paws -v -ud /home/user show

	# Show help menu for show
	$ paws show -h

**OUTPUT**

**Active instance provisioned by paws.**

.. code:: bash

	[ecerquei@dev paws]$ paws show
	2016-12-02 16:26:30 INFO Begin paws execution
	2016-12-02 16:26:30 INFO START: Show
	2016-12-02 16:26:30 INFO Openstack providers credentials are set by a credentials file.
	2016-12-02 16:26:35 INFO *********************************************
	2016-12-02 16:26:35 INFO            System Resources (show)
	2016-12-02 16:26:35 INFO *********************************************
	2016-12-02 16:26:35 INFO 1.
	2016-12-02 16:26:35 INFO     Name         : PAWS_eduardo
	2016-12-02 16:26:35 INFO     Public IPv4  : 10.8.172.154
	2016-12-02 16:26:35 INFO     Username     : Administrator
	2016-12-02 16:26:35 INFO     Password     : my_password@2016
	2016-12-02 16:26:35 INFO *********************************************
	2016-12-02 16:26:35 INFO END: Show, TIME: 0h:0m:4s
	2016-12-02 16:26:35 INFO End paws execution in 0h:0m:5s


**Active instance provisioned by paws running in verbose mode.**

.. code:: bash

	[ecerquei@dev paws]$ paws show -v
	2016-12-02 16:27:07 INFO [paws.main:53] Begin paws execution
	2016-12-02 16:27:07 DEBUG [paws.main:54] *********************************************
	2016-12-02 16:27:07 DEBUG [paws.main:55]                 Paws arguments
	2016-12-02 16:27:07 DEBUG [paws.main:56] *********************************************
	2016-12-02 16:27:07 DEBUG [paws.main:59] task: show
	2016-12-02 16:27:07 DEBUG [paws.main:59] verbose: 2
	2016-12-02 16:27:07 DEBUG [paws.main:59] userdir: /usr/share/paws
	2016-12-02 16:27:07 DEBUG [paws.main:59] credentials: credentials.yaml
	2016-12-02 16:27:07 DEBUG [paws.main:59] topology: resources.yaml
	2016-12-02 16:27:07 DEBUG [paws.main:60] *********************************************
	2016-12-02 16:27:07 INFO [paws.tasks.show.run:74] START: Show
	2016-12-02 16:27:07 DEBUG [paws.providers.openstack.get_credentials:215] Getting Openstack credentials.
	2016-12-02 16:27:07 INFO [paws.providers.openstack.get_credentials:231] Openstack providers credentials are set by a credentials file.
	2016-12-02 16:27:07 DEBUG [paws.providers.openstack.create:641] Playbook /usr/share/paws/.get_ops_facts.yaml created.
	2016-12-02 16:27:07 DEBUG [paws.remote.driver.run_playbook:241] Running Ansible Playbook /usr/share/paws/.get_ops_facts.yaml
	2016-12-02 16:27:09 DEBUG [paws.remote.results.msg:59] Ansible call executed successfully!
	2016-12-02 16:27:09 DEBUG [paws.providers.openstack.generate_resources_paws:284] Generating /usr/share/paws/resources.paws
	2016-12-02 16:27:09 DEBUG [paws.providers.openstack.generate_resources_paws:317] Successfully created /usr/share/paws/resources.paws
	2016-12-02 16:27:09 DEBUG [paws.util.update_resources_paws:289] Successfully updated /usr/share/paws/resources.paws
	2016-12-02 16:27:09 INFO [paws.util.log_resources:305] *********************************************
	2016-12-02 16:27:09 INFO [paws.util.log_resources:306]            System Resources (show)
	2016-12-02 16:27:09 INFO [paws.util.log_resources:307] *********************************************
	2016-12-02 16:27:09 INFO [paws.util.log_resources:311] 1.
	2016-12-02 16:27:09 INFO [paws.util.log_resources:312]     Name         : PAWS_eduardo
	2016-12-02 16:27:09 INFO [paws.util.log_resources:314]     Public IPv4  : 10.8.172.154
	2016-12-02 16:27:09 INFO [paws.util.log_resources:316]     Username     : Administrator
	2016-12-02 16:27:09 INFO [paws.util.log_resources:317]     Password     : my_password@2016
	2016-12-02 16:27:09 INFO [paws.util.log_resources:319] *********************************************
	2016-12-02 16:27:09 INFO [paws.tasks.show.post_tasks:130] END: Show, TIME: 0h:0m:2s
	2016-12-02 16:27:09 INFO [paws.main:94] End paws execution in 0h:0m:3s

**No active instance.**

.. code:: bash

	[ecerquei@dev paws]$ paws show
	2016-12-02 15:45:02 INFO Begin paws execution
	2016-12-02 15:45:02 INFO START: Show
	2016-12-02 15:45:02 INFO Openstack providers credentials are set by a credentials file.
	2016-12-02 15:45:05 INFO *********************************************
	2016-12-02 15:45:05 WARNING Nothing to show, did you try provision?
	2016-12-02 15:45:05 INFO *********************************************
	2016-12-02 15:45:05 INFO END: Show, TIME: 0h:0m:3s
	2016-12-02 15:45:05 INFO End paws execution in 0h:0m:3s

**No active instance running in verbose mode.**

.. code:: bash

	[ecerquei@dev paws]$ paws show -v
	2016-12-02 15:54:47 INFO [paws.main:53] Begin paws execution
	2016-12-02 15:54:47 DEBUG [paws.main:54] *********************************************
	2016-12-02 15:54:47 DEBUG [paws.main:55]                 Paws arguments
	2016-12-02 15:54:47 DEBUG [paws.main:56] *********************************************
	2016-12-02 15:54:47 DEBUG [paws.main:59] task: show
	2016-12-02 15:54:47 DEBUG [paws.main:59] verbose: 2
	2016-12-02 15:54:47 DEBUG [paws.main:59] userdir: /usr/share/paws
	2016-12-02 15:54:47 DEBUG [paws.main:59] credentials: credentials.yaml
	2016-12-02 15:54:47 DEBUG [paws.main:59] topology: resources.yaml
	2016-12-02 15:54:47 DEBUG [paws.main:60] *********************************************
	2016-12-02 15:54:47 INFO [paws.tasks.show.run:74] START: Show
	2016-12-02 15:54:47 DEBUG [paws.providers.openstack.get_credentials:215] Getting Openstack credentials.
	2016-12-02 15:54:47 INFO [paws.providers.openstack.get_credentials:231] Openstack providers credentials are set by a credentials file.
	2016-12-02 15:54:47 DEBUG [paws.providers.openstack.create:641] Playbook /usr/share/paws/.get_ops_facts.yaml created.
	2016-12-02 15:54:47 DEBUG [paws.remote.driver.run_playbook:241] Running Ansible Playbook /usr/share/paws/.get_ops_facts.yaml
	2016-12-02 15:54:51 DEBUG [paws.remote.results.msg:59] Ansible call executed successfully!
	2016-12-02 15:54:51 DEBUG [paws.providers.openstack.generate_resources_paws:284] Generating /usr/share/paws/resources.paws
	2016-12-02 15:54:51 INFO [paws.util.log_resources:297] *********************************************
	2016-12-02 15:54:51 WARNING [paws.util.log_resources:298] Nothing to show, did you try provision?
	2016-12-02 15:54:51 INFO [paws.util.log_resources:299] *********************************************
	2016-12-02 15:54:51 INFO [paws.tasks.show.post_tasks:130] END: Show, TIME: 0h:0m:3s
	2016-12-02 15:54:51 INFO [paws.main:94] End paws execution in 0h:0m:4s

.. Note::
	The credentials **username and password** from your Windows system
	provisioned is displayed at the console output.

	As we think Paws is a tool to simplify your access to Windows systems. We
	thought it would be okay to show the username and password for a system. We
	felt it was not a big security issue because the system is not to be run in
	any production application only for testing purposes.

	Maybe you have a use case that you need a Windows machine for a single
	task (just to access via RDP - remote desktop protocol) and then teardown
	the system. It would be nice to have all this information that you need to
	access the machine after provisioned. Instead of having to navigate
	through files to find the login information.

 .. code:: bash

	*********************************************
	            System Resources (show)
	*********************************************
	 1.
	     Name         : PAWS_eduardo
	     Public IPv4  : 10.8.172.154
	     Username     : Administrator
	     Password     : my_password@2016
	*********************************************

 If you find it not acceptable to display this username for security or
 critical types of test. Please contact the maintainers of paws and we can
 implement a parameter to show this information or not. Feel free to send
 a code patch to our gerrit as well.
