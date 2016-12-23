import os

from apiclient.discovery import build
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from google.appengine.ext.deferred import deferred
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
from oauth2client import client
import httplib2

from subscribae.models import Subscription, OauthToken, create_composite_key



API_NAME = 'youtube'
API_VERSION = 'v3'
API_MAX_RESULTS = 10


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


def import_data_for_user(user_id, page_token=None):
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
                    title=item["snippet"]["title"],
                    description=item["snippet"]["description"],
                    upload_playlist=None,  # must fetch this from the channel data
                )

            channel_list = youtube.channels() \
                .list(id=",".join(subscriptions.keys()), part='contentDetails', maxResults=API_MAX_RESULTS) \
                .execute()

            sub_size = len(subscription_list['items'])
            chan_size = len(channel_list['items'])
            assert sub_size == chan_size, "Subscription list and channel list are different sizes! (%s != %s)" % (sub_size, chan_size)

            for channel in channel_list['items']:
                subscriptions[channel["id"]]["upload_playlist"] = channel["contentDetails"]["relatedPlaylists"]["uploads"]

            for sub in subscriptions.itervalues():
                key = sub.pop("id")
                Subscription.objects.update_or_create(id=key, defaults=sub)

            if 'nextPageToken' in subscription_list:
                page_token = subscription_list['nextPageToken']
            else:
                break
    except RuntimeExceededError:
        deferred.defer(import_data_for_user, user_id, page_token)


def get_service(user_id):
    token = OauthToken.objects.get(user_id=user_id)
    credentials = token.get()
    http = credentials.authorize(httplib2.Http())

    service = build(API_NAME, API_VERSION, http=http)
    return service
