##
#    Subscribae
#    Copyright (C) 2018  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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

from djangae.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import JsonResponse, Http404

from subscribae.models import Video, create_composite_key


API_PAGE_SIZE = 10

VIDEO_API_MAP = {
    "id": "youtube_id",
    "title": "title",
    "description": "description",
    "published": "published_at",
    "subscription": "subscription_title",
}


def queryset_to_json(qs, ordering, property_map=None, before=None, after=None):
    qs = qs.order_by(ordering)
    if ordering.startswith("-"):
        ordering = ordering[1:]

    if not isinstance(property_map, dict):
        raise ValueError("property_map should be a dict-like object")

    if before is not None:
        qs = qs.filter(**{"{}__lt".format(ordering): before}).reverse()
    elif after is not None:
        qs = qs.filter(**{"{}__gt".format(ordering): after})

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
def video(request, bucket):
    try:
        qs = Video.objects.filter(user=request.user, buckets__contains=int(bucket))
    except ValueError:
        raise Http404

    if request.method == "POST":
        with transaction.atomic():
            try:
                key = create_composite_key(str(request.user.pk), request.POST["id"])
                vid = qs.get(id=key)
            except (Video.DoesNotExist, KeyError):
                raise Http404

            vid.viewed = True
            vid.save()
        return JsonResponse({})
    else:
        before = request.GET.get("before")
        after = request.GET.get("after")

        videos, first, last = queryset_to_json(qs, "ordering_key", VIDEO_API_MAP, before, after)

        next_url = "{}?after={}".format(reverse("video-api", kwargs={"bucket": bucket}), last)

        return JsonResponse({"videos": videos, "next": next_url})
