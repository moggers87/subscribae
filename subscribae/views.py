from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse

from oauth2client import client


def home(request):
    return HttpResponse("Hello")


def bucket(request, bucket):
    return HttpResponse("Hello %s" % bucket)


def subscription(request, subscription):
    return HttpResponse("Hello %s" % subscription)


def video(request, video):
    return HttpResponse("Hello %s" % video)


def oauth_callback(request):
    flow = client.flow_from_clientsecrets(
        settings.OAUTH_SETTINGS,
        scope=settings.OAUTH_SCOPES,
        redirect_uri=reverse("oauth2callback"),
    )
    if "code" not in request.GET:
        auth_uri = flow.step1_get_authorize_url()
        return HttpResponseRedirect(auth_uri)
    else:
        auth_code = request.GET["code"]
        credentials = flow.step2_exchange(auth_code)
        # TODO find out what fields are needed
        #OauthToken.objects.create(**credentials.to_json())
        return reverse("home")
