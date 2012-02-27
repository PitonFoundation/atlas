from fabric.api import task, env
from fabric.operations import put, run, sudo
from fabric.context_managers import cd, prefix
import os
from pprint import pprint

# Fabric tasks to deploy atlas
# Tested on Ubuntu 11.10

# Set up some default environment
# Name of instance, will be used to create paths and name certain
# config files
env['instance'] = env.get('instance', 'atlas')
# Directory where all the app assets will be put
# Tasks assume that this directory already exists and that you
# have write permissions on it. This is what I did to get started:
# 
# sudo addgroup atlas
# sudo adduser ghing atlas
# sudo mkdir /srv/www/atlas_dev
# sudo chmod g+rwxs /srv/www/atlas_dev
env['instance_root'] = env.get('instance_root', 
    os.path.join('/srv/www/', env['instance']))
env['production'] = env.get('production', False)
# Git repo
# Production environments can only pull from repo
env['repo_uri'] = env.get('repo_uri', 
    'git://github.com/ghing/atlas.git' if env['production'] else 'git@github.com:ghing/atlas.git')
env['repo_branch'] = env.get('repo_branch', 
    'master' if env['production'] else 'develop')

@task
def print_env():
    """ Output the configuration environment for debugging purposes """
    pprint(env)

@task
def mkvirtualenv():
    """ Create the virtualenv for the deployment """ 
    with cd(env['instance_root']):
        run('virtualenv --distribute --no-site-packages venv') 

@task
def install_mod_wsgi():
    """ Install Apache mod_wsgi """
    sudo('apt-get install libapache2-mod-wsgi')
    sudo('a2enmod wsgi')

@task
def install_postgres():
    """ Installs Postgresql package """
    sudo('apt-get install postgresql postgresql-server-dev-9.1')

@task
def install_spatial():
    """ Install geodjango dependencies """
    sudo('apt-get install binutils gdal-bin libproj-dev postgresql-9.1-postgis')

@task
def install_pil_dependencies():
    """ Install the dependencies for the PIL library """
    sudo('apt-get install python-dev libfreetype6-dev zlib1g-dev libjpeg8-dev')

@task
def install_nginx():
    """ Install the nginx webserver, used to serve static assets. """
    sudo('apt-get install nginx')
    # Disable the default nginx site
    sudo('rm /etc/nginx/sites-enabled/default') 

@task
def create_spatial_db_template():
    """ Create the spatial database template for PostGIS """
    # Upload the spatial template creation script
    put('scripts/create_template_postgis-debian.sh', '/tmp')

    # Run the script
    sudo('bash /tmp/create_template_postgis-debian.sh', user='postgres')

    # Delete the script
    run('rm /tmp/create_template_postgis-debian.sh')

@task
def createdb(name=env['instance']):
    """ Create the database """
    sudo("createdb -T template_postgis %s" % (name), user='postgres')

@task 
def createuser(username=env['instance'], dbname=env['instance']):
    """ Create a Postgresql user for this instance and grant them the permissions Django needs to the database """
    sudo("createuser --encrypted --pwprompt %s" % (username), user='postgres')
    print "You need to make sure you have a line like one of the following "
    print "in your pg_hba.conf:"
    print ""
    print "local\t%s\t%s\t127.0.0.1/32\tmd5" % (dbname, username)

@task 
def clone():
    """ Clone the application repository """
    with cd(env['instance_root']):
        run("git clone %s atlas" % (env['repo_uri']))

@task
def checkout(branch=env['repo_branch']):
    """ Checkout a particular repository branch """
    with cd(os.path.join(env['instance_root'], 'atlas')):
        run("git checkout %s" % (branch))

@task
def pull():
    """ Fetch updates from remote repo """
    with cd(os.path.join(env['instance_root'], 'atlas')):
        run('git pull')

@task
def install_requirements():
    """ Install application's Python requirements into the virtualenv """
    with cd(env['instance_root']):
        with prefix('source venv/bin/activate'):
            run('pip install --requirement ./atlas/REQUIREMENTS')

@task
def make_log_directory(instance=env['instance']):
    """ Create directory for instance's logs """
    with cd(env['instance_root']):
        run('mkdir logs')

@task
def upload_config(config_dir=os.path.join(os.getcwd(), 'config', env['instance']) + '/'):
    """ Upload a local config directory """
    remote_dir = os.path.join(env['instance_root'], 'atlas', 'config')
    put(config_dir, remote_dir)

@task
def install_config(instance=env['instance']):
    """ Install files that were uploaded via upload_local_config to their final homes """
    with cd(env['instance_root'] + '/atlas/'):
        run("cp config/%s/settings.py settings/%s.py" % (env['instance'], env['instance']))
        run("cp config/%s/wsgi.py wsgi.py" % (env['instance']))
        sudo("cp config/%s/apache/site /etc/apache2/sites-available/%s" % (env['instance'], env['instance']))
        sudo("cp config/%s/nginx/site /etc/nginx/sites-available/%s" % (env['instance'], env['instance']))

@task 
def syncdb(instance=env['instance']):
    """ Run syncdb management command in the instance's Django environment """
    with cd(env['instance_root']):
        with prefix('source venv/bin/activate'):
            run("python atlas/manage.py syncdb --settings=atlas.settings.%s" % (env['instance']))

@task 
def migrate(instance=env['instance']):
    """ Run South migrations in the instance's Django environment """
    with cd(env['instance_root']):
        with prefix('source venv/bin/activate'):
            run("python atlas/manage.py migrate --settings=atlas.settings.%s" % (env['instance']))

@task
def a2ensite(instance=env['instance']):
    """ Enable the site for the instance in Apache """
    sudo("a2ensite %s" % (instance))

@task
def nginxensite(instance=env['instance']):
    """ Enable the site for the instance's static files in Nginx """
    sudo("ln -s /etc/nginx/sites-available/%s /etc/nginx/sites-enabled/%s" % (instance, instance))

@task
def apache2_reload():
    """ Reload the Apache configuration """
    sudo('service apache2 reload')

@task
def nginx_reload():
    """ Reload the Nginx configuration """
    sudo('service nginx reload')

# QUESTION: How do you combine tasks?
