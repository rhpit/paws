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

**OUTPUT**

Here is an example of PowerShell output when run by paws.

.. code-block:: bash

	2016-12-13 20:57:44 INFO [paws.remote.driver.run_playbook:243] PowerShell script to be run /usr/share/paws/powershell/get_system_info.ps1
	2016-12-13 20:57:44 INFO [paws.remote.driver.run_playbook:248] *********************************************
	2016-12-13 20:57:44 INFO [paws.remote.driver.run_playbook:249] PLEASE WAIT WHILE ANSIBLE PLAYBOOK IS RUNNING
	2016-12-13 20:57:44 INFO [paws.remote.driver.run_playbook:250] This could take several minutes to complete.
	2016-12-13 20:57:44 INFO [paws.remote.driver.run_playbook:251] *********************************************
	2016-12-13 20:57:51 INFO [paws.remote.results.process:99] ---------------
	2016-12-13 20:57:51 INFO [paws.remote.results.process:100] Results
	2016-12-13 20:57:51 INFO [paws.remote.results.process:101] ---------------
	2016-12-13 20:57:51 INFO [paws.remote.results.process:109] ** 10.8.173.232 **
	2016-12-13 20:57:51 INFO [paws.remote.results.process:113] Standard output:
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] 12/13/2016 20:57:44 - get_system_info.ps1 - Starting get_system_info.ps1
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Status                                    : OK
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Name                                      : Microsoft Windows Server 2012 R2 St
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115]                                             andard|C:\windows|\Device\Harddisk0
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115]                                             \Partition1
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] FreePhysicalMemory                        : 7776952
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] FreeSpaceInPagingFiles                    : 1310720
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] FreeVirtualMemory                         : 9117784
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Caption                                   : Microsoft Windows Server 2012 R2 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115]                                             Standard
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Description                               : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] InstallDate                               : 12/13/2016 8:56:15 PM
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CreationClassName                         : Win32_OperatingSystem
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CSCreationClassName                       : Win32_ComputerSystem
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CSName                                    : CI-PAWS-WIN-201
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CurrentTimeZone                           : 0
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Distributed                               : False
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] LastBootUpTime                            : 12/13/2016 8:55:44 PM
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] LocalDateTime                             : 12/13/2016 8:57:44 PM
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] MaxNumberOfProcesses                      : 4294967295
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] MaxProcessMemorySize                      : 137438953344
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] NumberOfLicensedUsers                     : 0
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] NumberOfProcesses                         : 36
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] NumberOfUsers                             : 2
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] OSType                                    : 18
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] OtherTypeDescription                      : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] SizeStoredInPagingFiles                   : 1310720
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] TotalSwapSpaceSize                        : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] TotalVirtualMemorySize                    : 9698800
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] TotalVisibleMemorySize                    : 8388080
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Version                                   : 6.3.9600
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] BootDevice                                : \Device\HarddiskVolume1
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] BuildNumber                               : 9600
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] BuildType                                 : Multiprocessor Free
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CodeSet                                   : 1252
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CountryCode                               : 1
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CSDVersion                                : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] DataExecutionPrevention_32BitApplications : True
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] DataExecutionPrevention_Available         : True
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] DataExecutionPrevention_Drivers           : True
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] DataExecutionPrevention_SupportPolicy     : 3
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Debug                                     : False
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] EncryptionLevel                           : 256
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] ForegroundApplicationBoost                : 2
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] LargeSystemCache                          : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Locale                                    : 0409
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Manufacturer                              : Microsoft Corporation
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] MUILanguages                              : {en-US}
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] OperatingSystemSKU                        : 7
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Organization                              : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] OSArchitecture                            : 64-bit
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] OSLanguage                                : 1033
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] OSProductSuite                            : 272
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] PAEEnabled                                : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] PlusProductID                             : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] PlusVersionNumber                         : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] PortableOperatingSystem                   : False
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] Primary                                   : True
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] ProductType                               : 3
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] RegisteredUser                            : Windows User
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] SerialNumber                              : 00252-00055-00001-AA028
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] ServicePackMajorVersion                   : 0
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] ServicePackMinorVersion                   : 0
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] SuiteMask                                 : 272
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] SystemDevice                              : \Device\HarddiskVolume1
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] SystemDirectory                           : C:\windows\system32
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] SystemDrive                               : C:
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] WindowsDirectory                          : C:\windows
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] PSComputerName                            : 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CimClass                                  : root/cimv2:Win32_OperatingSystem
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CimInstanceProperties                     : {Caption, Description, 
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115]                                             InstallDate, Name...}
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115] CimSystemProperties                       : Microsoft.Management.Infrastructure
	2016-12-13 20:57:51 INFO [paws.remote.results.process:115]                                             .CimSystemProperties