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
import logging
import os

from apiclient.discovery import build
from djangae.db import transaction
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from google.appengine.ext.deferred import deferred
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
from oauth2client import client
import httplib2

from subscribae.models import Bucket, Video, Subscription, OauthToken, create_composite_key


API_NAME = 'youtube'
API_VERSION = 'v3'
API_MAX_RESULTS = 10
USER_SHARD = 500

_log = logging.getLogger(__name__)


def get_oauth_flow(user):
    redirect_uri = "https://%s%s" % (os.environ['HTTP_HOST'], reverse("oauth2callback"))

    flow = client.flow_from_clientsecrets(
        settings.OAUTH_CONF_PATH,
        scope=settings.OAUTH_SCOPES,
        redirect_uri=redirect_uri,
        login_hint=user.email,
    )
    # we need to access the user's YT account even when they're not directly
    # accessing the site
    flow.params['access_type'] = 'offline'
    # make sure YT gives us a refresh token, otherwise the above line is
    # useless, see
    # https://github.com/google/google-api-python-client/issues/213
    # https://github.com/google/oauth2client/issues/453
    flow.params['prompt'] = 'consent'

    return flow


def get_service(user_id):
    token = OauthToken.objects.get(user_id=user_id)
    credentials = token.get()
    http = credentials.authorize(httplib2.Http())

    service = build(API_NAME, API_VERSION, http=http)
    return service


def update_subscriptions(last_pk=None):
    try:
        qs = OauthToken.objects.order_by("pk").all()
        if last_pk:
            qs = qs.filter(pk__gt=last_pk)

        for obj in qs.iterator():
            deferred.defer(update_subscriptions_for_user, obj.user_id)
            last_pk = obj.pk
    except RuntimeExceededError:
        deferred.defer(update_subscriptions, last_pk)



def update_subscriptions_for_user(user_id, last_pk=None):
    """Updates subscriptions

    Loops over subscriptions we already have, deleting ones that no longer
    appear in the API
    """
    try:
        subscriptions = {}

        subscriptions_qs = Subscription.objects.order_by("pk").filter(user_id=user_id)
        if last_pk:
            subscriptions_qs = subscriptions_qs.filter(pk__gt=last_pk)
        subscriptions_qs = subscriptions_qs[:API_MAX_RESULTS]
        if len(subscriptions_qs) == 0:
            logging.debug("Subscription updates for User %s done.", user_id)
            return

        youtube = get_service(user_id)

        subscription_list = youtube.subscriptions() \
            .list(mine=True, forChannelId=','.join([obj.channel_id for obj in subscriptions_qs]), part='snippet', maxResults=API_MAX_RESULTS) \
            .execute()

        for item in subscription_list['items']:
            channel_id = item['snippet']['resourceId']['channelId']

            subscriptions[channel_id] = dict(
                last_update=timezone.now(),
                title=item['snippet']['title'],
                description=item['snippet']['description'],
                thumbnails={size: value.get('url', '') for size, value in item['snippet']['thumbnails'].items()},
                upload_playlist=None,  # must fetch this from the channel data
            )

        ids_from_sub = subscriptions.keys()

        channel_list = youtube.channels() \
            .list(id=','.join(ids_from_sub), part='contentDetails', maxResults=API_MAX_RESULTS) \
            .execute()
        ids_from_chan = [channel['id'] for channel in channel_list['items']]

        # there are times when a subscription has a channel id, but there
        # isn't channel data for whatever reason, e.g. I'm subscribed to
        # UCMzNCTNmDMBO9oueVWpuOMg but there's no data from the channel API
        missing_channels = set(ids_from_sub) - set(ids_from_chan)
        extra_channels = set(ids_from_chan) - set(ids_from_sub)
        _log.info("Missing these IDs from the channel list endpoint: %s", missing_channels)
        _log.info("Extra IDs from the channel list endpoint: %s", extra_channels)

        for channel in channel_list['items']:
            if channel['id'] in ids_from_sub:
                subscriptions[channel['id']]['upload_playlist'] = channel['contentDetails']['relatedPlaylists']['uploads']


        for obj in subscriptions_qs:
            if obj.channel_id not in ids_from_sub:
                # unsubscribed?
                continue
            if obj.channel_id in missing_channels:
                # missing data
                continue

            data = subscriptions[obj.channel_id]
            with transaction.atomic():
                obj.refresh_from_db()

                obj.last_update = data['last_update']
                obj.title = data['title']
                obj.description = data['description']
                obj.thumbnails = data['thumbnails']
                obj.upload_playlist = data['upload_playlist']

                obj.save()

            bucket_ids = Bucket.objects.filter(subs__contains=obj).values_list('pk', flat=True)
            bucket_ids = list(bucket_ids)
            deferred.defer(import_videos, user_id, obj.pk, obj.upload_playlist, bucket_ids)

            last_pk = obj.pk

    except RuntimeExceededError:
        pass

    deferred.defer(update_subscriptions_for_user, user_id, last_pk)


