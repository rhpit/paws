Installation
============

PAWS is only supported in Linux systems and currently can be installed as 
regular application based on **RPM**, **PIP** or **container**. 

Support matrix
--------------

.. csv-table::
	:header: "Operating System", "Version", "Application", "Container"
	:widths: 100, 75, 70, 70

	"`CentOS <http://www.centos.org>`_", "7.2, 7.3, 7.4", "Yes", "Yes"
	"`Fedora <http://www.fedoraproject.org>`_", "`Supported Releases <https://fedoraproject.org/wiki/Releases#Current_Supported_Releases>`_", "Yes", "Yes"
	"`Red Hat Enterprise Linux <https://www.redhat.com/en/technologies/linux-platforms>`_", "7.2, 7.3, 7.4", "Yes", "No"

.. note::

	PAWS when installed by RPM runs automatically a post task to install 
	some extra python pip modules to your system. They must be handled by pip
	because at this current date some of them are not distributed by RPM 
	and others are outdated when installed by RP,M like the case of 
	python-novaclient that by RPM the latest version is 3.3.1 
	and by pip it is 9.1.0 

	At this link you can see all pip modules that will be installed during
	post task: https://github.com/rhpit/paws/raw/master/requirements.txt
		 
	Ansible requires two additional python packages to be installed in order
	to communicate with Windows systems.

	**pywinrm**: This package is used for Windows remote management.
	At this time there is no RPM available.

	https://pypi.python.org/pypi/pywinrm

	**shade**: This package is required by Ansible to
	provision/teardown resources in a cloud infrastructure.

	https://pypi.python.org/pypi/shade
	
	http://docs.openstack.org/infra/shade/
	
	http://docs.ansible.com/ansible/list_of_cloud_modules.html#openstack


Application
-----------

**Installing by PIP**

.. attention::

	PAWS pip package name is **paws-cli** [1] and not only paws. It is because 
	the project name paws [2] is already been used by other project with no
	relation with this project.
	
	[1] https://pypi.python.org/pypi/paws-cli
	
	[2] https://pypi.python.org/pypi/paws

Using pip the installation is basically running one command, *exception may
occur if you are running a minimal OS version or don't have python-pip and 
others required packages installed in your system*, installing packages required:

.. code:: bash

	# Yum package manager
	sudo yum install -y git gcc make python-devel python-setuptools python-pip \
	openssl openssl-devel libffi-devel redhat-rpm-config

	# Dnf package manager
	sudo dnf install -y git gcc make python-devel python-setuptools python-pip \
	openssl openssl-devel libffi-devel redhat-rpm-config

.. code-block:: bash

	sudo pip install paws-cli


**Installing by RPM**

RPM is available at https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/ 
Below follow the steps to install PAWS for each of supported OS

CentOS
++++++

.. code-block:: bash

	sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
	sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/repo/epel-7/eduardocerqueira-paws-epel-7.repo
	sudo yum install -y paws

Fedora
++++++

Replace **<VERSION>** from repo url to match with your Fedora version or just
use copr that does it automatically for you:

.. code-block:: bash

	sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/repo/fedora-<VERSION>/eduardocerqueira-paws-fedora-<VERSION>.repo
	sudo dnf install -y paws
	
or by copr

.. code-block:: bash

	sudo dnf install dnf-plugins-core -y
	sudo dnf copr enable eduardocerqueira/paws -y
	sudo dnf install -y paws


Red Hat Enterprise Linux
++++++++++++++++++++++++

On RHEL you need to have a valid subscription and enable repos below. EPEL is optional.

.. code-block:: bash

	sudo subscription-manager register
	sudo subscription-manager attach
	sudo subscription-manager repos --enable rhel-7-<variant>-rpms
    sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
	sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/repo/epel-7/eduardocerqueira-paws-epel-7.repo
	sudo yum install -y paws


Container
---------

To use paws in a container, you will need to have docker installed and running
on your system. Please see the following link for details to setup your system
with docker: https://docs.docker.com/engine/installation/

.. attention::

   Make sure docker service is running and if you are running a Linux distro
   that has SELINUX make sure to manage it too otherwise it can cause 
   permissions denied errors while running paws container.

PAWS docker image are based on official alpine image and you can pull from
https://hub.docker.com/r/rywillia/paws/ or running the following commands
below.

You will notice the commands below are mounting the folder 
**/home/user/ws/** from host into the container. This folder contains
the WS scripts that you will see at next section on `getting started <guide.html>`_ 

PS: By default PAWS searches for /home/user/ws as folder for userdir where
scripts should be saved. see `userdir <tasks.html?highlight=userdir>`_

.. code-block:: bash

    sudo docker pull rywillia/paws:latest
    cd ~ && git clone https://github.com/rhpit/ws.git ws
    sudo docker run -it --name paws -v /home/user/ws/:/home/paws/ws rywillia/paws:latest sh

You are now ready to begin using paws! To get started please navigate to the
side bar on the left to see the `getting started <guide.html>`_
guide.
