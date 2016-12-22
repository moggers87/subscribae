import os

from apiclient.discovery import build
from django.conf import settings
from django.core.urlresolvers import reverse
from google.appengine.ext.deferred import deferred
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
from oauth2client import client
import httplib2

from subscribae.models import OauthToken


API_NAME = 'youtube'
API_VERSION = 'v3'


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
        subscription_list = youtube.subscriptions() \
            .list(mine=True, part='sniipet, contentDetails', pageToken=page_token) \
            .execute()
        for item in subscription_list:
            print item
    except RuntimeExceededError:
        deferred.defer(import_data_for_user, user_id, page_token)


def get_service(user_id):
    token = OauthToken.objects.get(user_id=user_id)
    credentials = token.get()
    http = credentials.authorize(httplib2.Http())

    service = build(API_NAME, API_VERSION, http=http)
    return service
