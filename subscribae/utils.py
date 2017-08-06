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

            data = subscriptions[obj.channel_id]
            with transaction.atomic():
                obj.refresh_from_db()

                obj.last_update = data['last_update']
                obj.title = data['title']
                obj.description = data['description']
                obj.upload_playlist = data['upload_playlist']

                obj.save()

            bucket_ids = Bucket.objects.filter(subs_ids=obj.pk).values_list('pk', flat=True)
            bucket_ids = list(bucket_ids)
            if len(bucket_ids) > 0:
                deferred.defer(import_videos, user_id, key, obj.upload_playlist, bucket_ids)

            last_pk = obj.pk

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
            ids_from_playlist = [item['contentDetails']['videoId'] for item in playlistitem_list['items']]

            video_list = youtube.videos() \
                .list(id=','.join(ids_from_playlist), part='snippet', maxResults=API_MAX_RESULTS) \
                .execute()
            ids_from_video = [video['id'] for video in video_list['items']]


            missing_videos = set(ids_from_playlist) - set(ids_from_video)
            extra_videos = set(ids_from_video) - set(ids_from_playlist)
            _log.info("Missing these IDs from the video list endpoint: %s", missing_videos)
            _log.info("Extra IDs from the video list endpoint: %s", extra_videos)

            for video in video_list['items']:
                if video['id'] not in ids_from_playlist:
                    continue

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
