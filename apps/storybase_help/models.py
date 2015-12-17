import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from storybase.fields import ShortTextField
from storybase.models.translation import TranslatedModel, TranslationModel


class HelpManager(models.Manager):
    def get_by_natural_key(self, help_id):
        return self.get(help_id=help_id)


class HelpTranslation(TranslationModel):
    help = models.ForeignKey('Help')
    title = ShortTextField(blank=True)
    body = models.TextField(blank=True)


class Help(TranslatedModel):
    help_id = models.UUIDField(default=uuid.uuid4)
    slug = models.SlugField(blank=True)
    searchable = models.BooleanField(default=False)

    objects = HelpManager()

    translated_fields = ['body', 'title']
    translation_set = 'helptranslation_set'
    translation_class = HelpTranslation

    class Meta:
        verbose_name_plural = "help items"

    def __unicode__(self):
        if self.title:
            return self.title

        return _("Help Item") + " " + self.help_id

    def natural_key(self):
        return (self.help_id,)

    @models.permalink
    def get_absolute_url(self):
        """Calculate the canonical URL for a Help item"""
        if self.slug:
            return ('help_detail', [self.slug])

        return ('help_detail', [self.help_id])


def create_help(title='', body='', language=settings.LANGUAGE_CODE,
                 *args, **kwargs):
    """Convenience function for creating Help

    Allows for the creation of help items without having to explicitly
    deal with the translations.

    """
    obj = Help(*args, **kwargs)
    obj.save()
    translation = HelpTranslation(help=obj, title=title, body=body,
                                   language=language)
    translation.save()
    return obj
