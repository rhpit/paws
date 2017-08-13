Windows PowerShell
==================

PowerShell (including Windows PowerShell and PowerShell Core) [1]_ *is a task
automation and configuration management framework from Microsoft, consisting
of a command-line shell and associated scripting language built on the
.NET Framework.*

Why PowerShell?
---------------

PowerShell is the native script language for Microsoft Operating Systems.

* PowerShell gives us access to a large number of MS libraries, making scripts
  easy to interact with MS components and features.
* PowerShell can interact with a dizzying number of technologies.
* PowerShell is object-based.
* PowerShell can help anyone working in the Microsoft ecosystem.

[2]_ *Windows PowerShell is a shell developed by Microsoft for purposes of task
automation and configuration management. This powerful shell is based on the
.NET framework and it includes a command-line shell and a scripting language.
On top of the standard command-line shell, you can also find the Windows
PowerShell ISE*

.. _ws:

PAWS and PowerShell [ws]
------------------------

PAWS uses PowerShell scripts to install, configure and perform any change in a
Windows previously provisioned.

WS **Windows Scripts** is a git repo to store PowerShell scripts to be used
during PAWS execution.

Everybody can use this repository and the idea is to use this a
**centralized place** that people can re-use scripts already developed and
contribute to expand for others use cases.

**WS REPO URL:** https://github.com/rhpit/ws

We strongly recommend cloning this repository to your user directory 
**/home/$USER/paws**

**powershell:** We currently have some PowerShell scripts that you can
start using with paws and more can be found here [3]_.

**group:** A group may have one or more PowerShell script calls. Groups allow
you to build and share your Windows pipeline. You can see more about groups at
`group task <create_group.html>`_.

Users can use all these scripts provided to run winsetup or group tasks. Users
can pull or push their scripts/groups to this repository.


References
----------
.. [1] https://en.wikipedia.org/wiki/PowerShell

.. [2] http://www.digitalcitizen.life/simple-questions-what-powershell-what-can-you-do-it

.. [3] https://www.powershellgallery.com

