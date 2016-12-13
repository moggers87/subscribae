from django.conf import settings
from django.db import models
from djangae.fields import JSONField, RelatedSetField


class Subscription(models.Model):
    """A subscription that belongs to a user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    last_update = models.DateTimeField()
    last_viewed = models.DateTimeField()

    # from subscription endpoint
    channel_id = models.CharField(max_length=200)  # snippet.resourceId.channelId
    title = models.CharField(max_length=200)  # snippet.title
    description = models.CharField(max_length=200)  # snippet.description
    thumbnail = models.ImageField()  # snippet.thumbnails.default
    # from channel endpoint
    upload_playlist = models.CharField(max_length=200)  # contentDetails.relatedPlaylists.uploads


class Bucket(models.Model):
    """A "bucket" that a user can put a subscription in

    A subscription can be in more than one bucket
    """
    subs = RelatedSetField(Subscription)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    last_update = models.DateTimeField()
    last_viewed = models.DateTimeField()


class Video(models.Model):
    """A video"""
    subscription = models.ForeignKey(Subscription)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    viewed = models.BooleanField(default=False)
    buckets = RelatedSetField(Bucket)

    # from video endpoint
    youtube_id = models.CharField(max_length=200)  # id
    title = models.CharField(max_length=200)  # snippet.title
    description = models.CharField(max_length=200)  # snippet.description
    thumbnail = models.ImageField()  # snippet.thumbnails.default
    # maybe?
    #player = models.TextField()  # player.embedHtml


class OauthToken(models.Model):
    """Oauth tokens for a specific user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    data = JSONField()
