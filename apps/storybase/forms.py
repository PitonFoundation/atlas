from copy import deepcopy
import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.fields import (CharField, FileField, MultiValueField,
        URLField)
from django.forms.widgets import FileInput, Textarea, TextInput, MultiWidget
from django.forms.models import ModelFormMetaclass, modelform_factory
from django.utils.translation import ugettext_lazy as _

from storybase.utils import is_file

COMMA_SPLIT_RE = re.compile(r'\s*,\s*')

class UserEmailField(CharField):
    """
    Field that takes a comma-separated list of email addresses and
    returns a queryset of User model instances whose email fields match the
    e-mail addresses passed as field data.
    """
    widget = Textarea

    def split_value(self, value):
        """
        Split input value at commas and whitespace.
        """
        return COMMA_SPLIT_RE.split(value)

    def clean(self, value):
        """
        Validates the given value and returns its "cleaned" value as an
        appropriate Python object.

        Raises ValidationError for any errors.
        """
        if not value:
            return []

        values = self.split_value(value)
        return User.objects.filter(email__in=values)


class FileOrUrlWidget(MultiWidget):
    def __init__(self, attrs=None):
        widgets = (FileInput(attrs=attrs),
                   TextInput(attrs=attrs),
        )
        super(FileOrUrlWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            if is_file(value):
                return [value, None]

            return [None, value]

        return [None, None]

    def format_output(self, rendered_widgets):
        """
        Given a list of rendered widgets (as strings), returns a Unicode string
        representing the HTML for the whole lot.

        """
        output = []
        output.append(u"<label class=\"sublabel\">%s</label>" % _("Select a file"))
        output.append(rendered_widgets[0])
        output.append(u"<label class=\"sublabel\">%s</label>" %  _("Or specify a URL"))
        output.append(rendered_widgets[1])
        return u''.join(output)


class FileOrUrlField(MultiValueField):
    widget = FileOrUrlWidget

    def __init__(self, *args, **kwargs):
        fields = (
            FileField(),
            URLField(),
        )
        super(FileOrUrlField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        # Return the file if it's specified, otherwise return the URL
        if data_list:
            if data_list[0]:
                return data_list[0]

            self.fields[1].run_validators(data_list[1])
            return data_list[1]

        return None


class TranslatedModelFormMetaclass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(TranslatedModelFormMetaclass, cls).__new__(cls,
                name, bases, attrs)
        meta = getattr(new_class, 'Meta', None)
        # Add a translated_fields attribute to the form's meta
        # options
        if meta:
            new_class._meta.translated_fields = getattr(meta,
                    'translated_fields', None)

        return new_class


class TranslatedModelForm(ModelForm):
    __metaclass__ = TranslatedModelFormMetaclass

    def __init__(self, data=None, *args, **kwargs):
        # Extract the data for the translated fields for passing to
        # the translation form
        translated_data = None
        if data:
            translated_data = {}
            for key, value in data.iteritems():
                if key in self._meta.translated_fields:
                    translated_data[key] = value
            if not len(translated_data):
                # If none of the translated fields were passed as data,
                # set translated_data back to None so the translation form
                # will be unbound
                translated_data = None
        super(TranslatedModelForm, self).__init__(data, *args, **kwargs)
        self._translation_model_form_class = modelform_factory(
            self._meta.model.translation_class,
            fields=self._meta.translated_fields)
        self._translation_form = self._translation_model_form_class(
                translated_data,
                instance=self._get_initial_translation_instance())
        merged_fields = deepcopy(self._translation_form.fields)
        merged_fields.update(self.fields)
        self.fields = merged_fields

    def _get_initial_translation_instance(self):
        if self.instance.pk is None:
            # New model, we can create an empty translation instance,
            # but we need to associate it with our instance
            relation_field_name = self._meta.model.get_translation_fk_field_name()
            kwargs = {}
            kwargs[relation_field_name] = self.instance
            return self._meta.model.translation_class(**kwargs)

        return self.instance.get_translation(create=True)

    def _update_translation_relation(self):
        # Update the translation form's instance relation to point to
        # the current value of the translated model instance.
        # The effect of this that we're concerned about is that this
        # sets the value of the <field_name>_id attribute to the that of
        # the instance's id.  In the case where both the instance and it's
        # translation are being created for the first time, the underlying
        # id field will be set to None when the assignment is made in
        # __init__
        self._translation_form
        relation_field_name = self._meta.model.get_translation_fk_field_name()
        setattr(self._translation_form.instance, relation_field_name,
                self.instance)

    def save(self, commit=True):
        instance = super(TranslatedModelForm, self).save(commit)
        self._update_translation_relation()
        self._translation_form.save(commit)
        return instance

    def full_clean(self):
        super(TranslatedModelForm, self).full_clean()
        self._translation_form.full_clean()
        self._errors.update(self._translation_form._errors)
