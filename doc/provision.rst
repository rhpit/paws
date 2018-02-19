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

.. note::

    One completion, you will find a new file **resources.paws** stored within
    your user directory. This file contains updated information for the
    system resource provisioned.

    .. code-block:: yaml

      resources:
         - name: windows_server_01
           public_v4: 192.168.0.1
           private_v4: 127.0.0.1
           ssh_key_file: /home/$USER/.ssh/id_rsa
           keypair: my_key_pair
           id: 79f0dd24-28f0-45e1-b560-a299767fa969
           win_password: my_password@2018
           win_username: Administrator
