Teardown
--------

**DESCRIPTION**

Teardown task will teardown system resources in your supplied provider. It will
teardown the resources you have defined inside your resources.yaml if they are
active instances.

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

    # teardown using default options
    paws teardown

    # teardown using default options with verbose logging
    paws -v teardown

    # teardown overriding user directory
    paws -ud /tmp/ws teardown

    # show help menu
    paws teardown --help
