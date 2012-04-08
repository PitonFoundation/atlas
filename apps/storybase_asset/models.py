"""Models for story content assets"""

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
from django.utils.html import strip_tags
from django.utils.text import truncate_words
from django.utils.safestring import mark_safe
from filer.fields.image import FilerFileField, FilerImageField
from model_utils.managers import InheritanceManager
import oembed
from oembed.exceptions import OEmbedMissingEndpoint
from uuidfield.fields import UUIDField
from storybase.fields import ShortTextField
from storybase.models import (LicensedModel, PublishedModel,
    TimestampedModel, TranslatedModel, TranslationModel,
    set_date_on_published)
from embedable_resource import EmbedableResource
from embedable_resource.exceptions import UrlNotMatched
   
oembed.autodiscover()

ASSET_TYPES = (
  (u'image', u'image'),
  (u'audio', u'audio'),
  (u'video', u'video'),
  (u'map', u'map'),
  (u'table', u'table'),
  (u'quotation', u'quotation'),
  (u'text', u'text'),
)
"""The available types of assets

These represent what an asset is and not neccessarily how it is stored.
For example, a map might actually be stored as an image, or it could be
an HTML snippet.
"""

class Asset(TranslatedModel, LicensedModel, PublishedModel,
    TimestampedModel):
    """A piece of content included in a story

    An asset could be an image, a block of text, an embedded resource
    represented by an HTML snippet or a media file.
    
    This is a base class that provides common metadata for the asset.
    However, it does not provide the fields that specify the content
    itself.  Also, to reduce the number of database tables and queries
    this model class does not provide translated metadata fields.  When
    creating an asset, one shouldn't instantiate this class, but instead
    use one of the model classes that inherits form Asset.

    """
    asset_id = UUIDField(auto=True)
    type = models.CharField(max_length=10, choices=ASSET_TYPES)
    attribution = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    """The URL where an asset originated.

    It could be used to store the canonical URL for a resource that is not
    yet oEmbedable or the canonical URL of an article or tweet where text 
    is quoted from.

    """
    owner = models.ForeignKey(User, related_name="assets", blank=True,
                              null=True)
    section_specific = models.BooleanField(default=False)
    datasets = models.ManyToManyField('DataSet', related_name='assets', 
                                      blank=True)
    asset_created = models.DateTimeField(blank=True, null=True)
    """Date/time the non-digital version of an asset was created

    For example, the data a photo was taken
    """

    translated_fields = ['title', 'caption']

    # Use InheritanceManager from django-model-utils to make
    # fetching of subclassed objects easier
    objects = InheritanceManager()

    def __unicode__(self):
        subclass_obj = Asset.objects.get_subclass(pk=self.pk)
        return subclass_obj.__unicode__()

    @models.permalink
    def get_absolute_url(self):
        return ('asset_detail', [str(self.asset_id)])

    def display_title(self):
        """
        Wrapper to handle displaying some kind of title when the
        the title field is blank 
        """
        # For now just call the __unicode__() method
        return unicode(self)

    def render(self, format='html'):
        """Render a viewable representation of an asset

        Arguments:
        format -- the format to render the asset. defaults to 'html' which
                  is presently the only available option.

        """
        try:
            return getattr(self, "render_" + format).__call__()
        except AttributeError:
            return self.__unicode__()

    def render_thumbnail(self, width=None, height=None, format='html'):
        """Render a thumbnail-sized viewable representation of an asset 

        Arguments:
        height -- Height of the thumbnail in pixels
        width  -- Width of the thumbnail in pixels
        format -- the format to render the asset. defaults to 'html' which
                  is presently the only available option.

        """
        return getattr(self, "render_thumbnail_" + format).__call__(
            width, height)

    def render_thumbnail_html(self, width=None, height=None):
        """
        Render HTML for a thumbnail-sized viewable representation of an 
        asset 

        This just provides a dummy placeholder and should be implemented
        classes that inherit from Asset.

        Arguments:
        height -- Height of the thumbnail in pixels
        width  -- Width of the thumbnail in pixels

        """
        if width is None:
            width = 150
        if height is None:
            height = 100
        return mark_safe("<div class='featured-asset' "
                "style='height: %dpx; width: %dpx'>Asset Thumbnail</div>" %
                (height, width))
        
