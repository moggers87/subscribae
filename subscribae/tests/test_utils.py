##
#    Copyright (C) 2019  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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

from djangae.test import TestCase
from django.core.cache import cache
from google.appengine.api import memcache
import mock

from subscribae.models import OauthToken
from subscribae.tests.utils import SubscriptionFactory, UserFactory, VideoFactory
from subscribae.utils import (SUBSCRIPTION_TITLE_CACHE_PREFIX, VIDEO_TITLE_CACHE_PREFIX, get_service,
                              subscription_add_titles, video_add_titles)


class GetServiceTestCase(TestCase):
    def test_get_service_no_user(self):
        with self.assertRaises(OauthToken.DoesNotExist):
            get_service(1)

    def test_get_service_no_token(self):
        user = UserFactory()
        with self.assertRaises(OauthToken.DoesNotExist):
            get_service(user.pk)

    def test_get_service_no_oauth_data(self):
        user = UserFactory()
        OauthToken.objects.create(user=user, data={})

        with self.assertRaises(KeyError):
            get_service(user.pk)

    @mock.patch("subscribae.utils.build")
    @mock.patch("subscribae.models.Credentials")
    def test_get_service_without_cache(self, credentials, build):
        user = UserFactory()
        OauthToken.objects.create(user=user, data='{}')

        service = get_service(user.pk, False)

        authorize = credentials.new_from_json.return_value.authorize
        self.assertEqual(build.call_count, 1)
        self.assertEqual(build.return_value, service)
        self.assertEqual(build.call_args, (("youtube", "v3"), {"http": authorize.return_value}))
        self.assertEqual(authorize.call_count, 1)
        self.assertEqual(authorize.call_args[0][0].cache, None)
        self.assertEqual(credentials.new_from_json.call_count, 1)
        self.assertEqual(credentials.new_from_json.call_args, ((u"{}",), {}))

    @mock.patch("subscribae.utils.build")
    @mock.patch("subscribae.models.Credentials")
    def test_get_service_with_cache(self, credentials, build):
        user = UserFactory()
        OauthToken.objects.create(user=user, data='{}')

        service = get_service(user.pk)

        authorize = credentials.new_from_json.return_value.authorize
        self.assertEqual(build.call_count, 1)
        self.assertEqual(build.return_value, service)
        self.assertEqual(build.call_args, (("youtube", "v3"), {"http": authorize.return_value}))
        self.assertEqual(authorize.call_count, 1)
        self.assertEqual(authorize.call_args[0][0].cache, memcache)
        self.assertEqual(credentials.new_from_json.call_count, 1)
        self.assertEqual(credentials.new_from_json.call_args, ((u"{}",), {}))


class AddTitlesSubscriptionTestCase(TestCase):
    def setUp(self):
        super(AddTitlesSubscriptionTestCase, self).setUp()

        self.service_patch = mock.patch('subscribae.utils.get_service')
        self.service_mock = self.service_patch.start()

        self.channel_mock = self.service_mock.return_value.channels.return_value.list

        self.channel_mock.return_value.execute.return_value = {
            'items': [
                {
                    'id': '123',
                    'snippet': {
                        "title": "henlo",
                        "description": "bluh bluh",
                    },
                },
                {
                    'id': '456',
                    'snippet': {
                        "title": "bye-q",
                        "description": "blah blah",
                    },
                },
            ],
        }

    def tearDown(self):
        mock.patch.stopall()

    def test_clean_cache(self):
        sub = SubscriptionFactory.build(channel_id="123")

        cached_data = cache.get(SUBSCRIPTION_TITLE_CACHE_PREFIX + "123")
        self.assertEqual(cached_data, None)

        results = list(subscription_add_titles([sub]))
        self.assertEqual(results, [sub])

        self.assertEqual(sub.title, "henlo")
        self.assertEqual(sub.description, "bluh bluh")

        self.assertEqual(self.channel_mock.call_count, 1)
        self.assertEqual(self.channel_mock.call_args[1]["id"], "123")

        cached_data = cache.get(SUBSCRIPTION_TITLE_CACHE_PREFIX + "123")
        self.assertEqual(cached_data, {"title": "henlo", "description": "bluh bluh"})

    def test_cache_populated(self):
        sub = SubscriptionFactory.build(channel_id="123")

        cache.set(SUBSCRIPTION_TITLE_CACHE_PREFIX + "123", {"title": "henlo", "description": "bluh bluh"})

        results = list(subscription_add_titles([sub]))
        self.assertEqual(results, [sub])

        self.assertEqual(sub.title, "henlo")
        self.assertEqual(sub.description, "bluh bluh")

        self.assertEqual(self.channel_mock.call_count, 0)

    def test_no_objects(self):
        results = list(subscription_add_titles([]))
        self.assertEqual(results, [])
        self.assertEqual(self.channel_mock.call_count, 0)


class AddTitlesVideoTestCase(TestCase):
    def setUp(self):
        super(AddTitlesVideoTestCase, self).setUp()

        self.service_patch = mock.patch('subscribae.utils.get_service')
        self.service_mock = self.service_patch.start()

        self.video_mock = self.service_mock.return_value.videos.return_value.list

        self.video_mock.return_value.execute.return_value = {
            'items': [
                {
                    'id': '123',
                    'snippet': {
                        "title": "henlo",
                        "description": "bluh bluh",
                    },
                },
                {
                    'id': '456',
                    'snippet': {
                        "title": "bye-q",
                        "description": "blah blah",
                    },
                },
            ],
        }

    def tearDown(self):
        mock.patch.stopall()

    def test_clean_cache(self):
        vid = VideoFactory.build(youtube_id="123")

        cached_data = cache.get(VIDEO_TITLE_CACHE_PREFIX + "123")
        self.assertEqual(cached_data, None)

        results = list(video_add_titles([vid]))
        self.assertEqual(results, [vid])

        self.assertEqual(vid.title, "henlo")
        self.assertEqual(vid.description, "bluh bluh")

        self.assertEqual(self.video_mock.call_count, 1)
        self.assertEqual(self.video_mock.call_args[1]["id"], "123")

        cached_data = cache.get(VIDEO_TITLE_CACHE_PREFIX + "123")
        self.assertEqual(cached_data, {"title": "henlo", "description": "bluh bluh"})

    def test_cache_populated(self):
        vid = VideoFactory.build(youtube_id="123")

        cache.set(VIDEO_TITLE_CACHE_PREFIX + "123", {"title": "henlo", "description": "bluh bluh"})

        results = list(video_add_titles([vid]))
        self.assertEqual(results, [vid])

        self.assertEqual(vid.title, "henlo")
        self.assertEqual(vid.description, "bluh bluh")

        self.assertEqual(self.video_mock.call_count, 0)

    def test_no_objects(self):
        results = list(video_add_titles([]))
        self.assertEqual(results, [])
        self.assertEqual(self.video_mock.call_count, 0)
