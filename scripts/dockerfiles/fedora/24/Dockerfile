#
# paws-fedora:24
#
# to build:
# sudo docker build -t paws-fedora:24 .
# 
# to run:
# sudo docker run -it --name paws-f24 \
# -v /home/ecerquei/github/ws/:/home/paws/paws paws-fedora:24 /bin/bash 
#

FROM fedora:24

# Enable paws copr repository
RUN dnf install dnf-plugins-core -y
RUN dnf copr enable eduardocerqueira/paws -y

# Install paws package
RUN dnf install -y paws

# Clean yum cache
RUN dnf clean all

# Add paws user with uid=1000
RUN useradd -u 1000 paws

# Switch to paws user
USER paws