class AssetTranslation(TranslationModel):
    """
    Abstract base class for common translated metadata fields for Asset
    instances
    """
    asset = models.ForeignKey('Asset',  
        related_name="%(app_label)s_%(class)s_related") 
    title = ShortTextField(blank=True) 
    caption = models.TextField(blank=True)

    class Meta:
        abstract = True
        unique_together = (('asset', 'language')) 

class ExternalAsset(Asset):
    """Asset not stored on the same system as the application

    An ExternalAsset's resource can either be retrieved via an oEmbed API
    endpoint or in the case of an image or other media file, the file's
    URL.
    """
    translation_set = 'storybase_asset_externalassettranslation_related'
    translated_fields = Asset.translated_fields + ['url']

    def __unicode__(self):
        if self.title:
            return self.title
        elif self.url:
            return self.url
        else:
            return "Asset %s" % self.asset_id

    def render_html(self):
        """Render the asset as HTML"""
        output = []
        output.append('<figure>')
        try:
            # First try to embed the resource via oEmbed
            resource = oembed.site.embed(self.url, format='json')
            resource_data = resource.get_data()
            output.append(resource_data['html'])
        except OEmbedMissingEndpoint:
            try:
                # Next try to embed things ourselves
                html = EmbedableResource.get_html(self.url)
                output.append(html)
            except UrlNotMatched:
                # If all else fails, just show an image or a link
                if self.type == 'image':
                    output.append('<img src="%s" alt="%s" />' % (self.url, self.title))
                else:
                    output.append("<a href=\"%s\">%s</a>" % (self.url, self.title))

        if self.caption:
            output.append('<figcaption>')
            output.append(self.caption)
            output.append('</figcaption>')
        output.append('</figure>')

        return mark_safe(u'\n'.join(output))

class ExternalAssetTranslation(AssetTranslation):
    """Translatable fields for an Asset model instance"""
    url = models.URLField()

class HtmlAsset(Asset):
    """An Asset that can be stored as a block of HTML.

    This can store formatted text or an HTML snippet for an embedable
    resource.

    The text stored in an HtmlAsset doesn't have to contain HTML markup.

    """
    translation_set = 'storybase_asset_htmlassettranslation_related'
    translated_fields = Asset.translated_fields + ['body']

    def __unicode__(self):
        """ String representation of asset """
        if self.title:
            return self.title
        elif self.body:
            return truncate_words(strip_tags(mark_safe(self.body)), 4)
        else:
            return 'Asset %s' % self.asset_id

    def render_html(self):
        """Render the asset as HTML"""
        output = []
        if self.type == 'map':
            output.append('<figure>')
            output.append(self.body)
            if self.caption:
                output.append('<figcaption>')
                output.append(self.caption)
                output.append('</figcaption>')
            output.append('</figure>')
        else:
            output.append(self.body)
            
        return mark_safe(u'\n'.join(output))

class HtmlAssetTranslation(AssetTranslation):
    """Translatable fields for an HtmlAsset model instance"""
    body = models.TextField(blank=True)

class LocalImageAsset(Asset):
    """
    An asset that can be stored as an image file accessible by the
    application through a Django API
    
    This currently uses the `django-filer <https://github.com/stefanfoulis/django-filer>`_ 
    application for storing images as this app adds a lot of convenience
    for working with images in the Django admin.  This is subject to change.
    
    """
    translation_set = 'storybase_asset_localimageassettranslation_related'
    translated_fields = Asset.translated_fields + ['image']

    def __unicode__(self):
        if self.title:
            return self.title
        else:
            return "Asset %s" % self.asset_id

    def render_html(self):
        """Render the asset as HTML"""
        output = []
        output.append('<figure>')
        output.append('<img src="%s" alt="%s" />' % (self.image.url, 
                                                     self.title))
        if self.caption:
            output.append('<figcaption>')
            output.append(self.caption)
            output.append('</figcaption>')
        output.append('</figure>')
            
        return mark_safe(u'\n'.join(output))

