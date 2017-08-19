Installation
============

PAWS is only supported in Linux systems and currently can be installed as 
regular application based on RPM or container. 

Support matrix
--------------

.. csv-table::
	:header: "Operating System", "Version", "Application", "Container"
	:widths: 100, 75, 70, 70

	"`CentOS <http://www.centos.org>`_", "7.2, 7.3, 7.4", "Yes", "Yes"
	"`Fedora <http://www.fedoraproject.org>`_", "24, 25, 26", "Yes", "Yes"
	"`Red Hat Enterprise Linux <https://www.redhat.com/en/technologies/linux-platforms>`_", "7.2, 7.3, 7.4", "Yes", "No"

Application
-----------

PAWS is distributed as **RPM** compatible with YUM and DNF and **PIP** python
package.

.. attention::

	Ansible requires two additional python packages to be installed in order
	to communicate with Windows systems.

	**pywinrm**: This package is used for Windows remote management.
	At this time there is no RPM available.

	*https://pypi.python.org/pypi/pywinrm*

	**shade**: This package is required by Ansible to
	provision/teardown resources in a cloud infrastructure.

	*https://pypi.python.org/pypi/shade*
	*http://docs.openstack.org/infra/shade/*
	*http://docs.ansible.com/ansible/list_of_cloud_modules.html#openstack*

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
	openssl-devel libffi-devel redhat-rpm-config

	# Dnf package manager
	sudo dnf install -y git gcc make python-devel python-setuptools python-pip \
	openssl-devel libffi-devel redhat-rpm-config
	
installing paws-cli

.. code-block:: bash

	sudo pip install paws-cli

  

**Installing by RPM**

RPM is available at https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/ 
You will notice after install rpm we recommend running a pip to install some 
python libraries needed by PAWS providers. It is because those libraries are 
outdated by rpm and newest versions are provided by pip.

Below follow the steps to install PAWS for each of supported OS

CentOS
++++++

.. code-block:: bash

	sudo yum install -y centos-release-openstack-liberty
	sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
	sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/repo/epel-7/eduardocerqueira-paws-epel-7.repo
	sudo yum install -y paws
	
	sudo pip install python-novaclient python-glanceclient python-keystoneclient --upgrade

Fedora
++++++

Replace version from repo url to match with your Fedora version. 

.. code-block:: bash

	sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/repo/fedora-24/eduardocerqueira-paws-fedora-24.repo
	sudo dnf install -y paws

	sudo pip install python-novaclient python-glanceclient python-keystoneclient --upgrade

Red Hat Enterprise Linux
++++++++++++++++++++++++

On RHEL you need to have a valid subscription and enable repos below. EPEL is optional.

.. code-block:: bash

	sudo subscription-manager register
	sudo subscription-manager attach
	sudo subscription-manager repos --enable rhel-7-<variant>-rpms
	sudo subscription-manager repos --enable rhel-7-<variant>-optional-rpms
	sudo subscription-manager repos --enable rhel-7-<variant>-extras-rpms
	sudo subscription-manager repos --enable rhel-7-<variant>-openstack-8-tools-rpms
	sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/repo/epel-7/eduardocerqueira-paws-epel-7.repo
	sudo yum install -y paws

	sudo pip install python-novaclient python-glanceclient python-keystoneclient --upgrade


Container
---------

To use paws in a container, you will need to have docker installed and running
on your system. Please see the following link for details to setup your system
with docker: https://docs.docker.com/engine/installation/

.. attention::

   Make sure docker service is running and if you are running a Linux distro
   that has SELINUX make sure to manage it too otherwise it can cause 
   permissions denied errors while running paws container.

PAWS docker images are based on official Centos and Fedora images and you can 
pull from at https://hub.docker.com/r/eduardomcerqueira/paws/ or running the 
commands below.

You will notice the commands below are mounting the folder 
**/home/ecerquei/github/ws/** from host into the container. This folder contains
the WS scripts that you will see at next section on `getting started <guide.html>`_ 

Centos
++++++

.. code-block:: bash

	sudo docker pull eduardomcerqueira/paws:0.3.8-centos-latest
	sudo docker run -it --name paws-dev -v /home/ecerquei/github/ws/:/home/paws/paws eduardomcerqueira/paws:0.3.8-centos-latest /bin/bash 

Fedora latest
+++++++++++++

.. code-block:: bash

	sudo docker pull eduardomcerqueira/paws:0.3.8-fedora-latest
	sudo docker run -it --name paws-dev -v /home/ecerquei/github/ws/:/home/paws/paws eduardomcerqueira/paws:0.3.8-fedora-latest /bin/bash

Fedora 26
+++++++++

.. code-block:: bash

	sudo docker pull eduardomcerqueira/paws:0.3.8-fedora-26
	sudo docker run -it --name paws-dev -v /home/ecerquei/github/ws/:/home/paws/paws eduardomcerqueira/paws:0.3.8-fedora-26 /bin/bash

Fedora 25
+++++++++

.. code-block:: bash

	sudo docker pull eduardomcerqueira/paws:0.3.8-fedora-25
	sudo docker run -it --name paws-dev -v /home/ecerquei/github/ws/:/home/paws/paws eduardomcerqueira/paws:0.3.8-fedora-25 /bin/bash

Fedora 24
+++++++++

.. code-block:: bash

	sudo docker pull eduardomcerqueira/paws:0.3.8-fedora-24
	sudo docker run -it --name paws-dev -v /home/ecerquei/github/ws/:/home/paws/paws eduardomcerqueira/paws:0.3.8-fedora-24 /bin/bash

----

You are now ready to begin using paws! To get started please navigate to the
side bar on the left to see the `getting started <guide.html>`_
guide.
