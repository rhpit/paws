#
# paws -- provision automated windows and services
# Copyright (C) 2016 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

default: help

############################################
# GLOBAL VARIABLES
############################################
# set paws version to use as docker tag
VERSION=0.3.8

############################################
# Color definition
############################################
NO_COLOR    = \x1b[0m
OK_COLOR    = \x1b[32;01m
WARN_COLOR  = \x1b[33;01m
ERROR_COLOR = \x1b[31;01m

help:
	@echo
	@echo -e "Usage: $(WARN_COLOR) make target$(NO_COLOR) where $(WARN_COLOR)target$(NO_COLOR) is one of following:"
	@echo
	@echo -e "\t$(WARN_COLOR)build-centos$(NO_COLOR)         build paws-centos docker image"
	@echo -e "\t$(WARN_COLOR)build-fedora$(NO_COLOR)         build paws-fedora docker images"
	@echo -e "\t$(WARN_COLOR)push-centos$(NO_COLOR)          push paws-centos docker image to hub.docker.com"	
	@echo -e "\t$(WARN_COLOR)push-fedora$(NO_COLOR)          push paws-fedora docker images to hub.docker.com"
	@echo -e "\t$(WARN_COLOR)push-all$(NO_COLOR)          	 build and push all docker images to hub.docker.com"
	@echo -e "\t$(WARN_COLOR)clean-paws-images$(NO_COLOR)    delete all paws tagged images"
	@echo -e "$(NO_COLOR)"

build-centos:
	@echo -e "$(OK_COLOR)building paws-centos-latest:$(VERSION) docker image$(NO_COLOR)"
	@sudo docker build -t paws-centos-latest:$(VERSION) centos/latest
	@sudo docker tag paws-centos-latest:$(VERSION) eduardomcerqueira/paws:$(VERSION)-centos-latest
	@echo -e "$(OK_COLOR)image built$(NO_COLOR)"
	@sudo docker images paws-centos-latest:$(VERSION)

build-fedora:
	@echo -e "$(OK_COLOR)building paws-fedora-24:$(VERSION) docker image$(NO_COLOR)"
	@sudo docker build -t paws-fedora-24:$(VERSION) fedora/24
	@sudo docker tag paws-fedora-24:$(VERSION) eduardomcerqueira/paws:$(VERSION)-fedora-24
	@echo -e "$(OK_COLOR)building paws-fedora-25:$(VERSION) docker image$(NO_COLOR)"
	@sudo docker build -t paws-fedora-25:$(VERSION) fedora/25
	@sudo docker tag paws-fedora-25:$(VERSION) eduardomcerqueira/paws:$(VERSION)-fedora-25
	@echo -e "$(OK_COLOR)building paws-fedora-26:$(VERSION) docker image$(NO_COLOR)"
	@sudo docker build -t paws-fedora-26:$(VERSION) fedora/26
	@sudo docker tag paws-fedora-26:$(VERSION) eduardomcerqueira/paws:$(VERSION)-fedora-26
	@echo -e "$(OK_COLOR)building paws-fedora-latest:$(VERSION) docker image$(NO_COLOR)"
	@sudo docker build -t paws-fedora-latest:$(VERSION) fedora/latest     
	@sudo docker tag paws-fedora-latest:$(VERSION) eduardomcerqueira/paws:$(VERSION)-fedora-latest
	@echo -e "$(OK_COLOR)images built$(NO_COLOR)"
	@sudo docker images paws-fedora

push-centos:
	@sudo docker login
	@echo -e "$(OK_COLOR)push paws-centos-latest:$(VERSION) docker image to hub.docker.com$(NO_COLOR)"
	@sudo docker push eduardomcerqueira/paws:$(VERSION)-centos-latest
	
push-fedora:
	@sudo docker login
	@echo -e "$(OK_COLOR)push paws-fedora-24:$(VERSION) docker image to hub.docker.com$(NO_COLOR)"
	@sudo docker push eduardomcerqueira/paws:$(VERSION)-fedora-24
	@echo -e "$(OK_COLOR)push paws-fedora-25:$(VERSION) docker image to hub.docker.com$(NO_COLOR)"
	@sudo docker push eduardomcerqueira/paws:$(VERSION)-fedora-25
	@echo -e "$(OK_COLOR)push paws-fedora-26:$(VERSION) docker image to hub.docker.com$(NO_COLOR)"
	@sudo docker push eduardomcerqueira/paws:$(VERSION)-fedora-26
	@echo -e "$(OK_COLOR)push paws-fedora-latest:$(VERSION) docker image to hub.docker.com$(NO_COLOR)"
	@sudo docker push eduardomcerqueira/paws:$(VERSION)-fedora-latest

push-all: build-centos push-centos build-fedora push-fedora
	@echo -e "$(OK_COLOR)build and push all paws docker images to hub.docker.com$(NO_COLOR)"

clean-paws-images:
	#TODO: need something better
	@sudo docker rmi paws-fedora-24:$(VERSION)
	@sudo docker rmi paws-fedora-25:$(VERSION)
	@sudo docker rmi paws-fedora-26:$(VERSION)
	@sudo docker rmi paws-fedora-latest:$(VERSION)	
	@sudo docker rmi paws-centos-latest:$(VERSION)		
	