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

_log = logging.getLogger(__name__)


def get_oauth_flow(user):
    redirect_uri = "https://%s%s" % (os.environ['HTTP_HOST'], reverse("oauth2callback"))

    flow = client.flow_from_clientsecrets(
        settings.OAUTH_CONF_PATH,
        scope=settings.OAUTH_SCOPES,
        redirect_uri=redirect_uri,
        login_hint=user.email,
    )
    flow.params['access_type'] = 'offline'

    return flow


def update_subscriptions(user_id, last_pk=None):
    """Updates subscriptions"""
    try:
        subscriptions = {}

        subscriptions_qs = Subscription.objects.order_by("pk").filter(user_id=user_id)
        if last_pk:
            subscriptions_qs = subscriptions_qs.filter(pk__gt=last_pk)
        subscriptions_qs[:API_MAX_RESULTS]
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
                upload_playlist=None,  # must fetch this from the channel data
            )

        channel_list = youtube.channels() \
            .list(id=','.join(subscriptions.keys()), part='contentDetails', maxResults=API_MAX_RESULTS) \
            .execute()

        sub_size = len(subscription_list['items'])
        chan_size = len(channel_list['items'])
        assert sub_size == chan_size, "Subscription list and channel list are different sizes! (%s != %s)" % (sub_size, chan_size)

        for channel in channel_list['items']:
            subscriptions[channel['id']]['upload_playlist'] = channel['contentDetails']['relatedPlaylists']['uploads']

        sub_count = 0
        for obj in subscriptions_qs:
            if obj.channel_id not in subscriptions:
                # unsubscribed?
                continue

            sub_count += 1
            data = subscriptions[obj.channel_id]
            with transaction.atomic():
                obj.refresh_from_db()

                obj.last_update = data['last_update']
                obj.title = data['title']
                obj.description = data['description']
                obj.upload_playlist = data['upload_playlist']

                obj.save()

            bucket_ids = Bucket.objects.filter(subs_ids__contains=obj.pk).values_list('pk', flat=True)
            bucket_ids = list(bucket_ids)
            if len(bucket_ids) > 0:
                deferred.defer(import_videos, user_id, key, obj.upload_playlist, bucket_ids)

            last_pk = obj.pk

        assert sub_count == sub_size, "Subscription count mismatch: %s != %s" % (sub_count, sub_size)
    except RuntimeExceededError:
        pass

    deferred.defer(update_subscriptions, user_id, last_pk)


def new_subscriptions(user_id, page_token=None):
    """Import new subscriptions into the system

    Will ignore subscriptions that we already know about."""
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
                    upload_playlist=None,  # must fetch this from the channel data
                )

            channel_list = youtube.channels() \
                .list(id=','.join(subscriptions.keys()), part='contentDetails', maxResults=API_MAX_RESULTS) \
                .execute()

            sub_size = len(subscription_list['items'])
            chan_size = len(channel_list['items'])
            assert sub_size == chan_size, "Subscription list and channel list are different sizes! (%s != %s)" % (sub_size, chan_size)
            _log.debug("Importing batch of %s subscriptions", sub_size)

            for channel in channel_list['items']:
                subscriptions[channel['id']]['upload_playlist'] = channel['contentDetails']['relatedPlaylists']['uploads']

            for data in subscriptions.itervalues():
                key = data.pop('id')
                obj, created = Subscription.objects.get_or_create(id=key, defaults=data)
                _log.debug("Subscription %s%s created", obj.id, "" if created else " not")

            if 'nextPageToken' in subscription_list:
                page_token = subscription_list['nextPageToken']
            else:
                break
    except RuntimeExceededError:
        deferred.defer(new_subscriptions, user_id, page_token)


def import_videos(user_id, subscription_id, playlist, bucket_ids, page_token=None):
    try:
        youtube = get_service(user_id)
        while True:
            playlistitem_list = youtube.playlistItems() \
                .list(playlistId=playlist, part='contentDetails', pageToken=page_token, maxResults=API_MAX_RESULTS) \
                .execute()

            video_list = youtube.videos() \
                .list(id=','.join([v['contentDetails']['videoId'] for v in playlistitem_list['items']]), part='snippet', maxResults=API_MAX_RESULTS) \
                .execute()

            playlist_size = len(playlistitem_list['items'])
            video_size = len(video_list['items'])
            assert playlist_size == video_size, "Playlist item list and video list are different sizes! (%s != %s)" % (playlist_size, video_size)
            _log.debug("Importing batch of %s videos", video_size)

            for video in video_list['items']:
                data = dict(
                    subscription_id=subscription_id,
                    user_id=user_id,
                    title=video['snippet']['title'],
                    description=video['snippet']['description'],
                    youtube_id=video['id'],
                    buckets_ids=bucket_ids,
                )
                key = create_composite_key(str(user_id), video['id'])
                obj, created = Video.objects.update_or_create(id=key, defaults=data)
                _log.debug("Video %s%s created", obj.id, "" if created else " not")

            if 'nextPageToken' in playlistitem_list:
                break  # TODO: decide how far back we're going to go?
                #page_token = playlistitem_list['nextPageToken']
            else:
                break
    except RuntimeExceededError:
        deferred.defer(import_videos, user_id, subscription_id, playlist, page_token)


def get_service(user_id):
    token = OauthToken.objects.get(user_id=user_id)
    credentials = token.get()
    http = credentials.authorize(httplib2.Http())

    service = build(API_NAME, API_VERSION, http=http)
    return service
