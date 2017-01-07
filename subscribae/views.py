from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from google.appengine.ext.deferred import deferred

from subscribae.models import OauthToken
from subscribae.utils import get_oauth_flow, import_subscriptions


OAUTH_RETURN_SESSION_KEY = 'subscribae-oauth-return-url-name'


def home(request):
    return HttpResponse("Hello")


@login_required
def bucket(request, bucket):
    return HttpResponse("Hello %s" % bucket)


@login_required
def subscription(request, subscription):
    return HttpResponse("Hello %s" % subscription)


@login_required
def video(request, video):
    return HttpResponse("Hello %s" % video)


@login_required
def sync_subscription(request):
    if OauthToken.objects.filter(user_id=request.user.id).exists():
        deferred.defer(import_subscriptions, request.user.id)
        return HttpResponse("Sync started")
    else:
        request.session[OAUTH_RETURN_SESSION_KEY] = 'sync'
        return HttpResponseRedirect(reverse('authorise'))


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

        redirect_uri = reverse(request.session.get(OAUTH_RETURN_SESSION_KEY, 'home'))
        return HttpResponseRedirect(redirect_uri)
    else:
        return HttpResponseForbidden("Something went wrong: %s" % request.GET)
