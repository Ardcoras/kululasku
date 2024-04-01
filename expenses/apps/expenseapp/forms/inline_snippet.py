from django import forms
from django.forms.models import ModelFormMetaclass
from django.forms.models import inlineformset_factory
from expenseapp.models import ExpenseLine, Expense
from datetime import datetime

from expenses.settings import TIME_ZONE


# Inline formset-snippet:
# Copyright (c) 2010, Stanislas Guerra.
# All rights reserved.
# This document is licensed as free software under the terms of the
# BSD License: http://www.opensource.org/licenses/bsd-license.php

class ModelFormOptions(object):
    def __init__(self, options=None):
        self.inlines = getattr(options, 'inlines', {})


class ModelFormMetaclass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._forms = ModelFormOptions(getattr(new_class, 'Forms', None))
        return new_class


class ModelForm(forms.ModelForm, metaclass=ModelFormMetaclass):
    """
    Add to ModelForm the ability to declare inline formsets.

    It save you from the boiler-plate implementation of cross validation/saving of such 
    forms in the views.
    You should use It in the admin's forms if you need the inherit them in your apps 
    because there is not multi-inherance.

    >>> class Program(models.Model):
    ...     name = models.CharField(max_length=100, blank=True)

    >>> class ImageProgram(models.Model):
    ...     image = models.ImageField('image')
    ...     program = models.ForeignKey(Programm)

    >>> class Ringtone(models.Model):
    ...     sound = models.FileField('sound')
    ...     program = models.ForeignKey(Programm)

    Use It in your admin.py instead of django.forms.ModelForm:
    >>> class ProgramAdminForm(ModelForm):
    ... class Meta:
    ...     model = Program
    ...     def clean(self):
    ...         cleaned_data = self.cleaned_data
    ...         # stuff
    ...         return cleaned_data

    In your app, say you declare the following inline formsets:
    >>> ImageProgramFormSet = inlineformset_factory(Program, ImageProgram, 
    ...                                             form=ImageProgramForm, max_num=6)
    >>> RingToneFormSet = inlineformset_factory(Program, RingTone, form=RingtoneProgramForm)

    You can bind them in your program's form:
    >>> class MyProgramForm(ProgramAdminForm):
    ...     class Forms:
    ...         inlines = {
    ...             'images': ImageProgramFormSet,
    ...             'ringtones': RingToneFormSet,
    ...         }

    And instanciate It:
    >>> program_form = MyProgramForm(request.POST, request.FILES, prefix='prog')

    In the template, you access the inlines like that :
    {{ program_form.inlineformsets.images.management_form }}
    {{ program_form.inlineformsets.images.non_form_errors }}
    <table>
    {{ program_form.inlineformsets.images.as_table }}
    </table>
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self._forms, 'inlines'):
            self.inlineformsets = {}
            for key, FormSet in list(self._forms.inlines.items()):
                self.inlineformsets[key] = FormSet(self.data or None, self.files or None,
                                                   prefix=self._get_formset_prefix(
                                                       key),
                                                   instance=self.instance)

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        result = isinstance(instance, Expense)
        if(result):
            if(instance.personno):
                instance.personno = instance.personno.upper()
                instance.save()
        if hasattr(self._forms, 'inlines'):
            for key, FormSet in list(self._forms.inlines.items()):
                fset = FormSet(self.data, self.files, prefix=self._get_formset_prefix(key),
                               instance=instance)
                if fset.is_valid():
                    if(fset.model == ExpenseLine):
                        for i in range(0, fset.total_form_count()):
                            form = fset.forms[i]

                            ended_at_date_input = form.cleaned_data['ended_at_date']
                            ended_at_time_input = form.cleaned_data['ended_at_time']
                            begin_at_date_input = form.cleaned_data['begin_at_date']
                            begin_at_time_input = form.cleaned_data['begin_at_time']

                            file_input = form.cleaned_data['receipt']

                            if(ended_at_date_input == None):
                                ended_at = None
                            else:
                                if(ended_at_time_input == None):
                                    ended_at_time_str = "00:00:00"
                                    ended_at_str = '%s %s' % (
                                        ended_at_date_input, ended_at_time_str)
                                    ended_at = datetime.strptime(
                                        ended_at_str, '%Y-%m-%d %H:%M:%S')
                                else:
                                    ended_at_str = '%s %s' % (
                                        ended_at_date_input, ended_at_time_input)
                                    ended_at = datetime.strptime(
                                        ended_at_str, '%Y-%m-%d %H:%M:%S')

                            if(begin_at_date_input == None):
                                return HttpResponse("<script>window.top.$('#id_preview').val(0); window.top.$('#expense-form').off('submit.open_preview').attr('target', '').submit();</script>")
                            else:
                                if(begin_at_time_input == None):
                                    begin_at_time_input = "00:00:00"

                            begin_at_str = '%s %s' % (
                                begin_at_date_input, begin_at_time_input)
                            begin_at = datetime.strptime(
                                begin_at_str, '%Y-%m-%d %H:%M:%S')

                            res = form.save(commit=False)
                            res.begin_at = begin_at
                            res.ended_at = ended_at
                            res.save()
                    fset.save()
        return instance

    def has_changed(self, *args, **kwargs):
        has_changed = super().has_changed(*args, **kwargs)
        if has_changed:
            return True
        else:
            for fset in list(self.inlineformsets.values()):
                for i in range(0, fset.total_form_count()):
                    form = fset.forms[i]
                    if form.has_changed():
                        return True
        return False

    def _get_formset_prefix(self, key):
        return '%s_%s' % (self.prefix, key.upper())

    def _clean_form(self):
        super()._clean_form()
        for key, fset in self.inlineformsets.items():
            for i in range(0, fset.total_form_count()):
                f = fset.forms[i]
                if f.errors:
                    self._errors['_%s_%d' %
                                 (fset.prefix, i)] = f.non_field_errors

# Endofsnippet
