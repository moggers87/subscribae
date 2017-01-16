from datetime import datetime
from exceptions import BaseException
from unittest import skip
import os

from djangae.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
import mock

from subscribae.models import Bucket, Subscription, OauthToken, create_composite_key
from subscribae.utils import import_subscriptions, import_videos, API_MAX_RESULTS


class MockExecute(object):
    '''A callable that iterates over return values

    Useful for mocking functions/methods that have varying output. Exceptions
    must be instantiated.
    '''
    def __init__(self, return_values):
        self.return_values = return_values[:]
        self.return_values.reverse()

    def __call__(self, *args, **kwargs):
        value = self.return_values.pop()
        if isinstance(value, BaseException):
            raise value
        else:
            return value


class ViewTestCase(TestCase):
    """Mostly just smoke tests to make sure things are working"""
    def setUp(self):
        super(ViewTestCase, self).setUp()
        os.environ['USER_EMAIL'] = 'test@example.com'
        os.environ['USER_ID'] = '1'
        self.user = get_user_model().objects.create(username='1', email='test@example.com')

    def tearDown(self):
        del os.environ['USER_EMAIL']
        del os.environ['USER_ID']
        super(ViewTestCase, self).tearDown()

    def test_home(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_bucket(self):
        response = self.client.get(reverse('bucket', kwargs={'bucket': 1}))
        self.assertEqual(response.status_code, 200)

    def test_subscription(self):
        response = self.client.get(reverse('subscription', kwargs={'subscription': 1}))
        self.assertEqual(response.status_code, 200)

    def test_video(self):
        response = self.client.get(reverse('video', kwargs={'video': 1}))
        self.assertEqual(response.status_code, 200)

    def test_sync(self):
        response = self.client.get(reverse('sync'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('authorise'))

        user = get_user_model().objects.get(username='1')
        OauthToken.objects.create(user=user)

        response = self.client.get(reverse('sync'))
        self.assertEqual(response.status_code, 200)

    @mock.patch('subscribae.utils.client')
    def test_oauth_start(self, client):
        client.flow_from_clientsecrets.return_value.step1_get_authorize_url.return_value = 'https://myserver/auth'

        response = self.client.get(reverse('authorise'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response['Location'].startswith('https://myserver/auth'),
            response['Location']
        )

    @mock.patch('subscribae.utils.client')
    def test_oauth_callback(self, client):
        client.flow_from_clientsecrets.return_value.step2_exchange.return_value.to_json.return_value = {'test': 'value'}

        response = self.client.get(reverse('oauth2callback'))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('oauth2callback') + '?code=1234')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('home'))


class ImportTasksTestCase(TestCase):

    # video imports

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
                    },
                },
                {
                    'id': 'video456',
                    'snippet': {
                        'title': 'my other video',
                        'description': 'this is my other video',
                    },
                },
            ],
        }

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=datetime.now())

        import_videos(user.id, subscription.id, "upload123")
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

    @skip("Not implemented")
    @mock.patch('subscribae.utils.get_service')
    def test_import_videos_pagination(self, service_mock):
        class MockExecute(object):
            def __init__(self, return_values):
                self.return_values = return_values[:]
                self.return_values.reverse()

            def __call__(self, *args, **kwargs):
                value = self.return_values.pop()
                if isinstance(value, Exception):
                    raise value
                else:
                    return value

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
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=datetime.now())

        import_videos(user.id, subscription.id, "upload123")
        self.assertEqual(playlistitems_mock.call_count, 2)

        self.assertEqual(playlistitems_mock.call_args_list,
        [
            ((), {'mine': True, 'part': 'snippet', 'maxResults': API_MAX_RESULTS, 'pageToken': None}),
            ((), {'mine': True, 'part': 'snippet', 'maxResults': API_MAX_RESULTS, 'pageToken': '123'}),
        ])

    @skip("Not implemented")
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
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=datetime.now())

        import_videos(user.id, subscription.id, "upload123")
        self.assertEqual(playlistitems_mock.call_count, 2)
        self.assertEqual(defer_mock.defer.call_count, 1)
        self.assertEqual(defer_mock.defer.call_args, (
            (import_videos, user.id, '123'),
            {},
        ))

    # Subscription imports

    @mock.patch('subscribae.utils.deferred')
    @mock.patch('subscribae.utils.get_service')
    def test_import_subscriptions(self, service_mock, defer_mock):
        subscription_mock = service_mock.return_value.subscriptions.return_value.list
        channel_mock = service_mock.return_value.channels.return_value.list

        subscription_mock.return_value.execute.return_value = {
            'items': [
                {
                    'snippet': {
                        'title': 'A channel',
                        'description': "It's a channel",
                        'resourceId': {'channelId': '123'},
                    },
                },
                {
                    'snippet': {
                        'title': 'Another channel',
                        'description': "It's another channel",
                        'resourceId': {'channelId': '456'},
                    },
                },
            ],
        }

        channel_mock.return_value.execute.return_value = {
            'items': [
                {
                    'id': '123',
                    'contentDetails': {
                        'relatedPlaylists': {'uploads': 'upload123'},
                    },
                },
                {
                    'id': '456',
                    'contentDetails': {
                        'relatedPlaylists': {'uploads': 'upload456'},
                    },
                },
            ],
        }

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})

        import_subscriptions(user.id)
        self.assertEqual(subscription_mock.call_count, 1)
        self.assertEqual(channel_mock.call_count, 1)
        self.assertEqual(defer_mock.defer.call_count, 0)

        self.assertEqual(subscription_mock.call_args, (
            (),
            {'mine': True, 'part': 'snippet', 'maxResults': API_MAX_RESULTS, 'pageToken': None}
        ))
        self.assertEqual(channel_mock.call_args, (
            (),
            {'id': '123,456', 'part': 'contentDetails', 'maxResults': API_MAX_RESULTS}
        ))

        subscriptions = Subscription.objects.all()
        bucket = Bucket.objects.create(user=user, subs=subscriptions, last_update=datetime.now())

        import_subscriptions(user.id)
        self.assertEqual(subscription_mock.call_count, 2)
        self.assertEqual(channel_mock.call_count, 2)
        self.assertEqual(defer_mock.defer.call_count, 2)

        self.assertEqual(defer_mock.defer.call_args_list,
            [
                ((import_videos, user.id, create_composite_key(str(user.id), '123'), 'upload123', [bucket.id]), {}),
                ((import_videos, user.id, create_composite_key(str(user.id), '456'), 'upload456', [bucket.id]), {}),
            ],
        )

    @mock.patch('subscribae.utils.get_service')
    def test_import_subscriptions_pagination(self, service_mock):
        class MockExecute(object):
            def __init__(self, return_values):
                self.return_values = return_values[:]
                self.return_values.reverse()

            def __call__(self, *args, **kwargs):
                value = self.return_values.pop()
                if isinstance(value, Exception):
                    raise value
                else:
                    return value

        subscription_mock = service_mock.return_value.subscriptions.return_value.list

        subscription_mock.return_value.execute = MockExecute([
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

        import_subscriptions(user.id)
        self.assertEqual(subscription_mock.call_count, 2)

        self.assertEqual(subscription_mock.call_args_list,
        [
            ((), {'mine': True, 'part': 'snippet', 'maxResults': API_MAX_RESULTS, 'pageToken': None}),
            ((), {'mine': True, 'part': 'snippet', 'maxResults': API_MAX_RESULTS, 'pageToken': '123'}),
        ])

    @mock.patch('subscribae.utils.deferred')
    @mock.patch('subscribae.utils.get_service')
    def test_import_subscriptions_runtime_exceeded(self, service_mock, defer_mock):
        subscription_mock = service_mock.return_value.subscriptions.return_value.list

        subscription_mock.return_value.execute = MockExecute([
            {
                'items': [],
                'nextPageToken': '123',
            },
            RuntimeExceededError(),
        ])

        user = get_user_model().objects.create(username='1')
        OauthToken.objects.create(user=user, data={})

        import_subscriptions(user.id)
        self.assertEqual(subscription_mock.call_count, 2)
        self.assertEqual(defer_mock.defer.call_count, 1)
        self.assertEqual(defer_mock.defer.call_args, (
            (import_subscriptions, user.id, '123'),
            {},
        ))
