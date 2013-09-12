#!/bin/sh  

sudo ./scripts/apply_django_patches /home/vagrant/virtualenv/python2.7/lib/python2.7/site-packages/django
createdb -T template_postgis atlas_travis -U postgres
fab --set run_local=True,instance=travis install_solr make_solr_conf_dir make_solr_data_dir make_solr_lib_dir install_solr_2155
fab --set run_local=True,instance=travis install_jetty_script install_jetty_config
sudo cp config/travis/solr/solr.xml /usr/local/share/solr/multicore/
python manage.py build_solr_schema --settings=settings.travis > config/travis/solr/schema.xml
sudo cp config/travis/solr/schema.xml /usr/local/share/solr/multicore/travis/conf/
fab --set run_local=True install_solr_config:instance=travis,solr_multicore=True,project_root=`pwd`
sudo service jetty restart
# If running browser tests, uncomment these lines
#export DISPLAY=:99.0
#sh -e /etc/init.d/xvfb start

