from django.db import models
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from mptt.managers import TreeManager

from categories.base import CategoryManager
from categories.settings import SLUG_TRANSLITERATOR

from storybase.models import TranslatedModel, TranslationModel
from storybase.utils import slugify

class CategoryTranslationBase(TranslationModel):
    name = models.CharField(verbose_name=_('Name'), max_length=100)
    slug = models.SlugField(verbose_name=_('Slug'))

    class Meta:
        abstract = True

    def __unicode__(self):
        return force_unicode(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(SLUG_TRANSLITERATOR(self.name))[:50]

        super(CategoryTranslationBase, self).save(*args, **kwargs)


class TranslatedCategoryBase(MPTTModel, TranslatedModel): 
    """
    A version of CategoryBase from the categories app that supports a
    translated name and slug field.
    """
    parent = TreeForeignKey('self', 
        blank=True, 
        null=True, 
        related_name="children", 
        verbose_name='Parent')
    active = models.BooleanField(default=True)
    
    objects = CategoryManager()
    tree = TreeManager()


    def save(self, *args, **kwargs):
        """
        While you can activate an item without activating its descendants,
        It doesn't make sense that you can deactivate an item and have its 
        decendants remain active.
        """
        super(TranslatedCategoryBase, self).save(*args, **kwargs)
        
        if not self.active:
            for item in self.get_descendants():
                if item.active != self.active:
                    item.active = self.active
                    item.save()
    
    def __unicode__(self):
        ancestors = self.get_ancestors()
        return ' > '.join([force_unicode(i.name) for i in ancestors]+[self.name,])
    
    class Meta:
        abstract = True
        ordering = ('tree_id', 'lft')
   
    # TODO: Figure out if we need to order categories by some field.
    # We could add a weight field to the model, or save a copy of the first
    # translation's name field.
    #class MPTTMeta:
    #    order_insertion_by = 'weight'


class CategoryTranslation(CategoryTranslationBase):
    category = models.ForeignKey('Category')

    class Meta:
        unique_together = (('category', 'language'))


class Category(TranslatedCategoryBase):
    translation_set = 'categorytranslation_set'
    translated_fields = ['name', 'slug']

    class Meta:
        verbose_name_plural = "categories"
