##
#    Copyright (C) 2018  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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

from djangae.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods

from subscribae.decorators import active_user
from subscribae.models import Bucket, Subscription, Video, create_composite_key

API_PAGE_SIZE = 10

VIDEO_API_MAP = {
    "id": "youtube_id",
    "title": "title",
    "description": "description",
    "published": "published_at",
    "html_snippet": "html_snippet",
    "ordering_key": "ordering_key",
}


def queryset_to_json(qs, ordering, property_map=None, before=None, after=None, start=None, end=None):
    """Turn a queryset into a JSON object that can easily serialised into JSON
    """
    qs = qs.order_by(ordering)
    if ordering.startswith("-"):
        ordering = ordering[1:]

    if not isinstance(property_map, dict):
        raise ValueError("property_map should be a dict-like object")

    unique_kwargs = [before, after, start, end]
    if unique_kwargs.count(None) < (len(unique_kwargs) - 1):  # a maximum of 1 item may be not None
        raise TypeError("queryset_to_json may only take one of: before, after, start, end")

    if before is not None:
        qs = qs.filter(**{"{}__lt".format(ordering): before}).reverse()
    elif after is not None:
        qs = qs.filter(**{"{}__gt".format(ordering): after})
    elif start is not None:
        qs = qs.filter(**{"{}__gte".format(ordering): start})
    elif end is not None:
        qs = qs.filter(**{"{}__lte".format(ordering): end}).reverse()

    qs = qs[:API_PAGE_SIZE]

    items = []
    item_orderings = []
    for obj in qs:
        items.append({k: getattr(obj, v) for k, v in property_map.items()})
        item_orderings.append(getattr(obj, ordering))

    if len(items):
        first = item_orderings[0]
        last = item_orderings[-1]
    else:
        first = None
        last = None

    return (items, first, last)


@login_required
@active_user
@require_http_methods(("GET",))
def bucket_video(request, bucket):
    """Video API for buckets

    Also accepts POST requests for viewed videos
    """
    try:
        bucket_id = int(bucket)
    except ValueError:
        raise Http404

    qs = Video.objects.from_bucket(user=request.user, bucket=bucket_id)

    videos, first, last = queryset_to_json(qs, "ordering_key", VIDEO_API_MAP,
                                           before=request.GET.get("before"),
                                           after=request.GET.get("after"),
                                           start=request.GET.get("start"),
                                           end=request.GET.get("end"),
                                           )

    data = {"videos": videos}

    if len(videos) > 0:
        next_url = "{}?after={}".format(reverse("bucket-video-api", kwargs={"bucket": bucket_id}), last)
        data["next"] = next_url

    return JsonResponse(data)


@login_required
@active_user
@require_http_methods(("POST",))
def bucket_video_viewed(request, bucket):
    try:
        bucket_id = int(bucket)
    except ValueError:
        raise Http404

    try:
        key = create_composite_key(str(request.user.pk), request.POST["id"])
    except KeyError:
        raise Http404

    with transaction.atomic(xg=True):
        try:
            bucket_obj = Bucket.objects.get(id=bucket_id)
        except Bucket.DoesNotExist:
            raise Http404

        try:
            vid = Video.objects.from_bucket(user=request.user, bucket=bucket_id).get(id=key)
        except Video.DoesNotExist:
            raise Http404

        bucket_obj.last_watched_video = vid.ordering_key
        bucket_obj.save()

        vid.viewed = True
        vid.save()
    return JsonResponse({})


@login_required
@active_user
@require_http_methods(("GET",))
def subscription_video(request, subscription):
    """Video API for subscriptions"""
    qs = Video.objects.from_subscription(user=request.user, subscription=subscription)

    videos, first, last = queryset_to_json(qs, "ordering_key", VIDEO_API_MAP,
                                           before=request.GET.get("before"),
                                           after=request.GET.get("after"),
                                           start=request.GET.get("start"),
                                           end=request.GET.get("end"),
                                           )

    data = {"videos": videos}

    if len(videos) > 0:
        next_url = "{}?after={}".format(reverse("subscription-video-api", kwargs={"subscription": subscription}), last)
        data["next"] = next_url

    return JsonResponse(data)


@login_required
@active_user
@require_http_methods(("POST",))
def subscription_video_viewed(request, subscription):
    try:
        key = create_composite_key(str(request.user.pk), request.POST["id"])
    except KeyError:
        raise Http404

    with transaction.atomic(xg=True):
        try:
            subscription_obj = Subscription.objects.get(id=subscription)
        except Subscription.DoesNotExist:
            raise Http404

        try:
            vid = Video.objects.from_subscription(user=request.user, subscription=subscription).get(id=key)
        except Video.DoesNotExist:
            raise Http404

        subscription_obj.last_watched_video = vid.ordering_key
        subscription_obj.save()

        vid.viewed = True
        vid.save()
    return JsonResponse({})
