from django.conf import settings
from django.db import models
from djangae.fields import RelatedSetField


class Subscription(models.Model):
    """A subscription that belongs to a user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    channel_id = models.CharField(max_length=200)  # check this?
    last_update = models.DateTime()
    last_viewed = models.DateTime()


class Bucket(models.Model):
    """A "bucket" that a user can put a subscription in

    A subscription can be in more than one bucket
    """
    subs = RelatedSetField(Subscription)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    last_update = models.DateTime()
    last_viewed = models.DateTime()


class Video(models.Model):
    """A video"""
    subs = models.ForeignKey(Subscription)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    viewed = models.BooleanField(default=False)
    youtube_id = models.CharField(max_length=200)  # check this?
