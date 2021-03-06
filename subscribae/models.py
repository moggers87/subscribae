##
#    Copyright (C) 2016  Matt Molyneaux <moggers87+git@moggers87.co.uk>
#
#    This file is part of Subscribae.
#
#    Subscribae is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Subscribae is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with Subscribae.  If not, see <http://www.gnu.org/licenses/>.
##

import base64

from djangae.contrib.gauth_datastore.models import GaeAbstractDatastoreUser
from djangae.db.constraints import UniquenessMixin
from djangae.fields import ComputedCharField, JSONField, RelatedSetField
from django.conf import settings
from django.db import models
from django.template import Context, Template
from django.template.loader import get_template
from oauth2client.client import Credentials

from subscribae.managers import SubscriptionQuerySet, VideoQuerySet

DEFAULT_SIZE = 'medium'


def create_composite_key(*args):
    key = '|'.join([a for a in args])
    return base64.urlsafe_b64encode(key)


class ThumbnailAbstract(models.Model):
    thumbnails = JSONField()

    def get_thumbnail(self, size=DEFAULT_SIZE):
        if size in self.thumbnails:
            return self.thumbnails[size]
        elif DEFAULT_SIZE in self.thumbnails:
            return self.thumbnails[DEFAULT_SIZE]
        elif len(self.thumbnails) > 0:
            return self.thumbnails.values()[0]
        else:
            return ""

    class Meta:
        abstract = True


class Subscription(ThumbnailAbstract):
    """A subscription that belongs to a user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    last_update = models.DateTimeField()
    last_viewed = models.DateTimeField(null=True)
    last_watched_video = models.CharField(max_length=200)

    # from subscription endpoint
    channel_id = models.CharField(max_length=200)  # snippet.resourceId.channelId

    # from channel endpoint
    upload_playlist = models.CharField(max_length=200)  # contentDetails.relatedPlaylists.uploads

    # calculate id based on user ID + channel ID so we can get by keys later
    id = ComputedCharField(lambda self: create_composite_key(str(self.user_id), self.channel_id),
                           primary_key=True, max_length=200)

    objects = SubscriptionQuerySet.as_manager()

    def __unicode__(self):
        tmpl = get_template("subscribae/models/subscription.html")
        return tmpl.render({"object": self})

    def __repr__(self):
        return "<Subscription {}>".format(self.channel_id.encode("utf-8", "ignore"))

    def add_titles(self):
        """Fetches titles and descriptions for Subscription"""
        from subscribae.utils import subscription_add_titles
        return list(subscription_add_titles([self]))[0]


class Bucket(UniquenessMixin, models.Model):
    """A "bucket" that a user can put a subscription in

    A subscription can be in more than one bucket
    """
    subs = RelatedSetField(Subscription)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=100)
    last_update = models.DateTimeField()
    last_viewed = models.DateTimeField(null=True, blank=True)
    last_watched_video = models.CharField(max_length=200)

    class Meta:
        unique_together = ["user", "title"]
        ordering = ["title"]

    @property
    def latest_videos(self):
        qs = self.video_set.all()
        if self.last_watched_video:
            qs = qs.filter(ordering_key__gt=self.last_watched_video)

        return qs


class Video(ThumbnailAbstract):
    """A video"""
    subscription = models.ForeignKey(Subscription)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    viewed = models.BooleanField(default=False)
    buckets = RelatedSetField(Bucket)

    # from video endpoint
    youtube_id = models.CharField(max_length=200)  # id
    published_at = models.DateTimeField()

    # calculate id based on user ID + video ID so we can get by keys later
    id = ComputedCharField(lambda self: create_composite_key(str(self.user_id), self.youtube_id),
                           primary_key=True, max_length=200)
    ordering_key = ComputedCharField(lambda self: create_composite_key(self.published_at.isoformat(" "),
                                     self.youtube_id), max_length=200)

    objects = VideoQuerySet.as_manager()

    class Meta:
        ordering = ["ordering_key"]

    @property
    def html_snippet(self):
        tmpl = get_template("subscribae/includes/videos.html")
        return tmpl.render({"video": self})

    def add_titles(self):
        """Fetches titles and descriptions for Video"""
        from subscribae.utils import video_add_titles
        return list(video_add_titles([self]))[0]


class OauthToken(models.Model):
    """Oauth tokens for a specific user"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True)
    data = models.TextField()

    def get(self):
        return Credentials.new_from_json(self.data)


class SiteConfig(models.Model):
    """
    Site specific configuration

    Because storing this in a settings.ini and redploying any time you want to
    change a settings is horrid
    """
    site_name = models.CharField(default="cool.example.com", max_length=200)
    footer_text = models.TextField(default="Someone forgot to fill out the footer!")
    source_link = models.CharField(default="https://github.com/moggers87/subscribae", max_length=200)

    def render_footer(self):
        tmpl = Template(self.footer_text)
        return tmpl.render(Context({"object": self}))


class SubscribaeUser(GaeAbstractDatastoreUser):
    is_active = models.BooleanField(default=False)
