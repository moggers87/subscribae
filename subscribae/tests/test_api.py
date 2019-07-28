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

import json

from djangae.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
import mock

from subscribae.models import Video
from subscribae.test import gae_login, gae_logout
from subscribae.tests.utils import BucketFactory, VideoFactory
from subscribae.views.api import queryset_to_json


def datetime_to_js_iso(dt):
    js_iso = dt.isoformat()
    if dt.microsecond:
        js_iso = js_iso[:23] + js_iso[26:]
    if js_iso.endswith('+00:00'):
        js_iso = js_iso[:-6] + 'Z'

    return js_iso


class VideoApiTestCase(TestCase):
    def setUp(self):
        super(VideoApiTestCase, self).setUp()
        self.user = get_user_model().objects.create(username='1', email='test@example.com', is_active=True)
        gae_login(self.user)

    def tearDown(self):
        gae_logout()
        super(VideoApiTestCase, self).tearDown()

    def test_login_required(self):
        gae_logout()
        response = self.client.get(reverse("video-api", kwargs={"bucket": "123"}))
        self.assertRedirects(response, "{}?next={}".format(reverse("djangae_login_redirect"),
                             reverse("video-api", kwargs={"bucket": "123"})), fetch_redirect_response=False)

    def test_get_empty(self):
        bucket = BucketFactory()
        response = self.client.get(reverse("video-api", kwargs={"bucket": bucket.id}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {"videos": []})

    def test_get(self):
        bucket = BucketFactory(user=self.user)
        video = VideoFactory(user=self.user, buckets=[bucket])

        response = self.client.get(reverse("video-api", kwargs={"bucket": bucket.pk}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            "next": "{}?after={}".format(reverse("video-api", kwargs={"bucket": bucket.pk}), video.ordering_key),
            "videos": [{
                "id": video.youtube_id,
                "title": video.title,
                "description": video.description,
                "published": datetime_to_js_iso(video.published_at),
                "html_snippet": video.html_snippet,
                "ordering_key": video.ordering_key,
            }],
        })

    def test_get_with_start(self):
        bucket = BucketFactory(user=self.user)
        videos = VideoFactory.create_batch(3, user=self.user, buckets=[bucket])
        videos = sorted(videos, key=lambda v: v.ordering_key)

        response = self.client.get("{}?start={}".format(reverse("video-api",
                                                        kwargs={"bucket": bucket.pk}), videos[1].ordering_key))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["videos"]), 2)
        self.assertEqual(data, {
            "next": "{}?after={}".format(reverse("video-api", kwargs={"bucket": bucket.pk}), videos[2].ordering_key),
            "videos": [
                {
                    "id": videos[1].youtube_id,
                    "title": videos[1].title,
                    "description": videos[1].description,
                    "published": datetime_to_js_iso(videos[1].published_at),
                    "html_snippet": videos[1].html_snippet,
                    "ordering_key": videos[1].ordering_key,
                },
                {
                    "id": videos[2].youtube_id,
                    "title": videos[2].title,
                    "description": videos[2].description,
                    "published": datetime_to_js_iso(videos[2].published_at),
                    "html_snippet": videos[2].html_snippet,
                    "ordering_key": videos[2].ordering_key,
                },
            ],
        })

    def test_get_with_after(self):
        bucket = BucketFactory(user=self.user)
        videos = VideoFactory.create_batch(3, user=self.user, buckets=[bucket])
        videos = sorted(videos, key=lambda v: v.ordering_key)

        response = self.client.get("{}?after={}".format(reverse("video-api",
                                                        kwargs={"bucket": bucket.pk}), videos[0].ordering_key))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["videos"]), 2)
        self.assertEqual(data, {
            "next": "{}?after={}".format(reverse("video-api", kwargs={"bucket": bucket.pk}), videos[2].ordering_key),
            "videos": [
                {
                    "id": videos[1].youtube_id,
                    "title": videos[1].title,
                    "description": videos[1].description,
                    "published": datetime_to_js_iso(videos[1].published_at),
                    "html_snippet": videos[1].html_snippet,
                    "ordering_key": videos[1].ordering_key,
                },
                {
                    "id": videos[2].youtube_id,
                    "title": videos[2].title,
                    "description": videos[2].description,
                    "published": datetime_to_js_iso(videos[2].published_at),
                    "html_snippet": videos[2].html_snippet,
                    "ordering_key": videos[2].ordering_key,
                },
            ],
        })

    def test_post_not_found(self):
        data = {}
        response = self.client.post(reverse("video-api", kwargs={"bucket": "123"}), data=data)
        self.assertEqual(response.status_code, 404)

    def test_post_bad_bucket_id(self):
        video = VideoFactory(user=self.user)
        data = {"id": video.youtube_id}
        response = self.client.post(reverse("video-api", kwargs={"bucket": "cannot be cast to int"}), data=data)
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        video = VideoFactory(user=self.user, buckets=[BucketFactory(user=self.user)])
        data = {"id": video.youtube_id}
        response = self.client.post(reverse("video-api", kwargs={"bucket": video.buckets.first().pk}), data=data)
        self.assertEqual(response.status_code, 200)

        video.refresh_from_db()
        self.assertEqual(video.viewed, True)
        self.assertEqual(video.buckets.all()[0].last_watched_video, video.ordering_key)


