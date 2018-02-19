Winsetup
--------

**DESCRIPTION**

Winsetup task will perform configuration on Windows systems by running a
Windows PowerShell script supplied by parameter input.

**ARGUMENTS**

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Argument
        - Default
        - Required
        - Description

    *   - -t, --topology
        - resources.yaml
        - Yes
        - System resources definition

    *   - -ps, --powershell
        -
        - Yes
        - PowerShell script to run

    *   - -psv, --powershell_vars
        -
        - No
        - PowerShell variables

    *   - -s, --system
        - All system resources
        - No
        - Systems to configure

    *   - -h, --help
        -
        - No
        - Enable to show help menu

**EXAMPLES**

.. code-block:: bash
    :linenos:

    # winsetup using default options and setting powershell
    paws winsetup -ps powershell/my_ps.ps1

    # winsetup using default options, set powershell and enable verbose logging
    paws -v winsetup -ps powershell/my_ps.ps1

    # winsetup overriding user directory and giving powershell vars file
    paws winsetup -ud /tmp/ws -ps powershell/my_ps.ps1 -psv powershell/vars.json

    # winsetup giving set of systems to run powershell against
    paws winsetup -ps powershell/my_ps.ps1 -s win2012_1

    # winsetup setting powershell vars non file form
    paws winsetup -ps powershell/set_uac.ps1 -psv '-uacValue 0'

    # show help menu
    paws winsetup --help
