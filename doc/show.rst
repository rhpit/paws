Show
----

**DESCRIPTION**

Show task will display system resources in your supplied provider. It
assumes the `provision task <guide.html#provision>`_ was called previously and
your system resource was successfully provisioned. If show does not find any
system resources in your supplied provider. A warning message will be
displayed instead.

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

    # show windows systems using default options
    paws show

    # show using default options with verbose logging
    paws -v show

    # show overriding user directory
    paws -ud /tmp/ws show

    # show help menu
    paws show --help
