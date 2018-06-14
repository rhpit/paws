#
# paws dockerfile
#
# Build:
# sudo docker build -t paws:latest -f Dockerfile-latest .
#
# Run:
# sudo docker run -it --name paws-latest \
# -v /home/<user>/github/ws/:/home/paws/paws paws:latest bash
#

FROM centos:7

RUN useradd paws -u 1000
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
python get-pip.py && rm get-pip.py
RUN pip install --no-cache-dir paws-cli
USER paws
WORKDIR "/home/paws"
