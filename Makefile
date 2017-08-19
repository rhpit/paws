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
# set version into paws/version.txt before to run any build
# release is managed by separated variable due build diff between spec and pip
VERSION=$(shell cat paws/version.txt)
RELEASE=1
NAME=paws
MANPAGE=../paws-doc/man/paws.1
PWD=$(shell bash -c "pwd -P")
RPMDIST=$(shell rpm --eval '%dist')
RPMTOP=$(PWD)/rpmbuild
SPEC=$(NAME).spec
TARBALL=$(NAME)-$(VERSION)-$(RELEASE).tar.gz
SRPM=$(NAME)-$(VERSION)-$(RELEASE).src.rpm
RPM=$(NAME)-$(VERSION)-$(RELEASE).noarch.rpm
# for dev phony
DIST=$(shell bash -c "uname -r")
BRANCH=$(shell git symbolic-ref --short HEAD)
# Unit tests
TEST_SOURCE=tests
TEST_OUTPUT=$(RPMTOP)/TESTS
TEST_UNIT_FILE=unit-tests.xml

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
	@echo -e "\t$(OK_COLOR)--- code ---$(NO_COLOR)"	
	@echo -e "\t$(WARN_COLOR)clean$(NO_COLOR)         clean temp files from local workspace"
	@echo -e "\t$(WARN_COLOR)codecheck$(NO_COLOR)     run code checkers pep8 and pylint"
	@echo -e "\t$(WARN_COLOR)test$(NO_COLOR)          run unit tests locally"
				
	@echo -e "\t$(OK_COLOR)--- doc ---$(NO_COLOR)"	
	@echo -e "\t$(WARN_COLOR)doc$(NO_COLOR)           generate sphinx doc html and man pages"
	@echo -e "\t$(WARN_COLOR)gh-pages$(NO_COLOR)      publish html doc to github pages"

	@echo -e "\t$(OK_COLOR)--- pip ---$(NO_COLOR)"	
	@echo -e "\t$(WARN_COLOR)pip$(NO_COLOR)           build source codes and generate tar.gz file"
	@echo -e "\t$(WARN_COLOR)pypi-test$(NO_COLOR)     upload tar.gz to pypi-test"
	@echo -e "\t$(WARN_COLOR)pypi$(NO_COLOR)          upload tar.gz to pypi"

	@echo -e "\t$(OK_COLOR)--- rpm ---$(NO_COLOR)"	
	@echo -e "\t$(WARN_COLOR)rpm$(NO_COLOR)           build source codes and generate rpm file"
	@echo -e "\t$(WARN_COLOR)tarball$(NO_COLOR)       generate tarball of project"
	@echo -e "\t$(WARN_COLOR)srpm$(NO_COLOR)          generate srpm of project"
	@echo -e "\t$(WARN_COLOR)copr-dev$(NO_COLOR)      generate srpm and send to build in copr-devel internal Red Hat"
	@echo -e "\t$(WARN_COLOR)copr-upstream$(NO_COLOR) generate srpm and send to build in upstream copr-fedora"
	@echo -e "\t$(WARN_COLOR)all$(NO_COLOR)           clean test doc rpm"
	@echo -e "\t$(WARN_COLOR)dev$(NO_COLOR)           clean, rpm and install PAWS locally"

	@echo -e "\t$(OK_COLOR)--- docker ---$(NO_COLOR)"
	@echo -e "\t$(WARN_COLOR)build-centos$(NO_COLOR)  build paws-centos docker image"
	@echo -e "\t$(WARN_COLOR)build-fedora$(NO_COLOR)  build paws-fedora docker images"
	@echo -e "\t$(WARN_COLOR)push-centos$(NO_COLOR)   push paws-centos docker image to hub.docker.com"	
	@echo -e "\t$(WARN_COLOR)push-fedora$(NO_COLOR)   push paws-fedora docker images to hub.docker.com"
	@echo -e "\t$(WARN_COLOR)clean-images$(NO_COLOR)  delete all paws tagged images"
	@echo -e "$(NO_COLOR)"

all: clean test rpm

prep:
	@mkdir -p rpmbuild/{BUILD,RPMS,SOURCES,SRPMS,TESTS}
	@echo -e "$(OK_COLOR)rpmbuild workdir created$(NO_COLOR)"
	@echo

set-version:
	@cp paws/version.txt $(RPMTOP)/SOURCES/version.txt
	@cp paws/version.txt $(RPMTOP)/BUILD/version.txt
	@echo -e "$(OK_COLOR)set version $(VERSION) to $(RPMTOP)/SOURCES/version.txt$(NO_COLOR)"
	@echo

clean:
	$(RM) -r dist build paws.egg-info
	$(RM) $(NAME)*.tar.gz
	$(RM) -r rpmbuild build doc/build paws.egg-info 
	@find -name '*.py[co]' -delete
	@echo -e "$(OK_COLOR)deleted rpmbuild, dist and build$(NO_COLOR)"
	make clean -C doc/
	@echo
	
tarball: doc
	git ls-files | tar --transform='s|^|$(NAME)/|' \
	--files-from /proc/self/fd/0 \
	-czf $(RPMTOP)/SOURCES/$(TARBALL) $(SPEC)
	
	cd $(RPMTOP)/SOURCES/ && tar -xf $(TARBALL)
	cd $(RPMTOP)/SOURCES/ && cp paws.1 paws/paws.1
	cd $(RPMTOP)/SOURCES/ && tar -czf $(TARBALL) $(NAME)
	@echo -e "$(OK_COLOR)tarball created at $(RPMTOP)/SOURCES/$(TARBALL)$(NO_COLOR)"
	@echo

