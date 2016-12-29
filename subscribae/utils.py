import logging
import os

from apiclient.discovery import build
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from google.appengine.ext.deferred import deferred
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
from oauth2client import client
import httplib2

from subscribae.models import Video, Subscription, OauthToken, create_composite_key


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


def import_subscriptions(user_id, page_token=None):
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

            for sub in subscriptions.itervalues():
                key = sub.pop('id')
                obj, created = Subscription.objects.update_or_create(id=key, defaults=sub)
                deferred.defer(import_videos, user_id, key, sub['upload_playlist'])
                _log.debug("Subscription %s%s created", obj.id, "" if created else " not")

            if 'nextPageToken' in subscription_list:
                page_token = subscription_list['nextPageToken']
            else:
                break

    except RuntimeExceededError:
        deferred.defer(import_subscriptions, user_id, page_token)


def import_videos(user_id, subscription_id, playlist, page_token=None):
    try:
        youtube = get_service(user_id)
        while True:
            playlistitem_list = youtube.playlistItems() \
                .list(id=playlist, part='contentDetails', pageToken=page_token, maxResults=API_MAX_RESULTS) \
                .execute()

            video_list = youtube.videos() \
                .list(id=','.join([v['videoId'] for v in playlistitem_list['items']]), part='snippet', maxResults=API_MAX_RESULTS) \
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
