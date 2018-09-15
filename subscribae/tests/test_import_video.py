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

from datetime import datetime

from djangae.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
from pytz import UTC
import mock

from subscribae.models import Subscription, OauthToken, Video, create_composite_key
from subscribae.utils import import_videos, API_MAX_RESULTS
from subscribae.tests.utils import MockExecute, BucketFactory


class ImportVideoTasksTestCase(TestCase):
    @mock.patch('subscribae.utils.deferred')
    @mock.patch('subscribae.utils.get_service')
    def test_import_videos(self, service_mock, defer_mock):
        playlistitems_mock = service_mock.return_value.playlistItems.return_value.list
        videos_mock = service_mock.return_value.videos.return_value.list

        playlistitems_mock.return_value.execute.return_value = {
            'items': [
                {'contentDetails': {'videoId': 'video123'}},
                {'contentDetails': {'videoId': 'video456'}},
            ],
        }
        videos_mock.return_value.execute.return_value = {
            'items': [
                {
                    'id': 'video123',
                    'snippet': {
                        'title': 'my video',
                        'description': 'this is my video',
                        'thumbnails': {},
                        'publishedAt': '1997-07-16T19:20:30.45Z',
                    },
                },
                {
                    'id': 'video456',
                    'snippet': {
                        'title': 'my other video',
                        'description': 'this is my other video',
                        'thumbnails': {},
                        'publishedAt': '1997-07-16T19:20:30.45Z',
                    },
                },
            ],
        }

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=timezone.now())
        bucket = BucketFactory(user=user, subs=[subscription])

        import_videos(user.id, subscription.id, "upload123", [bucket.id])
        self.assertEqual(playlistitems_mock.call_count, 1)
        self.assertEqual(videos_mock.call_count, 1)
        self.assertEqual(defer_mock.call_count, 0)

        self.assertEqual(playlistitems_mock.call_args, (
            (),
            {'playlistId': 'upload123', 'part': 'contentDetails', 'maxResults': API_MAX_RESULTS, 'pageToken': None}
        ))
        self.assertEqual(videos_mock.call_args, (
            (),
            {'id': 'video123,video456', 'part': 'snippet', 'maxResults': API_MAX_RESULTS}
        ))

        self.assertEqual(Video.objects.count(), 2)
        video1 = Video.objects.get(youtube_id="video123")
        self.assertEqual(video1.title, "my video")
        self.assertEqual(video1.description, "this is my video")
        self.assertEqual(video1.published_at, datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC))
        self.assertEqual(video1.ordering_key,
                         create_composite_key(str(datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC)), "video123"))
        video2 = Video.objects.get(youtube_id="video456")
        self.assertEqual(video2.title, "my other video")
        self.assertEqual(video2.description, "this is my other video")
        self.assertEqual(video2.published_at, datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC))
        self.assertEqual(video2.ordering_key,
                         create_composite_key(str(datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC)), "video456"))

    @mock.patch('subscribae.utils.get_service')
    def test_import_videos_pagination(self, service_mock):
        playlistitems_mock = service_mock.return_value.playlistItems.return_value.list

        playlistitems_mock.return_value.execute = MockExecute([
            {
                'items': [],
                'nextPageToken': '123',
            },
            {
                'items': [],
            },
        ])

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=timezone.now())
        bucket = BucketFactory(user=user, subs=[subscription])

        import_videos(user.id, subscription.id, "upload123", [bucket.id])
        self.assertEqual(playlistitems_mock.call_count, 2)

        self.assertEqual(playlistitems_mock.call_args_list, [
            ((), {'part': 'contentDetails', 'playlistId': 'upload123',
                  'maxResults': API_MAX_RESULTS, 'pageToken': None}),
            ((), {'part': 'contentDetails', 'playlistId': 'upload123',
                  'maxResults': API_MAX_RESULTS, 'pageToken': '123'}),
        ])

    @mock.patch('subscribae.utils.deferred')
    @mock.patch('subscribae.utils.get_service')
    def test_import_videos_runtime_exceeded(self, service_mock, defer_mock):
        playlistitems_mock = service_mock.return_value.playlistItems.return_value.list

        playlistitems_mock.return_value.execute = MockExecute([
            {
                'items': [],
                'nextPageToken': '123',
            },
            RuntimeExceededError(),
        ])

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=timezone.now())
        bucket = BucketFactory(user=user, subs=[subscription])

        import_videos(user.id, subscription.id, "upload123", [bucket.id])
        self.assertEqual(playlistitems_mock.call_count, 2)
        self.assertEqual(defer_mock.defer.call_count, 1)
        self.assertEqual(defer_mock.defer.call_args, (
            (import_videos, user.id, subscription.id, "upload123", [bucket.id]),
            {"page_token": "123", "only_first_page": False},
        ))

    @mock.patch('subscribae.utils.get_service')
    def test_import_videos_only_first_page(self, service_mock):
        playlistitems_mock = service_mock.return_value.playlistItems.return_value.list

        playlistitems_mock.return_value.execute = MockExecute([
            {
                'items': [],
                'nextPageToken': '123',
            },
            {
                'items': [],
            },
        ])

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=timezone.now())
        bucket = BucketFactory(user=user, subs=[subscription])

        import_videos(user.id, subscription.id, "upload123", [bucket.id], only_first_page=True)
        self.assertEqual(playlistitems_mock.call_count, 1)

        self.assertEqual(playlistitems_mock.call_args_list, [
            ((), {'part': 'contentDetails', 'playlistId': 'upload123',
                  'maxResults': API_MAX_RESULTS, 'pageToken': None}),
        ])

    @mock.patch('subscribae.utils.get_service')
    def test_import_videos_only_first_page_and_page_token(self, service_mock):
        service_mock

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=timezone.now())

        import_videos(user.id, subscription.id, "upload123", [], page_token="123", only_first_page=True)
        self.assertEqual(service_mock.call_count, 0)

    @mock.patch('subscribae.utils.deferred')
    @mock.patch('subscribae.utils.get_service')
    def test_import_videos_already_got(self, service_mock, defer_mock):
        playlistitems_mock = service_mock.return_value.playlistItems.return_value.list
        videos_mock = service_mock.return_value.videos.return_value.list

        playlistitems_mock.return_value.execute.return_value = {
            'items': [
                {'contentDetails': {'videoId': 'video123'}},
                {'contentDetails': {'videoId': 'video456'}},
            ],
            'nextPageToken': '123',
        }
        videos_mock.return_value.execute.return_value = {
            'items': [
                {
                    'id': 'video123',
                    'snippet': {
                        'title': 'my video',
                        'description': 'this is my video',
                        'thumbnails': {},
                        'publishedAt': '1997-07-16T19:20:30.45Z',
                    },
                },
                {
                    'id': 'video456',
                    'snippet': {
                        'title': 'my other video',
                        'description': 'this is my other video',
                        'thumbnails': {},
                        'publishedAt': '1997-07-16T19:20:30.45Z',
                    },
                },
            ],
        }

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=timezone.now())
        bucket = BucketFactory(user=user, subs=[subscription])

        Video.objects.create(user=user, subscription=subscription, youtube_id="video456", published_at=timezone.now())

        import_videos(user.id, subscription.id, "upload123", [bucket.id])
        self.assertEqual(playlistitems_mock.call_count, 1)
        self.assertEqual(videos_mock.call_count, 1)
        self.assertEqual(defer_mock.call_count, 0)

        self.assertEqual(playlistitems_mock.call_args, (
            (),
            {'playlistId': 'upload123', 'part': 'contentDetails', 'maxResults': API_MAX_RESULTS, 'pageToken': None}
        ))
        self.assertEqual(videos_mock.call_args, (
            (),
            {'id': 'video123,video456', 'part': 'snippet', 'maxResults': API_MAX_RESULTS}
        ))

        self.assertEqual(Video.objects.count(), 2)
        video1 = Video.objects.get(youtube_id="video123")
        self.assertEqual(video1.title, "my video")
        self.assertEqual(video1.description, "this is my video")
        self.assertEqual(video1.published_at, datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC))
        self.assertEqual(video1.ordering_key,
                         create_composite_key(str(datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC)), "video123"))
        video2 = Video.objects.get(youtube_id="video456")
        self.assertEqual(video2.title, "")
        self.assertEqual(video2.description, "")
        self.assertNotEqual(video2.published_at, datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC))
        self.assertNotEqual(video2.ordering_key,
                         create_composite_key(str(datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC)), "video456"))

    def test_missing_oauth_token(self):
        user = get_user_model().objects.create(username='1')
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=timezone.now())
        bucket = BucketFactory(user=user, subs=[subscription])

        import_videos(user.id, subscription.id, "upload123", [bucket.id])
