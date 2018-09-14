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

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from google.appengine.ext.deferred import deferred

from subscribae.forms import BucketForm, BucketEditForm
from subscribae.models import OauthToken, Subscription, Bucket
from subscribae.utils import new_subscriptions


def home(request):
    return TemplateResponse(request, 'subscribae/home.html', {})


@login_required
def overview(request):
    context = {
        'subscription_list': request.user.subscription_set.all(),
        'bucket_list': request.user.bucket_set.all(),
    }
    return TemplateResponse(request, 'subscribae/overview.html', context)


@login_required
def bucket(request, bucket):
    bucket = get_object_or_404(Bucket, pk=bucket, user=request.user)
    if request.method == "POST":
        form = BucketEditForm(instance=bucket, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("bucket", kwargs={"bucket": bucket.pk}))
    else:
        form = BucketEditForm(instance=bucket)
    context = {
        'bucket': bucket,
        'form': form,
    }
    return TemplateResponse(request, 'subscribae/bucket.html', context)


@login_required
@require_POST
def bucket_new(request):
    form = BucketForm(user=request.user, data=request.POST)
    if form.is_valid():
        bucket = form.save()
        return HttpResponseRedirect(reverse('bucket', kwargs={'bucket': bucket.pk}))

    return TemplateResponse(request, 'subscribae/bucket-new.html', {"form": form})


@login_required
def subscription(request, subscription):
    subscription = get_object_or_404(Subscription, pk=subscription, user=request.user)
    buckets = Bucket.objects.filter(subs__contains=subscription)
    context = {
        'subscription': subscription,
        'buckets': buckets,
    }
    return TemplateResponse(request, 'subscribae/subscription.html', context)


@login_required
def video(request, video):
    return HttpResponse("Hello %s" % video)


@login_required
def sync_subscription(request):
    if OauthToken.objects.filter(user_id=request.user.id).exists():
        deferred.defer(new_subscriptions, request.user.id)
        return HttpResponse("Sync started")
    else:
        request.session[settings.OAUTH_RETURN_SESSION_KEY] = 'sync'
        return HttpResponseRedirect(reverse('authorise'))
