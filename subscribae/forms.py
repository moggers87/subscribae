from django import forms
from django.utils import timezone

from subscribae.models import Bucket


class BucketForm(forms.ModelForm):
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
