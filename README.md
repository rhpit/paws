[![PyPI version](https://badge.fury.io/py/paws-cli.svg)](https://badge.fury.io/py/paws-cli)
[![Documentation Status](https://readthedocs.com/projects/rhpit-paws/badge/?version=latest)](https://rhpit-paws.readthedocs-hosted.com/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/rhpit/paws.svg?branch=master)](https://travis-ci.org/rhpit/paws)

# PAWS :: Provision Automated Windows and Services

Paws is a Linux based tool to provision Windows systems and configure 
Windows services in a cloud or virtual computing environment.

Used by developers, quality engineerings, devOps, system administrators and 
anyone else that needs to perform operations against hybrid environments 
(Linux and Windows), PAWS easily builds Windows environments with minimal 
effort required.

### Benefits

* Create, build and destroy Windows test environments within minutes in cloud
or virtual computing environments.
* Create fresh environments to validate bugs and eliminating non-expected 
issues caused by left over configurations and data.
* Reduce the time spent on environment maintenance "golden-environments"
* Use native Windows language (PowerShell) to automate Windows server 
configurations.
* Easily share your scripts to run in different test environments 
(eliminating need to create scripts that already exists).

### important

* PAWS doesn't provide any Windows QCOW Image with it.
* It is expected you know how to build your own Windows QCOW image.
* PAWS doesn't supply any MSDN license or any rights.


## Examples of usage

* developers, working in components that interacts with Windows platform can
use PAWS to provision Windows with all configuration needed to verify their 
code changes.

* quality engineer, executing any type of tests for products running on hybrid 
environment (Linux and Windows) can use PAWS to provision the Windows
environment with pre-defined configuration and ready to start the tests
execution.

* developers, quality engineers and release engineers, can use PAWS to 
provison the Windows environment for a release dry-run before go to production.
With PAWS groups the installation and workflow can be defined managing the
reproducibility and avoiding left over data reducing risks of a production
release.  

* devOps, before apply changes in a hybrid environment (Linux and Windows) can
use PAWS to replicate the Windows environment based on scripts.


## Full documentation

To know more access the full documentation at
https://rhpit-paws.readthedocs-hosted.com/en/latest/


## Report an issue

To report an issue that can be ideas or suggestions for new features, or even
a bug, please follow github https://help.github.com/articles/creating-an-issue/

## License

It is under GNU GENERAL PUBLIC LICENSE version 3.0 as you have received a local
copy at LICENSE file