srpm: tarball
	rpmbuild --define="_topdir $(RPMTOP)" -ts $(RPMTOP)/SOURCES/$(TARBALL)
	@echo -e "$(OK_COLOR)srpm created at $(RPMTOP)/SRPMS/$(SRPM)$(NO_COLOR)"
	@echo

rpm: srpm
	rpmbuild --define="_topdir $(RPMTOP)" --rebuild $(RPMTOP)/SRPMS/$(SRPM)
	@echo -e "$(OK_COLOR)rpm created at $(RPMTOP)/RPMS/noarch/$(RPM)$(NO_COLOR)"
	@echo
	
test: prep
	nosetests --verbosity=3 -x --with-xunit \
	--xunit-file=$(TEST_OUTPUT)/$(TEST_UNIT_FILE)	
	@echo

doc: prep set-version
	make -C doc/ doc
	make -C doc/ man
	cp $(MANPAGE) $(RPMTOP)/SOURCES/
	cp $(MANPAGE) $(RPMTOP)/BUILD/paws.1
	@echo -e "$(OK_COLOR)html doc saved at: ../paws-doc/html/index.html$(NO_COLOR)"
	@echo -e "$(OK_COLOR)man page saved at: ../paws-doc/man/paws.1$(NO_COLOR)"
	@echo

gh-pages:
	make -C doc/ gh-pages

copr-dev: srpm
	# for devel and ci we use internal copr
	# you need to have a valid ~/.config/copr-devel file to use copr-cli
	@echo "building source-code from branch $(BRANCH)"
	@echo -e "$(OK_COLOR)running build in https://copr.devel.redhat.com/coprs/rhpit/paws-devel$(NO_COLOR)"
	@copr-cli --config /home/$(USER)/.config/copr-devel build rhpit/paws-devel $(RPMTOP)/SRPMS/$(SRPM) 

copr-upstream: srpm
	# build in fedora copr
	# you need to have a valid ~/.config/copr-fedora file to use copr-cli
	@echo "building source-code from branch $(BRANCH)"
ifeq ("$(BRANCH)","master")
	@echo -e "$(OK_COLOR)running build in https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/$(NO_COLOR)"
	@copr-cli --config /home/$(USER)/.config/copr-fedora build eduardocerqueira/paws $(RPMTOP)/SRPMS/$(SRPM) 
else
	@echo -e "$(ERROR_COLOR)can't run build for branch != master to upstream$(NO_COLOR)"
endif
	
codecheck: 
	@echo "------Starting PEP8 code analysis------"
	# TODO: pls enable me again after Libvirt code is integrated 
	# find paws/ tests/ -name "*.py" |xargs pep8 --verbose --statistics \
	# --count --show-pep8 --exclude=.eggs
	find paws/ tests/ -name "*.py" | grep -v libvirt | xargs pep8 \
	--verbose --statistics --count --show-pep8 --exclude=.eggs
	@echo "------Starting Pylint code analysis------"
	# TODO: pls enable me again after Libvirt code is integrated
	# find paws/ tests/ -name "*.py" | xargs pylint --rcfile=.pylintrc
	find paws/ tests/ -name "*.py" | grep -v libvirt | xargs pylint \
	--rcfile=.pylintrc
	@echo

# get distro and set package manager DNF or YUM depending of distro
distro:
	@echo "your system is running $(DIST)"
ifneq ($(findstring el,$(DIST)),)
PKGMNGR := yum
endif

ifneq ($(findstring fc,$(DIST)),)
PKGMNGR := dnf
endif

# build local rpm, remove previous, install new and print paws version
dev: clean distro rpm
ifneq ("$(wildcard /usr/bin/paws)","")
	sudo $(PKGMNGR) remove paws -y > /dev/null
endif
	sudo $(PKGMNGR) install $(shell bash -c "find $(RPMTOP)/RPMS/ \
	-name '$(NAME)-$(VERSION)*'") -y > /dev/null
# install pip modules
	sudo pip install -r requirements.txt > /dev/null
	sudo chown -R $(LOGNAME):$(LOGNAME) /usr/share/paws
	@echo 
	paws --version
	@echo

# Docker tasks
build-centos:
	@make -C scripts/dockerfiles build-centos
		
build-fedora:
	@make -C scripts/dockerfiles build-fedora
				
push-centos:
	@make -C scripts/dockerfiles push-centos

push-fedora:
	@make -C scripts/dockerfiles push-fedora

clean-images:
	@make -C scripts/dockerfiles clean-paws-images

# pip tasks
pip: clean
	@python setup.py sdist
	@echo -e "$(OK_COLOR)pip tar.gz created at dist/$(NAME)-cli-$(VERSION).tar.gz$(NO_COLOR)"
	@echo

# requires credential in ~/.pypirc		
pypi-test: pip
	@python setup.py sdist upload -r pypitest
	@echo -e "$(OK_COLOR)check https://test.pypi.org/project/paws/#files$(NO_COLOR)"
	@echo

# requires credential in ~/.pypirc		
pypi: pip
	@python setup.py sdist upload -r pypi
	@echo -e "$(OK_COLOR)check https://pypi.org/project/paws/#files$(NO_COLOR)"
	@echo
