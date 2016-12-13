from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden

from subscribae.models import OauthToken
from subscribae.utils import get_oauth_flow


def home(request):
    return HttpResponse("Hello")


def bucket(request, bucket):
    return HttpResponse("Hello %s" % bucket)


def subscription(request, subscription):
    return HttpResponse("Hello %s" % subscription)


def video(request, video):
    return HttpResponse("Hello %s" % video)


@login_required
def oauth_start(request):
    flow = get_oauth_flow(request.user)
    auth_uri = flow.step1_get_authorize_url()
    return HttpResponseRedirect(auth_uri)


@login_required
def oauth_callback(request):
    if "code" in request.GET:
        auth_code = request.GET["code"]
        flow = get_oauth_flow(request.user)

        credentials = flow.step2_exchange(auth_code)
        OauthToken.objects.update_or_create(user=request.user, defaults={'data': credentials.to_json()})

        return HttpResponseRedirect(reverse("home"))
    else:
        return HttpResponseForbidden("Something went wrong: %s" % request.GET)
