"""Utility functions for dealing with users and groups of users"""

from django.contrib.auth.models import User

import storybase_user.models
from storybase_user.models import Organization, Project, ADMIN_GROUP_NAME

def get_admin_emails():
    """Get a list of admin email addresses"""
    admin_qs = User.objects.filter(groups__name=ADMIN_GROUP_NAME)
                               
    if not admin_qs.count():
        # No CA admin users, default to superusers
        admin_qs = User.objects.filter(is_superuser=True)

    return admin_qs.values_list('email', flat=True)

def bulk_create(model, hashes, name_field='name',
                description_field='description'):
    create_fn = getattr(storybase_user.models,
                        "create_%s" % model.__name__.lower())
    for obj_dict in hashes:
        name = obj_dict[name_field]
        description = obj_dict[description_field]
        create_fn(name=name, description=description)


def bulk_create_organization(hashes, name_field='name',
                             description_field='description'):
    bulk_create(Organization, hashes, name_field, description_field)


def bulk_create_project(hashes, name_field='name',
                        description_field='description'):
    bulk_create(Project, hashes, name_field, description_field)
