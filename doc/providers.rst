Providers
==========

The definition of **provider** for PAWS is the location where the Windows will
be provisioned and managed by PAWS. it is the list of providers supported:


* `Openstack provider <providers.html#openstack>`_

* `Libvirt provider <providers.html#libvirt>`_


Openstack
---------

http://www.openstack.org

PAWS is integrated with Openstack and able to provision, configure and manage
Windows virtual machines running on public or private clouds.

Path: /usr/share/paws/credentials.yaml

.. code:: yaml

	credentials:
	  - provider: openstack
	    os_auth_url: http://dashboard.centralci.eng.rdu2.redhat.com:5000/v2.0
	    os_username: paws
	    os_password: ********
	    os_project_name: paws


+------------------+------------------------+------------------------+
|    Field name    |      Description       |         Value          |
+==================+========================+========================+
| provider         | name of provider where |   openstack, libvirt   |
|                  | your Windows system    |                        |
|                  | will live              |                        |
+------------------+------------------------+------------------------+
| os_auth_url      | OpenStack URL/port for | HTTP URL see in file   |
|                  | authentication         | above to use OSP7      |
+------------------+------------------------+------------------------+
| os_username      | Username to login to   | tenant username        |
|                  | OpenStack tenant       |                        |
+------------------+------------------------+------------------------+
| os_password      | Password to login to   | tenant password        |
|                  | OpenStack tenant       |                        |
+------------------+------------------------+------------------------+
| os_project_name  | Name of the OpenStack  | tenant or project      |
|                  | tenant or project      |                        |
+------------------+------------------------+------------------------+


Path: /usr/share/paws/resources.yaml

.. code:: yaml

	resources:
	- name: PAWS_WIN2012_R2
	  provider: openstack
	  count: 2
	  image: win-2012-r2
	  flavor: 4
	  network: 10.8.172.0/22
	  keypair: paws
	  ssh_private_key: /home/ecerquei/.ssh/paws
	  administrator_password: my_password@2016

*PS: resources accepts multiple resources definition.*

+------------------------+-----------------------------------+-------------+
|    Field name          |      Description                  |  Required   |
+========================+===================================+=============+
| name                   | The name that will be given when  |      Yes    |
|                        | the instance is provisioned       |             |
|                        | (Openstack sets this as the       |             |
|                        | instance name). When count > 1    |             |
|                        | during provisioning the instance  |             |
|                        | name will be automatically        |             |
|                        | appended with sequential numbers. |             |
+------------------------+-----------------------------------+-------------+
| provider               | provider name to use              |      Yes    |
+------------------------+-----------------------------------+-------------+
| count                  | The number of identical resources |      Yes    |
|                        | to create. This count only applies|             |
|                        | to each specific resource section.|             |
|                        | It does not apply to all resources|             |
|                        | in the file.                      |             |
+------------------------+-----------------------------------+-------------+
| image                  | The name of the image to be used  |      Yes    |
|                        | to create the instance. The       |             |
|                        | Windows image should exist and    |             |
|                        | your provider account must have   |             |
|                        | permission to use it.             |             |
|                        | *Check Openstack in FAQ to see*   |             |
|                        | *how you can get the full list of*|             |
|                        | *current Windows images in your*  |             |
|                        | *Openstack provider*              |             |
+------------------------+-----------------------------------+-------------+
| flavor                 | The flavor name or ID which should|      Yes    |
|                        | be used when creating the new     |             |
|                        | instance                          |             |
|                        | *Check Openstack FAQ to see how*  |             |
|                        | *you can get the full list of*    |             |
|                        | *current Windows flavors in your* |             |
|                        | *Openstack provider*              |             |
+------------------------+-----------------------------------+-------------+
| network                | The name or ID of a network to    |      Yes    |
|                        | attach this instance to. This     |             |
|                        | network will provide the floating |             |
|                        | IP to your instance. You will want|             |
|                        | to supply the external network    |             |
|                        | name as your network if it has a  |             |
|                        | router connecting it to an        |             |
|                        | internal network.                 |             |
+------------------------+-----------------------------------+-------------+
| keypair                | The key pair name to be used when |      Yes    |
|                        | creating an instance              |             |
+------------------------+-----------------------------------+-------------+
| ssh_private_key        | Absolute path from your host      |      Yes    |
|                        | machine to the SSH private key to |             |
|                        | login to system via SSH           |             |
+------------------------+-----------------------------------+-------------+
| administrator_password | The administrator password to set |      No     |
|                        | on the Windows system after       |             |
|                        | provisioning has finished         |             |
|                        | *If you do not want to set an*    |             |
|                        | *administrator password initially*|             |
|                        | *you can remove this key from*    |             |
|                        | *your resource section. It will*  |             |
|                        | *then use the Admin account to*   |             |
|                        | *login to the system via SSH*     |             |
+------------------------+-----------------------------------+-------------+
| snapshot               | Take a snapshot for a given       |      No     |
|                        | resource. You can define a list of|             |
|                        | tasks when to take a snapshot     |             |
+------------------------+-----------------------------------+-------------+

