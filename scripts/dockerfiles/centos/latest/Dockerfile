#
# paws-centos:latest
#
# to build:
# sudo docker build -t paws-centos:latest .
# 
# to run:
# sudo docker run -it --name paws-centos \
# -v /home/ecerquei/github/ws/:/home/paws/paws paws-centos:latest /bin/bash 
#

FROM centos:latest

# Install paws copr repository
RUN curl -o /etc/yum.repos.d/paws.repo https://copr.fedorainfracloud.org/\
coprs/eduardocerqueira/paws/repo/epel-7/eduardocerqueira-paws-epel-7.repo

# Install EPEL repository for paws dependencies
RUN yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest\
-7.noarch.rpm

# Install repository to access openstack packages
RUN yum install -y centos-release-openstack-liberty

# Install paws package
RUN yum install -y paws

# Clean yum cache
RUN yum clean all

# Add paws user with uid=1000
RUN useradd -u 1000 paws

# Switch to paws user
USER paws
