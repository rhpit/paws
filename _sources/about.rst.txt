
.. image:: _static/paws_highlevel_2.png
	:width: 60%
	:align: center

Provision Automated Windows and Services
----------------------------------------

A linux based tool focused on simplifying the process to provision Windows
systems and configure Windows services. To easily test hybrid environments
(Linux & Windows).

Benefits
--------

1. Build and destroy Windows environments within minutes.

2. Use of Windows during trial evaluation period.

3. Fresh environment to validate bugs.

4. Reduce time required to maintain "golden environments".

5. Configure Windows using native PowerShell language.

6. Share scripts to build Windows environments to eliminate need to
   create scripts that may already exist.

Usage
-----

* Developers working on components that interact with Windows platforms can
  benefit by paws to create a test environment to verify their code changes.

* Quality Engineers needing to test products within hybrid environments can
  benefit by paws to create their fully configured test environment. Allowing
  them to easily begin test execution.

* DevOps can use paws to preview changes to production hybrid environments to
  ensure changes are stable before making final deployment.

Layers
------

Paws is composed of three layers as shown below:

.. image:: _static/paws_overview.png
    :align: center

**PAWS Client:** Paws command line client (Linux based).

**Providers:** Infrastructure hosting the Windows systems. See `providers
<providers.html>`_ to view the current available providers. Ansible cloud
modules currently are used to handle provisioning in available infrastructures.

**WS:** Centralized repository where all PowerShell scripts reside. Users
can use the PowerShells in the repo or they can define a set of PowerShells
from another repo or local folder. This is all configurable.

Finally..
---------

* Paws is NOT another tool to provision Windows systems and does not intend
  replace any existing configuration management tool.

* Paws is a great choice to be used for easily spinning up Windows systems and
  performing a remote desktop connection or to be used in CI/CD environment.

* We envision paws as the solution to efficiently spin up and configure free
  Windows systems leaving hybrid environments no longer an issue for
  development or testing purposes.
