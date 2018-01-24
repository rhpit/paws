Provision
---------

**DESCRIPTION**

Provision task will provision system resources in your provider that you have
defined inside resources.yaml. If something unexpected happens during
provisioning. Paws will invoke the teardown task automatically.

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

    # provision using default options
    paws provision

    # provision using default options with verbose logging
    paws -v provision

    # provision overriding user directory
    paws provision -ud /tmp/ws

    # show help menu
    paws provision --help

**OUTPUT**

Here is an example output at the end of provision task.

.. code-block:: bash

	2016-12-15 20:32:22 INFO *********************************************
	2016-12-15 20:32:22 INFO         System Resources (provisioned)       
	2016-12-15 20:32:22 INFO *********************************************
	2016-12-15 20:32:22 INFO 1.
	2016-12-15 20:32:22 INFO     Name         : ryan_windows
	2016-12-15 20:32:22 INFO     Public IPv4  : 10.8.175.135
	2016-12-15 20:32:22 INFO     Username     : Admin
	2016-12-15 20:32:22 INFO     Password     : rBFXHL6eiuHOcGnQBiK9
	2016-12-15 20:32:22 INFO *********************************************
	2016-12-15 20:32:22 INFO END: Provision, TIME: 0h:0m:10s
	2016-12-15 20:32:22 INFO End paws execution in 0h:0m:14s


.. note::
	When the provision task is finished you will find a resources.paws file
	located within your user directory. This contains information about the
	system provisioned.

   .. code:: yaml

      resources:
         - name: windows_2012_server
           public_v4: 10.8.174.162
           private_v4: 172.16.5.184
           ssh_key_file: /home/user/.ssh/id_rsa
           keypair: my_key_pair
           id: 79f0dd24-28f0-45e1-b560-a299767fa969
           win_password: my_password@2016
           win_username: Administrator
