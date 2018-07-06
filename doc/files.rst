Files
=====

This document will explain in more detail about files used by paws.

ansible.cfg
-----------

Paws creates an Ansible configuration file stored at the default user
directory **/home/$USER/paws** to be used when run. This file will not have
Ansible generate playbook **.retry** files. 

Since this file lives in the user directory, you can modify Ansible settings 
if you wish. Please be aware if you change settings not supported by paws, 
you could see potential failures.

See Ansible doc for more information about .retry at 
http://docs.ansible.com/ansible/latest/intro_configuration.html#retry-files-enabled

----

credentials.yaml
----------------

Dictionary of your providers credentials.

.. hint::
	For Openstack as provider, you can use Openstack system environment
	variables instead of the credentials.yaml file. The physical
	credentials.yaml file is the primary source. If you are using system
	environments but still have credentials.yaml in your paws user directory,
	paws will use the file. For Openstack provider you can use Openstack
	system environment variables

	Check Openstack FAQ to see where to get and how to use  Openstack system 
	environment variables https://docs.openstack.org/keystone/latest/install/keystone-openrc.html

Example credentials.yaml:

.. code:: yaml

   credentials
      - provider: openstack
        os_auth_url: http://10.10.10.10:5000/v2.0
        os_username: username
        os_password: password
        os_project_name: tenant

.. note::

 see `Openstack provider <providers.html#Openstack>`_ for fields definition

 see `Libvirt provider <providers.html#Libvirt>`_ for fields definition

----

resources.yaml
--------------

A list of resources that you would like to provision.

Example resources.yaml for Openstack provider:

.. code:: yaml

   resources:
      - name: MY_WINDOWS_VM
        count: 1
        image: win-2012-r2
        flavor: 4
        network: network_name
        keypair: my_key_pair
        ssh_private_key: /home/user/.ssh/id_rsa
        administrator_password: my_password@2016
        provision_attempts: 30

.. note::

 see `Openstack provider <providers.html#Openstack>`_ for fields definition

 see `Libvirt provider <providers.html#Libvirt>`_ for fields definition


----

resources.paws
--------------

A list of resources that have been provisioned by provision task. This
file will be generated when provision task is finished. It is stored under the
users directory.

Example resources.paws:

.. code:: yaml

   resources:
      - name: windows_2012_server
        public_v4: 10.8.174.162
        private_v4: 172.16.5.194
        ssh_key_file: /home/user/.ssh/id_rsa
        keypair: my_key_pair
        id: 79f0dd24-28f0-45e1-b560-a299767fa969
        win_password: my_password@2016
        win_username: Administrator

.. note::
	**- name:** The name of the instance created in Openstack.

	**- public_v4:** The public IPv4 address.

	**- private_v4:** The private (internal) IPv4 address.

	**- ssh_key_file:** The SSH private key to login to the system via SSH.

	**- keypair:** They key pair associated with the instance when created.

	**- id:** The ID of the instance running in Openstack.

	**- win_password:** The password to login to your instance. This can be
	used by SSH or RDP (Remote Desktop Protocol).

	**- win_username:** The username to login to your instance. This can be
	used by SSH or RDP (Remote Desktop Protocol).

----

powershell files
----------------

For more information about PowerShell scripts can be found here:
`PowerShell <powershell.html#ws>`_.

----

group files
-----------

For more information about groups can be found here:
`group <create_group.html>`_.

.. tip::
	Files under powershell or group directories can be modified by your need.
	These are just base templates to help get you started with paws.
