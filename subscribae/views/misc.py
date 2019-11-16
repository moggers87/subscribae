##
#    Copyright (C) 2016  Matt Molyneaux <moggers87+git@moggers87.co.uk>
#
#    This file is part of Subscribae.
#
#    Subscribae is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Subscribae is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with Subscribae.  If not, see <http://www.gnu.org/licenses/>.
##

import os

from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from google.appengine.api import users
from google.appengine.ext.deferred import deferred

from subscribae.decorators import active_user
from subscribae.forms import BucketEditForm, BucketForm
from subscribae.models import Bucket, OauthToken, Subscription
from subscribae.utils import subscriptions


def home(request):
    return TemplateResponse(request, 'subscribae/home.html', {})


@login_required
@active_user
def overview(request):
    context = {
        'subscription_list': request.user.subscription_set.all().add_titles(),
        'bucket_list': request.user.bucket_set.all(),
        'form': BucketForm(user=request.user),
    }
    return TemplateResponse(request, 'subscribae/overview.html', context)


@login_required
@active_user
def bucket(request, bucket):
    bucket = get_object_or_404(Bucket, pk=bucket, user=request.user)
    video_start_from = request.GET.get("start")
    context = {
        'bucket': bucket,
        'start': video_start_from,
    }
    return TemplateResponse(request, 'subscribae/bucket.html', context)


@require_POST
@login_required
@active_user
def bucket_new(request):
    form = BucketForm(user=request.user, data=request.POST)
    if form.is_valid():
        bucket = form.save()
        return HttpResponseRedirect(reverse('bucket', kwargs={'bucket': bucket.pk}))

    return TemplateResponse(request, 'subscribae/bucket-new.html', {"form": form})


@login_required
@active_user
def bucket_edit(request, bucket):
    bucket = get_object_or_404(Bucket, pk=bucket, user=request.user)

    if request.method == "POST":
        form = BucketEditForm(instance=bucket, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("bucket", kwargs={"bucket": bucket.pk}))
    else:
        form = BucketEditForm(instance=bucket)

    return TemplateResponse(request, 'subscribae/bucket-edit.html', {"form": form})


@login_required
@active_user
def subscription(request, subscription):
    subscription = get_object_or_404(Subscription, pk=subscription, user=request.user)
    buckets = Bucket.objects.filter(subs__contains=subscription)
    context = {
        'subscription': subscription.add_titles(),
        'buckets': buckets,
    }
    return TemplateResponse(request, 'subscribae/subscription.html', context)


@login_required
@active_user
def sync_subscription(request):
    if OauthToken.objects.filter(user_id=request.user.id).exists():
        deferred.defer(subscriptions, request.user.id)
        return HttpResponse("Sync started")
    else:
        request.session[settings.OAUTH_RETURN_SESSION_KEY] = 'sync'
        return HttpResponseRedirect(reverse('authorise'))


@login_required
def logout(request):
    django_logout(request)
    logout_url = users.create_logout_url(reverse("home"))
    return HttpResponseRedirect(logout_url)


def source(request):
    version = os.environ["CURRENT_VERSION_ID"]
    return TemplateResponse(request, 'subscribae/source.html', {'version': version})


def styleguide(request):
    return TemplateResponse(request, 'subscribae/styleguide.html', {})
