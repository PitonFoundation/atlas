from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
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

class Asset(TranslatedModel, LicensedModel, PublishedModel,
    TimestampedModel):
    asset_id = UUIDField(auto=True)
    type = models.CharField(max_length=10, choices=ASSET_TYPES)
    attribution = models.TextField(blank=True)
    owner = models.ForeignKey(User, related_name="assets", blank=True,
                              null=True)
    section_specific = models.BooleanField(default=False)
    datasets = models.ManyToManyField('DataSet', related_name='assets', blank=True)
    # asset_created is when the asset itself was created
    # e.g. date a photo was taken
    asset_created = models.DateTimeField(blank=True, null=True)

    translated_fields = ['title', 'caption']

    # Use InheritanceManager from django-model-utils to make
    # fetching of subclassed objects easier
    objects = InheritanceManager()

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('asset_detail', [str(self.asset_id)])

    def render(self, format='html'):
        try:
            return getattr(self, "render_" + format).__call__()
        except AttributeError:
            return self.__unicode__()


class AssetTranslation(TranslationModel):
    asset = models.ForeignKey('Asset', related_name="%(app_label)s_%(class)s_related") 
    title = ShortTextField() 
    caption = models.TextField(blank=True)

    class Meta:
        abstract = True
        unique_together = (('asset', 'language')) 

class ExternalAsset(Asset):
#    translations = models.ManyToManyField('ExternalAssetTranslation', blank=True, verbose_name=_('translations'))

    translation_set = 'storybase_asset_externalassettranslation_related'
    translated_fields = Asset.translated_fields + ['url']

    def render_html(self):
        output = []
        output.append('<figure>')
        try:
            resource = oembed.site.embed(self.url, format='json')
            resource_data = resource.get_data()
            output.append(resource_data['html'])
        except OEmbedMissingEndpoint, e:
            print e
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
    url = models.URLField()

class HtmlAsset(Asset):
#    translations = models.ManyToManyField('HtmlAssetTranslation', blank=True, verbose_name=_('translations'))

    translation_set = 'storybase_asset_htmlassettranslation_related'
    translated_fields = Asset.translated_fields + ['body']

    def render_html(self):
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
    body = models.TextField(blank=True)

class LocalImageAsset(Asset):
#    translations = models.ManyToManyField('LocalImageAssetTranslation', blank=True, verbose_name=_('translations'))

    translation_set = 'storybase_asset_localimageassettranslation_related'
    translated_fields = Asset.translated_fields + ['image']

    def render_html(self):
        output = []
        output.append('<figure>')
        output.append('<img src="%s" alt="%s" />' % (self.image.url, self.title))
        if self.caption:
            output.append('<figcaption>')
            output.append(self.caption)
            output.append('</figcaption>')
        output.append('</figure>')
            
        return mark_safe(u'\n'.join(output))

class LocalImageAssetTranslation(AssetTranslation):
    image = FilerImageField()

# Hook up some signals so the publication date gets changed
# on status changes
pre_save.connect(set_date_on_published, sender=ExternalAsset)
pre_save.connect(set_date_on_published, sender=HtmlAsset)
pre_save.connect(set_date_on_published, sender=LocalImageAsset)

class DataSet(TranslatedModel, PublishedModel, TimestampedModel):
    dataset_id = UUIDField(auto=True)
    attribution = models.TextField(blank=True)
    owner = models.ForeignKey(User, related_name="datasets", blank=True,
                              null=True)
    # dataset_created is when the data set itself was created
    dataset_created = models.DateTimeField(blank=True, null=True)

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
        raise NotImplemented

class DataSetTranslation(TranslationModel):
    dataset = models.ForeignKey('DataSet', related_name="%(app_label)s_%(class)s_related") 
    title = ShortTextField() 
    description = models.TextField(blank=True)

    class Meta:
        unique_together = (('dataset', 'language')) 

class ExternalDataSet(DataSet):
    url = models.URLField()

    def download_url(self):
        return self.url 

class LocalDataSet(DataSet):
    file = FilerFileField()

    def download_url(self):
        return self.file.url 
