from django.contrib.auth.models import User
from django.db import models
from uuidfield.fields import UUIDField
from storybase.fields import ShortTextField

class Organization(models.Model):
    """ An organization or a community group that users and stories can be associated with. """
    organization_id = UUIDField(auto=True)
    name = ShortTextField()
    slug = models.SlugField()
    website_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, related_name='organizations', blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('organization_detail', [self.organization_id])

class Project(models.Model):
    """ 
    A project that collects related stories.  
    
    Users can also be related to projects.
    """
    project_id = UUIDField(auto=True)
    name = ShortTextField()
    slug = models.SlugField()
    website_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)
    organizations = models.ManyToManyField(Organization, related_name='projects', blank=True)
    members = models.ManyToManyField(User, related_name='projects', blank=True) 
    # TODO: Add Stories field to Project 

    def __unicode__(self):
        return self.name
