"""Customized base ModelAdmin classes"""

from django.contrib import admin
from django.contrib.admin import widgets
from fields import ShortTextField

class AdminLongTextInputWidget(widgets.AdminTextInputWidget):
    """ Slightly wider AdminTextInputWidget """
    def __init__(self, attrs=None):
        # Set size attribute as longer than default
        # and override class so text input size doesn't get 
        # shortened by CSS
        final_attrs = {'size': 60, 'class': 'vLongTextField'}
        if attrs is not None:
            final_attrs.update(attrs)
        super(AdminLongTextInputWidget, self).__init__(attrs=final_attrs)

class StorybaseModelAdmin(admin.ModelAdmin):
    """ Base class for ModelAdmin classes in this project 

    Correctly sets the widget for our text field class in the Django
    Admin.  It seems like this is the only place you can do it, though
    it would be nice to do it with the field definition.

    Also provides a prefix_inlines attribute that allows us to show some
    inlines before the rest of the fields rather than after (the default)

    """
    # List of classes listed in ModelAdmin.inlines that should have their
    # form shown before the model's non-inline fields rahter than after
    # Useful for translations
    prefix_inline_classes = [] 

    formfield_overrides = {
        ShortTextField: {'widget': AdminLongTextInputWidget},
    }

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['prefix_inline_classes'] = self.prefix_inline_classes
        return super(StorybaseModelAdmin, self).add_view(request, form_url,
           extra_context=extra_context) 

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context['prefix_inline_classes'] = self.prefix_inline_classes
        return super(StorybaseModelAdmin, self).change_view(request, object_id,
           extra_context=extra_context) 

class StorybaseStackedInline(admin.StackedInline):
    """Custom version of StackedInline

    This sets the widget for ShortTextField fields to the customized
    wider version.  It also provides a method to let us display some
    inlines before non-inline model fields and some after.

    """
    formfield_overrides = {
        ShortTextField: {'widget': AdminLongTextInputWidget},
    }

    def type(self):
        """ Get the class name of this inline

        Django's templates don't let us access attributes that start
        with '__', so we need to wrap it in a method.  This is used
        to check whether the an inline form should be shown before or
        after the other fields.

        """
        return self.__class__.__name__

def obj_title(obj):
    """ Callable to display an object title in the Django admin

    This is needed because title isn't an attribute of the Story or 
    Section models, it's an attribute of the translation class.

    """
    return obj.title
obj_title.short_description = 'Title'
