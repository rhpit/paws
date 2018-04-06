Configure
---------

**DESCRIPTION**

Configure task will perform configuration on Windows systems by running either
an Ansible playbook or Windows PowerShell scripts.

**ARGUMENTS**

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Argument
        - Default
        - Required
        - Description

    *   - [SCRIPT]
        -
        - Yes
        - Playbook or PowerShell script to execute

    *   - -t, --topology
        - resources.yaml
        - Yes
        - System resources definition

    *   - -sv, --script_vars
        -
        - No
        - Playbook or PowerShell script variables

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

    # configure via ansible playbook with no input variables
    paws configure ansible/task01.yml

    # configure via ansible playbook with input variables (format=file)
    paws configure ansible/task01.yml -sv ansible/my_vars.json

    # configure via ansible playbook with input variables (format=string)
    paws configure ansible/task01.yml -sv "{'key01': ['value01', 'value02']}"

    # configure via windows powershell script with no input variables
    paws configure powershell/task01.ps1

    # configure via windows powershell script with input varaibles (format=file)
    paws configure powershell/task01.ps1 -sv powershell/my_vars.json

    # configure via windows powershell script with input variables (format=string)
    paws configure powershell/task01.ps1 -sv "-command upgrade -packages @('python2')"
