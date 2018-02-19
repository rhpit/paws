Installation
============

Support Matrix
--------------

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Operating System
        - Version
        - Application
        - Container

    *   - `CentOS <http://www.centos.org>`_
        - OS >= 7.2
        - Yes
        - Yes

    *   - `Fedora <http://www.fedoraproject.org>`_
        - `Supported Releases <https://fedoraproject.org/wiki/Releases#Current_Supported_Releases>`_
        - Yes
        - Yes

    *   - `Red Hat Enterprise Linux <https://www.redhat.com/en/technologies/linux-platforms>`_
        - OS >= 7.2
        - Yes
        - No

Prerequisites
-------------

To install paws via pip, you will need to install the following system
dependencies in order to have the install succeed.

.. code-block:: bash
    :linenos:

    # dnf package manager
    sudo dnf install -y git gcc make python-devel python-setuptools \
    python-pip openssl openssl-devel libffi-devel redhat-rpm-config

    # yum package manager
    sudo yum install -y git gcc make python-devel python-setuptools \
    python-pip openssl openssl-devel libffi-devel redhat-rpm-config

Application
-----------

PIP
+++

https://pypi.python.org/pypi/paws-cli

.. code-block:: bash
    :linenos:

    pip install paws-cli

RPM
+++

https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/

**CentOS**

.. code-block:: bash
    :linenos:

    # install epel repo for package dependencies
    sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

    # install paws repo
    sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org\
    /coprs/eduardocerqueira/paws/repo/epel-7/eduardocerqueira-paws-epel-7.repo

    # install paws
    sudo yum install -y paws

**Fedora**

.. code-block:: bash
    :linenos:

    # install paws repo
    sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org\
    /coprs/eduardocerqueira/paws/repo/fedora-<VERSION>/eduardocerqueira-paws-\
    fedora-<VERSION>.repo

    # install paws
    sudo dnf install -y paws

-- OR --

.. code-block:: bash
    :linenos:

    # install dnf plugins core
    sudo dnf install dnf-plugins-core -y

    # enable paws copr repo
    sudo dnf copr enable eduardocerqueira/paws -y

    # install paws
    sudo dnf install -y paws

**Red Hat Enterprise Linux**

.. code-block:: bash
    :linenos:

    # register system
    sudo subscription-manager register

    # attach and enable repos
    sudo subscription-manager attach
    sudo subscription-manager repos --enable rhel-7-<variant>-rpms

    # enable epel repo for package dependencies (optional)
    sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

    # install paws repo
    sudo curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org/\
    coprs/eduardocerqueira/paws/repo/epel-7/eduardocerqueira-paws-epel-7.repo

    # install paws
    sudo yum install -y paws

.. warning::

    RPM installation will perform a post install task to install extra Python
    packages using pip. This is required because at this current point some
    required packages not available via RPM. You can view packages installed
    here: https://github.com/rhpit/paws/raw/master/requirements.txt

    Pywinrm: required for remote Windows management.

Container
---------

https://hub.docker.com/r/rywillia/paws/

.. code-block:: bash
    :linenos:

    # pull docker image
    sudo docker pull rywillia/paws:latest

    # clone ws repo
    cd ~ && git clone https://github.com/rhpit/ws.git ws

    # run docker and mount a new volume to the local ws repo folder
    sudo docker run -it --name paws -v /home/user/ws/:/home/paws/ws rywillia/paws:latest bash

Finally..
---------

By default PAWS searches for /home/user/ws as folder for userdir where
scripts should be saved. See `userdir <tasks.html?highlight=userdir>`_
