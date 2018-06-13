Name: 			paws
Version:		0.5.1
Release:		0

Summary:		Provision Automated Windows and Services
Group:			Development/Libraries
License:		GPL
URL:			https://rhpit.github.io/paws/
Source0:		https://copr.fedorainfracloud.org/coprs/eduardocerqueira/paws/tarball/%{name}-%{version}-%{release}.tar.gz

BuildArch:		noarch

BuildRequires:	python-setuptools
Requires:		python-pip
Requires:		redhat-rpm-config
Requires:		bash-completion
Requires:		python-devel
Requires:		gcc
Requires:		libffi-devel
Requires:		openssl-devel
Requires:		openssl
# git is needed to download ws.git repo
Requires:		git

%global debug_package %{nil}

%description
PAWS is a Linux command line tool for automation. Provisioning, installing and
configuring Windows services for test on hybrid Linux and Windows environment

%prep
%setup -q -n %{name}

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
# manpage
%{__mkdir_p} %{buildroot}/%{_mandir}/man1
cp paws.1 %{buildroot}/%{_mandir}/man1
# cli auto completion
%{__mkdir_p} %{buildroot}/%{_datadir}/bash-completion/completions
cp config/paws_completion %{buildroot}%{_datadir}/bash-completion/completions/paws

%files
%defattr(755,root,root,755)
%{python_sitelib}/paws*
%attr (755,root,root)/usr/bin/paws
%doc README.md
%doc doc/authors.rst
%doc %{_mandir}/man1/paws.1.gz
%{_datadir}/bash-completion/completions/paws

%post
# install pip modules required by PAWS and outdated when installed by rpm
echo installing pip required modules from https://github.com/rhpit/paws/raw/master/requirements.txt
pip install -U -r https://github.com/rhpit/paws/raw/master/requirements.txt > /dev/null

%changelog
* Wed Aug 08 2017 Eduardo Cerqueira <eduardomcerqueira@gmail.com>
 - removed ansible pip, now installed by rpm manager
* Tue Mar 21 2017 Eduardo Cerqueira <eduardomcerqueira@gmail.com>
 - Added git in required packages to be installed with paws
* Wed Feb 22 2017 Ryan Williams <rwilliams5262@gmail.com>
 - Fix path to man file to have man page working again
* Fri Feb 17 2017 Ryan Williams <rwilliams5262@gmail.com>
 - Added bash completion script to be part of rpm
* Thu Nov 03 2016 Eduardo Cerqueira <eduardomcerqueira@gmail.com>
 - USERDIR setfacl for sudo_user
* Mon Oct 31 2016 Eduardo Cerqueira <eduardomcerqueira@gmail.com>
- changed group to a valid group
- added action to install pip modules in post script
- organized buildrequires and requires packages
* Fri Oct 07 2016 Ryan Williams <rwilliams5262@gmail.com>
- Modify the user directory folder
* Mon Sep 19 2016 Eduardo Cerqueira <eduardomcerqueira@gmail.com>
- set permission to 755 for all files after install
* Thu Jul 14 2016 Eduardo Cerqueira <eduardomcerqueira@gmail.com>
- initial build