def new_subscriptions(user_id, page_token=None):
    """Import new subscriptions into the system

    Loops over subscription data from API, adding new suscriptions and updating
    old ones
    """
    try:
        youtube = get_service(user_id)
        while True:
            subscriptions = {}

            subscription_list = youtube.subscriptions() \
                .list(mine=True, part='snippet', maxResults=API_MAX_RESULTS, pageToken=page_token) \
                .execute()

            for item in subscription_list['items']:
                channel_id = item['snippet']['resourceId']['channelId']

                subscriptions[channel_id] = dict(
                    id=create_composite_key(str(user_id), channel_id),
                    user_id=user_id,
                    last_update=timezone.now(),
                    channel_id=channel_id,
                    title=item['snippet']['title'],
                    description=item['snippet']['description'],
                    thumbnails={size: value.get('url', '') for size, value in item['snippet']['thumbnails'].items()},
                    upload_playlist=None,  # must fetch this from the channel data
                )

            ids_from_sub = subscriptions.keys()

            channel_list = youtube.channels() \
                .list(id=','.join(ids_from_sub), part='contentDetails', maxResults=API_MAX_RESULTS) \
                .execute()
            ids_from_chan = [channel['id'] for channel in channel_list['items']]

            # there are times when a subscription has a channel id, but there
            # isn't channel data for whatever reason, e.g. I'm subscribed to
            # UCMzNCTNmDMBO9oueVWpuOMg but there's no data from the channel API
            missing_channels = set(ids_from_sub) - set(ids_from_chan)
            extra_channels = set(ids_from_chan) - set(ids_from_sub)
            _log.info("Missing these IDs from the channel list endpoint: %s", missing_channels)
            _log.info("Extra IDs from the channel list endpoint: %s", extra_channels)

            for channel in channel_list['items']:
                if channel['id'] in ids_from_sub:
                    subscriptions[channel['id']]['upload_playlist'] = channel['contentDetails']['relatedPlaylists']['uploads']

            for data in subscriptions.itervalues():
                if data['channel_id'] in missing_channels:
                    continue

                key = data.pop('id')
                obj, created = Subscription.objects.update_or_create(id=key, defaults=data)
                _log.debug("Subscription %s%s created", obj.id, "" if created else " not")
                if created:
                    deferred.defer(import_videos, user_id, key, obj.upload_playlist, [], only_first_page=True)

            if 'nextPageToken' in subscription_list:
                page_token = subscription_list['nextPageToken']
            else:
                break
    except RuntimeExceededError:
        deferred.defer(new_subscriptions, user_id, page_token)


def import_videos(user_id, subscription_id, playlist, bucket_ids, page_token=None, only_first_page=False):
    if page_token is not None and only_first_page:
        # initial import to show some videos, we don't need to do a full import of every video
        return
    try:
        youtube = get_service(user_id)
        while True:
            # TODO: consider
            # https://developers.google.com/youtube/v3/docs/activities/list it
            # has things like "publishedAfter" which could be a better way of
            # working out what we have and have not imported
            playlistitem_list = youtube.playlistItems() \
                .list(playlistId=playlist, part='contentDetails', pageToken=page_token, maxResults=API_MAX_RESULTS) \
                .execute()
            ids_from_playlist = [item['contentDetails']['videoId'] for item in playlistitem_list['items']]

            video_list = youtube.videos() \
                .list(id=','.join(ids_from_playlist), part='snippet', maxResults=API_MAX_RESULTS) \
                .execute()
            ids_from_video = [video['id'] for video in video_list['items']]

            missing_videos = set(ids_from_playlist) - set(ids_from_video)
            extra_videos = set(ids_from_video) - set(ids_from_playlist)
            _log.info("Missing these IDs from the video list endpoint: %s", missing_videos)
            _log.info("Extra IDs from the video list endpoint: %s", extra_videos)

            seen_before = False

            for video in video_list['items']:
                if video['id'] not in ids_from_playlist:
                    continue

                data = dict(
                    subscription_id=subscription_id,
                    user_id=user_id,
                    title=video['snippet']['title'],
                    description=video['snippet']['description'],
                    thumbnails={size: value.get('url', '') for size, value in video['snippet']['thumbnails'].items()},
                    youtube_id=video['id'],
                    buckets_ids=bucket_ids,
                )
                key = create_composite_key(str(user_id), video['id'])
                obj, created = Video.objects.get_or_create(id=key, defaults=data)
                _log.debug("Video %s%s created", obj.id, "" if created else " not")
                if not created:
                    # we've seen this video before, therefore we've already imported it
                    seen_before = True

            if 'nextPageToken' in playlistitem_list and not seen_before:
                page_token = playlistitem_list['nextPageToken']
            else:
                break
    except RuntimeExceededError:
        deferred.defer(import_videos, user_id, subscription_id, playlist, bucket_ids,
                       page_token=page_token, only_first_page=only_first_page)
