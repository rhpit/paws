Group
-----

**DESCRIPTION**

Group task gives users the ability to bulk multiple paws task calls into a
single paws call.

**ARGUMENTS**

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Argument
        - Default
        - Required
        - Description

    *   - -ud, --userdir
        - /home/$USER/ws
        - YES
        - User directory

    *   - -n, --name
        -
        - Yes
        - Group template filename

    *   - -h, --help
        -
        - No
        - Enable to show help menu


**EXAMPLES**

.. code-block:: bash

    # group using default options and setting group file
    paws group -n group/my_group.yaml

    # group overriding user directory
    paws -ud /tmp/ws group -n group/my_group.yaml

    # show help menu
    paws group --help

**OUTPUT**

Group output will be the same as all other paws tasks just combined.

.. note::
	To learn how to create a group visit the following: `Create group file
	<create_group.html>`_.
