# -*- coding: iso-8859-1 -*-

from __future__ import with_statement
from contextlib import nested

import datetime
import os

from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import exists


BACKUP_DATE_FORMAT = "%d_%m_%Y_%H_%S"


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


def bootstrap(virtualenv='europython2013',
              project='europython2013_talk_mezzanine'):
    prepare_virtualenv(virtualenv)
    with cd('/opt/projects/'):
        run('git clone https://github.com/simodalla/{}.git'.format(
            project))
    database_name = 'europython2013_demo'
    run('createdb -U postgres {}'.format(database_name))
    with settings(warn_only=True):
        local('pg_dump -h 127.0.0.1 -Ft {} |'
              ' pg_restore -U postgres -h {} -d {}'.format(database_name,
                                                           env['host'],
                                                           database_name))
    with nested(cd('/opt/projects/{}/europython2013_demo'.format(project)),
                prefix('workon {}'.format(virtualenv))):
        run('python manage.py collectstatic --noinput')
    run('service apache2 restart')


def deploy(virtualenv='europython2013',
           project='europython2013_talk_mezzanine'):
    now = datetime.datetime.now()
    if not confirm('Sei sicuro di voler fare il deploy del progetto'
                   ' in produzione?', default=False):
        abort('Deploy aborted.')
    project_path = '/opt/projects/{}/europython2013_demo'.format(project)
    database_name = 'europython2013_demo'
    run('tar cfz /opt/projects/backup_{}_{}.tar.gz --exclude={}/static'
        ' {}'.format(project, now.strftime(BACKUP_DATE_FORMAT),
                     project_path, project_path))
    run('pg_dump -U postgres -Ft {} >'
        ' /opt/projects/pg_{}_{}.dump'.format(
            database_name, project, now.strftime(BACKUP_DATE_FORMAT)))
    with cd('{}/../'.format(project_path)):
        run('git pull')
    with nested(cd(project_path), prefix('workon {}'.format(virtualenv))):
        # with prefix('workon {}'.format(virtualenv)):
        run('python manage.py collectstatic --noinput')
    run('service apache2 restart')
    # run('supervisorctl restart all')


def unbootstrap(virtualenv='europython2013',
                project='europython2013_talk_mezzanine'):
    run('rm -rf requirements.txt')
    run('rmvirtualenv {}'.format(virtualenv))
    run('apt-get uninstall libapache2-mod-wsgi')
    with settings(warn_only=True):
        run('dropdb -U postgres europython2013_demo')
        run('rm -rf /opt/projects/{}'.format(project))
        run('rm -rf /opt/projects/backup_europython2013*')
        run('rm -rf /opt/projects/pg_europython2013*')
