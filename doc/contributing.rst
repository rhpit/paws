Contributing
-------------


### Devel packages

You might need to have these packages in your system, othwerise proceed with 
the command below to install them:

```
sudo dnf install -y git git-review wget gcc make rpm-build python-devel \
python-setuptools python-pip python2-flake8 pylint python2-devel \
python-kitchen openssl-devel libffi-devel gcc python-oslo-serialization \
python-pep8 ansible krb5-workstation
```

### Python virtual environment

we recommend you running this application in a separated python virtual 
environment to avoid any library conflict. Create a python virtual environment, 
activate it and install required libs:

```
virtualenv -p /usr/bin/python2.7 venv_paws
source venv_paws/bin/activate
pip install -r requirements.txt --upgrade
```

### code check and analyze

Before any commit make sure your code changes are following the code standard
of this project running the command:

```
cd paws-imgsrv
make codecheck
```


* running on libvirt

install -y virt-install virt-manager virt-viewer libvirt libvirt-devel

see win.sh script

* on eclipse and pydev ( fixing unresolved imports or to link source code to correct path ) 

- pydev add venv_paws in Python interpreter and project root folder as external libraries 
- project-->properties-->pydev-pythonpath-->external libraries --> add source folder, add the PARENT FOLDER of the project. 
  force workspace build clean-up: Project -> Clean -> Clean all projects
  
see screenshots: pydev_confg_{1,2,3,4}.png