.. note::
	**- snapshot:** Take a snapshot for a given resource. You can define a
	list of tasks when to take a snapshot.

	.. code:: yaml

	   # Example 1: Create snapshot & clean old server snapshots
	   resources:
	      - name: MY_WINDOWS_VM
	        snapshot:
	          - task: teardown

	The resource above will take a snapshot and clean any old snapshots
	created for this VM (MY_WINDOWS_VM) during teardown task. The default
	behavior is when you give a list of tasks to create snapshots it will
	always create the snapshot and clean old snapshots. To override this
	please see the following example:

	.. code:: yaml

	   # Example 2: Create snapshot & do not clean old server snapshots
	   resources:
	      - name: MY_WINDOWS_VM
	        snapshot:
	          - task: teardown
	            clean: False

	This resource will take a snapshot and will not clean old snapshots
	created by paws for this server.


Libvirt
-------

http://www.libvirt.org

PAWS is integrated with Libvirt and able to provision, configure and manage
Windows virtual machines running locally.

To run PAWS with libvirt you need to create **credentials.yaml** and
**resources.yaml** see below details for these two files and a sample.

To configure your machine to run PAWS with libvirt follow
the section `Running Windows on VM <libvirt.html>`_

path: /usr/share/paws/credentials.yaml

.. code:: yaml

	credentials:
	  - provider: libvirt
	    qemu_instance: qemu:///system
	    imgsrv_url: http://imgsrv.usersys.redhat.com


+------------------+------------------------+----------------------------------+
|    Field name    |      Description       |         Value                    |
+==================+========================+==================================+
| provider         | name of provider where |   openstack, libvirt             |
|                  | your Windows system    |                                  |
|                  | will live              |                                  |
+------------------+------------------------+----------------------------------+
| qemu_instance    | specify the instance   | system, session                  |
|                  | for QEMU driver to use | for more information             |
|                  |                        | https://libvirt.org/drvqemu.html |
+------------------+------------------------+----------------------------------+
| imgsrv_url       | URL to retrieve the    | http://imgsrv.usersys.redhat.com |
|                  | pre-configured Windows | or for dev purpose, if running   |
|                  | image for Libvirt      | IMGSRV locally you can use       |
|                  |                        | http://127.0.0.1:5000            |
+------------------+------------------------+----------------------------------+


path: /usr/share/paws/resources.yaml

.. code:: yaml

	resources:
	  - name: PAWS_WIN2012_R2
	    provider: libvirt
	    memory: 4000
	    vcpu: 1
	    disk_source: /home/user/Downloads/windows_2012_R2.qcow
	    win_username: Administrator
	    win_password: my_password@2016



+------------------------+-----------------------------------+-------------+
|    Field name          |      Description                  |  Required   |
+========================+===================================+=============+
| name                   | The name that will be given when  |      Yes    |
|                        | the instance is provisioned       |             |
+------------------------+-----------------------------------+-------------+
| provider               | provider name to use              |      Yes    |
+------------------------+-----------------------------------+-------------+
| memory                 | The amount of memory you want to  |      Yes    |
|                        | set for the new virtual machine   |             |
|                        | that will be provisioned          |             |
|                        | *must be in MB*                   |             |
+------------------------+-----------------------------------+-------------+
| vcpu                   | The number of virtual CPU you want|      Yes    |
|                        | to allocate for the new virtual   |             |
|                        | machine                           |             |
+------------------------+-----------------------------------+-------------+
| disk_source            | The location in your local machine|      Yes    |
|                        | where the pre-configured Windows  |             |
|                        | image will be saved. This file is |             |
|                        | the storage drive for your virtual|             |
|                        | machine                           |             |
+------------------------+-----------------------------------+-------------+
| win_username           | the username pre-configured in the|      Yes    |
|                        | Windows image. You get this from  |             |
|                        | IMGSRV                            |             |
+------------------------+-----------------------------------+-------------+
| win_password           | the password pre-configured in the|      Yes    |
|                        | Windows image. You get this from  |             |
|                        | IMGSRV                            |             |
+------------------------+-----------------------------------+-------------+

