##
#    Subscribae
#    Copyright (C) 2016  Matt Molyneaux <moggers87+git@moggers87.co.uk>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
from django import forms
from django.utils import timezone

from subscribae.models import Bucket, Subscription
from subscribae.widgets import SubscriptionInBucket


class BucketUniqueMixin(object):
    def validate_unique(self):
        """
        Call the instance's validate_unique() method and update the form's
        validation errors if any were raised.
        """
        exclude = self._get_validation_exclusions()
        exclude.remove("user")
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as e:
            self._update_errors(e)


class ErrorClassMixin(object):
    error_css_class = "error"


class BucketForm(ErrorClassMixin, BucketUniqueMixin, forms.ModelForm):
    class Meta:
        model = Bucket
        fields = [
            "title",
        ]

    def __init__(self, user=None, **kwargs):
        super(BucketForm, self).__init__(**kwargs)

        if user is not None:
            self.instance.user = user
            self.instance.last_update = timezone.now()


class BucketEditForm(ErrorClassMixin, BucketUniqueMixin, forms.ModelForm):
    class Meta:
        model = Bucket
        fields = [
            "title",
            "subs",
        ]
        widgets = {
            "subs": SubscriptionInBucket,
        }

    def __init__(self, **kwargs):
        super(BucketEditForm, self).__init__(**kwargs)
        self.instance.last_update = timezone.now()
        self.fields['subs'].queryset = Subscription.objects.filter(user=self.instance.user)
