from django.conf import settings
from django.db import models
from djangae.fields import RelatedSetField


class Subscription(models.Model):
    """A subscription that belongs to a user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    channel_id = models.CharField(max_length=200)  # check this?


class Bucket(models.Model):
    """A "bucket" that a user can put a subscription in

    A subscription can be in more than one bucket
    """
    subs = RelatedSetField(Subscription)


class Video(models.Model):
    """A video"""
    subs = models.ForeignKey(Subscription)
