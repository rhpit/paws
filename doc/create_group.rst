Groups
======

This document will explain what a group is, the file structure of a group and
how you can create your own group.

What is a group?
----------------
A group is an easy way to bulk multiple single paws calls into one call.

What is the structure of a group?
---------------------------------

A group file is a YAML formatted file which contains three sections:
**Header**, **Vars** and **Tasks**.

Before starting group execution PAWS performs a data validation in a group yaml
file. The first part of validation is to check file schema that must contains
all basic elements header, vars and tasks. The second part is to check data
declared. At this current version PAWS runs regular expression match as
showed below:

.. code:: json

	# regular expressions to validate content of group yaml file
	GROUP_REQUIRED = {
	    'header': [
	        {'name': '.*.'},
	        {'description': '.*.'},
	        {'maintainer': "[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"}],
	    'vars': [{'topology': '(.*.yaml)$|(.*.yml)$'}]}

Header
++++++

The header section contains general information about the group. This
information isn't used directly when calling paws but is helpful when someone
wants to use your group within their testing environment.

The header section is in format of a dictionary. You will need to declare the
following keys:


| **name**: Name of the group.
| Required: True
| Type: String
| Validation: Must contains at least one string. Multi-line is allowed

| **description**: A short description what the group is doing.
| Required: True
| Type: String
| Validation: Must contains at least one string. Multi-line is allowed

| **maintainer**: The email address for the maintainer of the group.
| Required: True
| Type: String
| Validation: email address format

Here is an example of a header section:

.. code:: yaml

   group:
      - header:
        name: Windows server 2012 Active Directory group
        description: Provision and configure Windows vm for AD
        maintainer: rwilliams5262@gmail.com

Vars
++++

The vars section contains common options used throughout all tasks you want
to run.

| **credentials**: which defines the credentials filename.
| Required: False
| Type: String
| Validation: As optional field it doesn't have any validation.
| Notes: For Openstack provider you can use environmet system variable as
 credentials so you can skip credentials attribute in your group file. The same
 won't work if you want to use Libvirt as provider.

| **topology**: which defines the topology file to be used. This is the file
 which contains your systems you would like to provision or are already
 provisioned.
| Required: True
| Type: String
| Validation: any file must ends with .yaml or .yml

These keys can come from any of the options a task has available. Mostly you
will see options such as (user directory, credentails, topology) defined here.
All others will be defined by each specific task.

Example of a vars section:

.. code:: yaml

   group:
      - vars:
        credentials: credentials.yaml
        topology: resources.yaml

Tasks
+++++

The tasks section is the main part to a group. This is where you will define
all the tasks you want to run. The order that you define your tasks is the
order that paws will execute them.

Each task is in the format of a dictionary. You will need to declare the
following keys:

| **name**: Name of the task.
| Required: True
| Type: String
| Validation: none

| **task**: Name of the paws task to call.
| Required: True
| Type: String
| Validation: None

| **args**: Options that you would like to pass to that task.
| Required: False
| Type: dict
| Validation: None

Here is an example of a tasks section:

.. code:: yaml

   group:
      - tasks:
         - name: Provision Windows
           task: provision

         - name: Get Windows system information
           task: configure
           args:
            - script: powershell/get_system_info.ps1

         - name: Reboot Windows
           task: configure
           args:
            - script: powershell/reboot.ps1

As you can see we have declared three tasks to run:

1. First it will run the provision task to create a Windows system based on
   the system defined in the topology file set in the vars section.

2. Second it will run the configure task. It will execute the script that
   was specified.

3. Third it will run the configure task again. This will run the reboot.ps1
   PowerShell script to reboot the system.

Example of a group
------------------

.. code:: yaml

   group:
      - header:
        name: Display Windows system information
        description: Provision Windows system and display system information
        maintainer: rwilliams5262@gmail.com

      - vars:
        credentials: credentials.yaml
        topology: resources.yaml

      - tasks:
         - name: Provision Windows
           task: provision

         - name: Get Windows system information
           task: configure
           args:
            - script: powershell/get_system_info.ps1

         - name: Reboot Windows
           task: configure
           args:
            - script: powershell/reboot.ps1

Paws version 0.3.6 supports multiple resources. This means that you can
define multiple resources inside your resources.yaml and then configure them.
By default configure task will run PowerShell scripts on all resources defined
inside resources.yaml. If you want to set only a certain system to run the
PowerShell against you can pass the --system argument. This goes the same for
groups. The system name you give must match the one inside your resources.yaml.
Below is an example of running a task only on a certain system.

Example of a group with multiple resources
------------------------------------------

.. code:: yaml

   group:
      - header:
        name: Display Windows system information
        description: Provision Windows system and display system information
        maintainer: rwilliams5262@gmail.com

      - vars:
        credentials: credentials.yaml
        topology: resources.yaml

      - tasks:
         - name: Provision Windows
           task: provision

         - name: Get Windows system information
           task: configure
           args:
            - script: powershell/get_system_info.ps1
            - system:
              - windows2012

         - name: Reboot Windows
           task: configure
           args:
            - script: powershell/reboot.ps1

How you can create your own group?
----------------------------------

Now that you understand the three sections to a group and what they offer.
You can easily begin creating your own groups! Please feel free to use the
default group templates as a starting point and expand from there!

.. attention::

	One thing to note is if your group contains a number of configure tasks. You
	will need to keep all the PowerShell scripts and necessary variable files
	stored within your user directory where your group file is located.

	If you want to share your group file with someone else to use, you will
	need to provide them with all files: group, PowerShells, etc.

	When installing Windows features, some might require a reboot in order to
	take effect. If you issue the reboot PowerShell script and go to run
	another PowerShell script right after. It might fail because the system is
	going to go down. In order to handle these paws group offers a feature
	called **wait**. Wait is very simple: it will wait a duration that you
	specify. Lets look at the following example:

   .. code:: yaml

      - tasks:
         - name: Windows preparation
           task: configure
           args:
            - script: powershell/2012_ad_preparation.ps1
            - script_vars: powershell/my_vars.json

         - name: Reboot Windows
           task: configure
           args:
            - script: powershell/reboot.ps1

         - name: Wait for Windows to come back online
           task: wait
           duration: 30

         - name: Windows setup step 1
           task: configure
           args:
            - script: powershell/ad_setup_step1.ps1
            - script_vars: powershell/my_vars.json

	As you can see the wait is given after the reboot and will wait 30 seconds
	before running the next task in the list. This allows users to easily
	customize their workflow.
