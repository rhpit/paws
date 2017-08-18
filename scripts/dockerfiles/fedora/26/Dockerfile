#
# paws-fedora:26
#
# to build:
# sudo docker build -t paws-fedora:26 .
# 
# to run:
# sudo docker run -it --name paws-f26 \
# -v /home/ecerquei/github/ws/:/home/paws/paws paws-fedora:26 /bin/bash 
#

FROM fedora:26

# Enable paws copr repository
#RUN dnf install dnf-plugins-core -y
#RUN dnf copr enable eduardocerqueira/paws -y

RUN dnf install python-pip -y

# Add paws user with uid=1000
RUN useradd -u 1000 paws

# Switch to paws user
USER paws

RUN pip install -r https://github.com/rhpit/paws/raw/master/requirements-dev.txt

# temp using test.pypi
RUN pip install --user --index-url https://test.pypi.org/simple/ paws

# Install paws package
#RUN dnf install -y paws

# Clean yum cache
RUN dnf clean all
