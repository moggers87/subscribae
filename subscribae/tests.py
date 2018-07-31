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
from datetime import timedelta
from exceptions import BaseException
from unittest import skip
import os

from djangae.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import timezone
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
import factory
import factory.fuzzy
import mock

from subscribae.models import Bucket, Subscription, OauthToken, create_composite_key
from subscribae.utils import new_subscriptions, update_subscriptions, import_videos, API_MAX_RESULTS


class MockExecute(object):
    '''A callable that iterates over return values

    Useful for mocking functions/methods that have varying output. Exceptions
    must be instantiated.
    '''
    def __init__(self, return_values):
        self.return_values = return_values[:]
        self.return_values.reverse()

    def __call__(self, *args, **kwargs):
        try:
            self.last_value = self.return_values.pop()
        except IndexError:
            pass

        if isinstance(self.last_value, BaseException):
            raise self.last_value
        else:
            return self.last_value


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'john%s' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Call `create_user` rather than `create`

        Happily ignores `django_get_or_create`
        """
        manager = cls._get_manager(model_class)

        return manager.create_user(*args, **kwargs)


class BucketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bucket

    user = factory.SubFactory(UserFactory)
    last_update = factory.LazyFunction(timezone.now)
    title = factory.fuzzy.FuzzyText()


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    user = factory.SubFactory(UserFactory)
    last_update = factory.LazyFunction(timezone.now)


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

    def test_overview(self):
        response = self.client.get(reverse('overview'))
        self.assertEqual(response.status_code, 200)

    def test_bucket(self):
        response = self.client.get(reverse('bucket', kwargs={'bucket': 1}))
        self.assertEqual(response.status_code, 404)

        bucket = BucketFactory(title='Cheese')
        response = self.client.get(reverse('bucket', kwargs={'bucket': bucket.slug}))
        self.assertEqual(response.status_code, 404)

        bucket.user = self.user
        bucket.save()
        response = self.client.get(reverse('bucket', kwargs={'bucket': bucket.slug}))
        self.assertEqual(response.status_code, 200)

        subscription = SubscriptionFactory(user=self.user)
        self.assertEqual(len(bucket.subs), 0)
        data = {
            'title': 'Games',
            'subs': [subscription.pk],
        }
        response = self.client.post(reverse('bucket', kwargs={'bucket': bucket.slug}), data)

        bucket.refresh_from_db()

        self.assertRedirects(response, reverse('bucket', kwargs={'bucket': bucket.slug}))
        self.assertEqual(bucket.title, 'Games')
        self.assertEqual(bucket.subs_ids, set([subscription.pk]))

        new_bucket = BucketFactory(title='Cheese', user=self.user)
        response = self.client.post(reverse('bucket', kwargs={'bucket': new_bucket.slug}), data)
        self.assertEqual(response.status_code, 200)

    def test_bucket_new(self):
        self.assertEqual(len(self.user.bucket_set.all()), 0)
        data = {
            'title': 'Games',
        }
        response = self.client.post(reverse('bucket-new'), data)
        self.assertEqual(len(self.user.bucket_set.all()), 1)
        bucket = self.user.bucket_set.first()
        self.assertRedirects(response, reverse('bucket', kwargs={'bucket': bucket.slug}))

        self.assertEqual(bucket.title, 'Games')
        self.assertEqual(bucket.subs_ids, set())

        response = self.client.post(reverse('bucket-new'), data)
        self.assertEqual(len(self.user.bucket_set.all()), 1)
        self.assertEqual(response.status_code, 200)

    def test_subscription(self):
        response = self.client.get(reverse('subscription', kwargs={'subscription': 1}))
        self.assertEqual(response.status_code, 404)

        subscription = SubscriptionFactory()
        response = self.client.get(reverse('subscription', kwargs={'subscription': subscription.pk}))
        self.assertEqual(response.status_code, 404)

        subscription.user = self.user
        subscription.save()
        response = self.client.get(reverse('subscription', kwargs={'subscription': subscription.pk}))
        self.assertEqual(response.status_code, 200)

    def test_video(self):
        response = self.client.get(reverse('video', kwargs={'video': 1}))
        self.assertEqual(response.status_code, 200)

    def test_sync(self):
        response = self.client.get(reverse('sync'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('authorise'))

        OauthToken.objects.create(user=self.user)

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
                    },
                },
                {
                    'id': 'video456',
                    'snippet': {
                        'title': 'my other video',
                        'description': 'this is my other video',
                        'thumbnails': {},
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
        subscription = Subscription.objects.create(user=user, channel_id="123", last_update=timezone.now())
        bucket = BucketFactory(user=user, subs=[subscription])

        import_videos(user.id, subscription.id, "upload123", [bucket.id])
        self.assertEqual(playlistitems_mock.call_count, 2)

        self.assertEqual(playlistitems_mock.call_args_list,
        [
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


class ImportSubscriptionTasksTestCase(TestCase):
    def setUp(self):
        super(ImportSubscriptionTasksTestCase, self).setUp()

        self.service_patch = mock.patch('subscribae.utils.get_service')
        self.service_mock = self.service_patch.start()

        self.subscription_mock = self.service_mock.return_value.subscriptions.return_value.list
        self.channel_mock = self.service_mock.return_value.channels.return_value.list

        self.subscription_mock.return_value.execute.return_value = {
            'items': [
                {
                    'snippet': {
                        'title': 'A channel',
                        'description': "It's a channel",
                        'resourceId': {'channelId': '123'},
                        'thumbnails': {},
                    },
                },
                {
                    'snippet': {
                        'title': 'Another channel',
                        'description': "It's another channel",
                        'resourceId': {'channelId': '456'},
                        'thumbnails': {},
                    },
                },
            ],
        }

        self.channel_mock.return_value.execute.return_value = {
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

        self.user = UserFactory.create()
        OauthToken.objects.create(user=self.user, data={})

    def test_new_subscriptions(self):
        new_subscriptions(self.user.id)
        self.assertEqual(self.subscription_mock.call_count, 1)
        self.assertEqual(self.channel_mock.call_count, 1)
        self.assertEqual(Subscription.objects.count(), 2)
        # two import video tasks for the two subscriptions
        self.assertNumTasksEquals(2)

        self.assertEqual(self.subscription_mock.call_args, (
            (),
            {'mine': True, 'part': 'snippet', 'maxResults': API_MAX_RESULTS, 'pageToken': None}
        ))
        self.assertEqual(self.channel_mock.call_args, (
            (),
            {'id': '123,456', 'part': 'contentDetails', 'maxResults': API_MAX_RESULTS}
        ))

        self.flush_task_queues()

        new_subscriptions(self.user.id)
        self.assertEqual(self.subscription_mock.call_count, 2)
        self.assertEqual(self.channel_mock.call_count, 2)
        self.assertEqual(Subscription.objects.count(), 2)
        self.assertNumTasksEquals(0)

    def test_new_subscriptions_pagination(self):
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

        self.subscription_mock.return_value.execute = MockExecute([
            {
                'items': [],
                'nextPageToken': '123',
            },
            {
                'items': [],
            },
        ])
        self.channel_mock.return_value.execute.return_value = {'items': []}

        new_subscriptions(self.user.id)
        self.assertEqual(self.subscription_mock.call_count, 2)

        self.assertEqual(self.subscription_mock.call_args_list,
        [
            ((), {'mine': True, 'part': 'snippet', 'maxResults': API_MAX_RESULTS, 'pageToken': None}),
            ((), {'mine': True, 'part': 'snippet', 'maxResults': API_MAX_RESULTS, 'pageToken': '123'}),
        ])

    def test_new_subscriptions_runtime_exceeded(self):
        self.subscription_mock.return_value.execute = MockExecute([
            {
                'items': [],
                'nextPageToken': '123',
            },
            RuntimeExceededError(),
            {
                'items': [],
            }
        ])
        self.channel_mock.return_value.execute.return_value = {'items': []}

        new_subscriptions(self.user.id)
        self.assertEqual(self.subscription_mock.call_count, 2)
        # deadline exceeded will cause a new task to be spawned
        self.assertNumTasksEquals(1)
        # run the task
        self.process_task_queues()
        self.assertEqual(self.subscription_mock.call_count, 3)

    def test_update_subscriptions(self):
        last_week = timezone.now() - timedelta(7)
        sub1 = SubscriptionFactory.create(user=self.user, channel_id="123", last_update=last_week)
        sub2 = SubscriptionFactory.create(user=self.user, channel_id="456", last_update=last_week)

        update_subscriptions(self.user.id)
        self.assertEqual(self.subscription_mock.call_count, 1)
        self.assertEqual(self.channel_mock.call_count, 1)

        sub1.refresh_from_db()
        self.assertNotEqual(sub1.last_update, last_week)
        self.assertEqual(sub1.title, "A channel")
        self.assertEqual(sub1.description, "It's a channel")

        sub2.refresh_from_db()
        self.assertNotEqual(sub2.last_update, last_week)
        self.assertEqual(sub2.title, "Another channel")
        self.assertEqual(sub2.description, "It's another channel")

        # the update task end by deferring itself with the last PK
        self.assertNumTasksEquals(1)
        # make sure it doens't infinitely loop
        self.process_task_queues()

    def test_update_subscriptions_with_last_pk(self):
        last_week = timezone.now() - timedelta(7)
        sub1 = SubscriptionFactory.create(user=self.user, channel_id="123", last_update=last_week)
        sub2 = SubscriptionFactory.create(user=self.user, channel_id="456", last_update=last_week)
        first, second = sorted([sub1, sub2], key=lambda x: x.pk)

        self.subscription_mock.return_value.execute.return_value['items'] = [{
            'snippet': {
                'title': 'Another channel',
                'description': "It's another channel",
                'resourceId': {'channelId': second.channel_id},
                'thumbnails': {},
            },
        }]

        self.channel_mock.return_value.execute.return_value['items'] = [{
            'id': second.channel_id,
            'contentDetails': {
                'relatedPlaylists': {'uploads': 'upload%s' % second.channel_id},
            },
        }]

        update_subscriptions(self.user.id, last_pk=first.id)
        self.assertEqual(self.subscription_mock.call_count, 1)
        self.assertEqual(self.channel_mock.call_count, 1)

        first.refresh_from_db()
        self.assertEqual(first.last_update, last_week)
        self.assertEqual(first.title, "")
        self.assertEqual(first.description, "")

        second.refresh_from_db()
        self.assertNotEqual(second.last_update, last_week)
        self.assertEqual(second.title, "Another channel")
        self.assertEqual(second.description, "It's another channel")

        # the update task end by deferring itself with the last PK
        self.assertNumTasksEquals(1)
        # make sure it doens't infinitely loop
        self.process_task_queues()
