#
# paws-fedora:25
#
# to build:
# sudo docker build -t paws-fedora:25 .
# 
# to run:
# sudo docker run -it --name paws-f25 \
# -v /home/ecerquei/github/ws/:/home/paws/paws paws-fedora:25 /bin/bash 
#

FROM fedora:25

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
