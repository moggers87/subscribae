import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect

from oauth2client import client

from subscribae.models import OauthToken


def home(request):
    return HttpResponse("Hello")


def bucket(request, bucket):
    return HttpResponse("Hello %s" % bucket)


def subscription(request, subscription):
    return HttpResponse("Hello %s" % subscription)


def video(request, video):
    return HttpResponse("Hello %s" % video)


@login_required
def oauth_callback(request):
    redirect_uri = "https://%s%s" % (os.environ['HTTP_HOST'], reverse("oauth2callback"))
    flow = client.flow_from_clientsecrets(
        settings.OAUTH_CONF_PATH,
        scope=settings.OAUTH_SCOPES,
        redirect_uri=redirect_uri,
        login_hint=request.user.email,
    )

    # TODO: deal with errors. Maybe initial Oauth should be a separate view?
    if "code" not in request.GET:
        auth_uri = flow.step1_get_authorize_url()
        return HttpResponseRedirect(auth_uri)
    else:
        auth_code = request.GET["code"]
        credentials = flow.step2_exchange(auth_code)
        OauthToken.objects.update_or_create(user=request.user, defaults={'data': credentials.to_json()})

        return HttpResponseRedirect(reverse("home"))
