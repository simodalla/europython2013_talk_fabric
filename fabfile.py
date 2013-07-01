# -*- coding: iso-8859-1 -*-

import os

from fabric.api import *
from fabric.contrib.files import exists


def host_type():
    run('uname -s')


def update_system_packages():
    run('apt-get update && apt-get upgrade -y')


def install_system_package(package=None):
    if package is None:
        package = prompt('Which package? ')
    run('apt-get install -y {}'.format(package))


def prepare_psycopg():
    """
    Prepare requirement for 'psycopg2' under virtualenv.
    """
    run('apt-get build-dep psycopg2 -y')


def prepare_virtualenv(virtualenv='europython2013'):
    requirements = 'requirements.txt'
    put(requirements)
    if not exists('/opt/virtualenvs/{}'.format(virtualenv)):
        run('mkvirtualenv --no-site-packages --distribute --clear {}'.format(
            virtualenv))
    with prefix('workon {}'.format(virtualenv)):
        run('lssitepackages')
        run('pip install -r {}'.format(requirements))


def start_vm_demo():
    vm_name = env['host'].split('.')[0]
    vm_path = os.path.expanduser(
        '~/Documents/Virtual Machines.localized/{}.vmwarevm/'.format(vm_name))
    local('ls "{}"'.format(vm_path))
    with path('"/Applications/VMware Fusion.app/Contents/Library"'):
        local('vmrun -T fusion start "{}"'.format(vm_path))


def stop_vm_demo():
    run('shutdown -h now')


def verify_virtualenv():
    with prefix('workon europython2013_ok'):
        run('lssitepackages')


def bootstrap(virtualenv='europython2013'):
    prepare_virtualenv(virtualenv)


def unbootstrap(virtualenv='europython2013'):
    run('rm -rf requirements.txt')
    run('rmvirtualenv {}'.format(virtualenv))
    run('apt-get uninstall libapache2-mod-wsgi')