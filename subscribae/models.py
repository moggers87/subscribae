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
import base64

from djangae.fields import ComputedCharField, RelatedSetField
from django.conf import settings
from django.db import models
from oauth2client.client import Credentials


def create_composite_key(*args):
    key = '|'.join([a for a in args])
    return base64.urlsafe_b64encode(key)


class Subscription(models.Model):
    """A subscription that belongs to a user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    last_update = models.DateTimeField()
    last_viewed = models.DateTimeField(null=True)

    # from subscription endpoint
    channel_id = models.CharField(max_length=200)  # snippet.resourceId.channelId
    title = models.CharField(max_length=200)  # snippet.title
    description = models.TextField()  # snippet.description
    thumbnail = models.ImageField()  # snippet.thumbnails.default

    # from channel endpoint
    upload_playlist = models.CharField(max_length=200)  # contentDetails.relatedPlaylists.uploads

    # calculate id based on user ID + channel ID so we can get by keys later
    id = ComputedCharField(lambda self: create_composite_key(str(self.user_id), self.channel_id), primary_key=True, max_length=200)


class Bucket(models.Model):
    """A "bucket" that a user can put a subscription in

    A subscription can be in more than one bucket
    """
    subs = RelatedSetField(Subscription)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=200)
    last_update = models.DateTimeField()
    last_viewed = models.DateTimeField(null=True)


class Video(models.Model):
    """A video"""
    subscription = models.ForeignKey(Subscription)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    viewed = models.BooleanField(default=False)
    buckets = RelatedSetField(Bucket)

    # from video endpoint
    youtube_id = models.CharField(max_length=200)  # id
    title = models.CharField(max_length=200)  # snippet.title
    description = models.TextField()  # snippet.description
    thumbnail = models.ImageField(null=True)  # snippet.thumbnails.default
    # maybe?
    #player = models.TextField()  # player.embedHtml

    # calculate id based on user ID + video ID so we can get by keys later
    id = ComputedCharField(lambda self: create_composite_key(str(self.user_id), self.youtube_id), primary_key=True, max_length=200)


class OauthToken(models.Model):
    """Oauth tokens for a specific user"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True)
    data = models.TextField()

    def get(self):
        return Credentials.new_from_json(self.data)