class LocalImageAssetTranslation(AssetTranslation):
    """Translatable fields for a LocalImageAsset model instance"""
    image = FilerImageField()

# Hook up some signals so the publication date gets changed
# on status changes
pre_save.connect(set_date_on_published, sender=ExternalAsset)
pre_save.connect(set_date_on_published, sender=HtmlAsset)
pre_save.connect(set_date_on_published, sender=LocalImageAsset)

class DataSet(TranslatedModel, PublishedModel, TimestampedModel):
    """
    A set of data related to a story or used to produce a visualization
    included in a story

    This is a base class that provides common metadata for the data set.
    However, it does not provide the fields that specify the content itself.
    When creating a data set, one shouldn't instatniate this class, but
    instead use one of the model classes that inherits from DataSet.

    """
    dataset_id = UUIDField(auto=True)
    source = models.TextField(blank=True)
    attribution = models.TextField(blank=True)
    owner = models.ForeignKey(User, related_name="datasets", blank=True,
                              null=True)
    # dataset_created is when the data set itself was created
    dataset_created = models.DateTimeField(blank=True, null=True)
    """
    When the data set itself was created (possibly in non-digital form)
    """

    translation_set = 'storybase_asset_datasettranslation_related'
    translated_fields = ['title', 'description']

    # Use InheritanceManager from django-model-utils to make
    # fetching of subclassed objects easier
    objects = InheritanceManager()

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('dataset_detail', [str(self.asset_id)])

    def download_url(self):
        """Returns the URL to the downloadable version of the data set"""
        raise NotImplemented

class DataSetTranslation(TranslationModel):
    """Translatable fields for a DataSet model instance"""
    dataset = models.ForeignKey('DataSet', 
        related_name="%(app_label)s_%(class)s_related") 
    title = ShortTextField() 
    description = models.TextField(blank=True)

    class Meta:
        unique_together = (('dataset', 'language')) 

class ExternalDataSet(DataSet):
    """A data set stored on a different system from the application"""
    url = models.URLField()

    def download_url(self):
        """Returns the URL to the downloadable version of the data set"""
        return self.url 

class LocalDataSet(DataSet):
    """
    A data set stored as a file accessible by the application through
    a Django API

    This currently uses the `django-filer <https://github.com/stefanfoulis/django-filer>`_ 
    application for storing files as this app adds a lot of convenience
    for working with files in the Django admin.  This is subject to change.
    
    """
    file = FilerFileField()

    def download_url(self):
        """Returns the URL to the downloadable version of the data set"""
        return self.file.url 

def create_html_asset(type, title='', caption='', body='', language=settings.LANGUAGE_CODE, *args, **kwargs):
    """ Convenience function for creating a HtmlAsset

    Allows for creation of Assets without having to explicitly deal with
    the translations.

    """
    obj = HtmlAsset(
        type=type, 
        *args, **kwargs)
    obj.save()
    translation = HtmlAssetTranslation(
        asset=obj, 
        title=title, 
        caption=caption,
        body=body,
        language=language)
    translation.save()
    return obj

def create_external_asset(type, title='', caption='', url='', language=settings.LANGUAGE_CODE, *args, **kwargs):
    """ Convenience function for creating a HtmlAsset

    Allows for creation of Assets without having to explicitly deal with
    the translations.

    """
    obj = ExternalAsset(
        type=type, 
        *args, **kwargs)
    obj.save()
    translation = ExternalAssetTranslation(
        asset=obj, 
        title=title, 
        caption=caption,
        url=url,
        language=language)
    translation.save()
    return obj
