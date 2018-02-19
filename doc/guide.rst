Getting Started
===============

Prerequisites
-------------

Clone a local copy of the `ws repository <https://github.com/rhpit/ws.git>`_.
This will provide you with paws files for getting started.

.. code-block:: bash
    :linenos:

    cd ~ && git clone https://github.com/rhpit/ws.git

.. important::

    We recommend storing the ws repo within your users home directory. By
    default paws will look for a ws directory at /home/$USER/ws to load files.
    You can always override this by defining **-ud** option at runtime.

    We strongly recommend that you read about `paws files <files.html>`_.

How To Run
----------

To run paws, just issue the following command in a terminal.

.. code-block:: bash
    :linenos:

    paws

You can view more about each paws task by providing the help option.

.. code-block:: bash
    :linenos:

    paws <task> --help

Provision
^^^^^^^^^

Provision task will provision Windows systems in their given provider defined.

You can find more details about configuring your providers credentials at the
following: `provider credentials <files.html#credentials-yaml>`_.

You will want to modify the **resources.yaml** file within your local copy
of ws repository stored within your user directory folder path.

.. code:: yaml

    resources:
        - name: windows
          provider: openstack
          count: 1
          image: win-2016-serverstandard-x86_64-released
          flavor: m1.xlarge
          network: 192.168.1.0
          keypair: keypair
          ssh_private_key: /home/user/.ssh/id_rsa
          administrator_password: my_password@2018

You can find more details about configuring your resources file at the
following: `resources.yaml <files.html#resources-yaml>`_.

Once your files are set, go ahead and call paws provision task. Shortly you
should have your Windows system provisioned and ready for use!

.. code-block:: bash
    :linenos:

    paws provision

.. note::

    More details about provision task can be found at the following:
    `provision task <tasks.html#provision>`_.

Teardown
^^^^^^^^

Teardown task will teardown Windows systems in their given provider defined.
It requires both files (**credentials.yaml** & **resources.yaml**) which were
used in provision task. These files define provider credentials and which
systems to delete.

Once your files are set, go ahead and call paws teardown task. Shortly you
should see your Windows systems deleted.

.. code-block:: bash
    :linenos:

    paws teardown

.. note::

    More details about teardown task can be found at the following:
    `teardown task <tasks.html#teardown>`_.

Winsetup
^^^^^^^^

Winsetup task will configure services on a Windows system by running a
Windows PowerShell script.

At top of this page you saw how to clone `ws repository
<https://github.com/rhpit/ws.git>`_ repo that contains some samples of
powershell and scripts you can use here.

Example powershell scripts can be found at the following:
**/home/$USER/ws/powershell**.

Below is an example calling a powershell script to list system information
for the defined resources within **resources.yaml**.

.. code-block:: bash
    :linenos:

    paws winsetup -ps powershell/get_system_info.ps1

.. note::

    More details about winsetup task can be found at the following:
    `winsetup task <tasks.html#winsetup>`_.

Group
^^^^^

Group task will run multiple paws commands as one command. A group is a YAML
file which defines a list of paws tasks to run.

Example group files can be found at the following: **/home/$USER/ws/group**.

Below is an example calling a paws group file to configure a 2012 Windows
Active Directory server.

.. code-block:: bash
    :linenos:

    paws group -n group/2012_winad.yaml

.. note::

    More details about group task can be found at the following:
    `group task <tasks.html#group>`_.

Show
^^^^

Show task will display system resources based on what is defined within your
**resources.yaml** file. Show is helpful when you may have forgotten the
password for a defined Windows resource.

Below is an example calling paws show to view system resources/details.

.. code-block:: bash
    :linenos:

    paws show

.. note::

    More details about show task can be found at the following:
    `show task <tasks.html#show>`_.