class QuerySetToJsonTestCase(TestCase):
    def test_empty(self):
        qs = Video.objects.none()
        result = queryset_to_json(qs, "pk", {"id": "id"})

        self.assertEqual(result, ([], None, None))

    def test_pagination_options(self):
        videos = VideoFactory.create_batch(3)
        videos = sorted(videos, key=lambda v: v.id)

        qs = Video.objects.all()
        items, first, last = queryset_to_json(qs, "pk", {"id": "id"})
        self.assertEqual(items, [{"id": v.id} for v in videos])
        self.assertEqual(first, videos[0].pk)
        self.assertEqual(last, videos[2].pk)

    @mock.patch("subscribae.views.api.API_PAGE_SIZE", 2)
    def test_page_size(self):
        VideoFactory.create_batch(3)

        qs = Video.objects.all()
        items, _, _ = queryset_to_json(qs, "pk", {"id": "id"})
        self.assertEqual(len(items), 2)

    def test_before(self):
        videos = VideoFactory.create_batch(3)
        videos = sorted(videos, key=lambda v: v.pk)

        qs = Video.objects.all()
        items, first, last = queryset_to_json(qs, "pk", {"id": "id"}, before=videos[2].pk)
        self.assertEqual(items, [{"id": v.id} for v in reversed(videos[:2])])
        self.assertEqual(first, videos[1].pk)
        self.assertEqual(last, videos[0].pk)

    def test_after(self):
        videos = VideoFactory.create_batch(3)
        videos = sorted(videos, key=lambda v: v.pk)

        qs = Video.objects.all()
        items, first, last = queryset_to_json(qs, "pk", {"id": "id"}, after=videos[0].pk)
        self.assertEqual(items, [{"id": v.id} for v in videos[1:]])
        self.assertEqual(first, videos[1].pk)
        self.assertEqual(last, videos[2].pk)

    def test_start(self):
        videos = VideoFactory.create_batch(3)
        videos = sorted(videos, key=lambda v: v.pk)

        qs = Video.objects.all()
        items, first, last = queryset_to_json(qs, "pk", {"id": "id"}, start=videos[1].pk)
        self.assertEqual(items, [{"id": v.id} for v in videos[1:]])
        self.assertEqual(first, videos[1].pk)
        self.assertEqual(last, videos[2].pk)

    def test_end(self):
        videos = VideoFactory.create_batch(3)
        videos = sorted(videos, key=lambda v: v.pk)

        qs = Video.objects.all()
        items, first, last = queryset_to_json(qs, "pk", {"id": "id"}, end=videos[1].pk)
        self.assertEqual(items, [{"id": v.id} for v in reversed(videos[:2])])
        self.assertEqual(first, videos[1].pk)
        self.assertEqual(last, videos[0].pk)

    def test_property_map(self):
        video = VideoFactory()

        qs = Video.objects.all()
        items, _, _ = queryset_to_json(qs, "pk", {"bob": "title"})

        self.assertEqual(items[0].keys(), ["bob"])
        self.assertEqual(items[0]["bob"], video.title)

    def test_property_map_value_error(self):
        VideoFactory()

        qs = Video.objects.all()
        with self.assertRaises(ValueError):
            queryset_to_json(qs, "pk", (("id", "id"), ("title", "title")))

    def test_ordering(self):
        VideoFactory.create_batch(3)

        qs = Video.objects.all()
        forward, _, _ = queryset_to_json(qs, "pk", {"id": "id"})
        backward, _, _ = queryset_to_json(qs, "-pk", {"id": "id"})
        self.assertEqual(forward, list(reversed(backward)))
