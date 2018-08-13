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

from djangae.test import TestCase
from django.utils import timezone
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
import mock

from subscribae.models import OauthToken
from subscribae.utils import update_subscriptions_for_user, update_subscriptions
from subscribae.tests.utils import MockExecute, UserFactory, SubscriptionFactory


class UpdateSubscriptionsForUsersTestCase(TestCase):
    def setUp(self):
        super(UpdateSubscriptionsForUsersTestCase, self).setUp()

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

    def test_update_subscriptions_for_user(self):
        last_week = timezone.now() - timedelta(7)
        sub1 = SubscriptionFactory.create(user=self.user, channel_id="123", last_update=last_week)
        sub2 = SubscriptionFactory.create(user=self.user, channel_id="456", last_update=last_week)

        update_subscriptions_for_user(self.user.id)
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

        # the update task end by deferring itself with the last PK, plus two
        # import_video calls
        self.assertNumTasksEquals(3)
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

        update_subscriptions_for_user(self.user.id, last_pk=first.id)
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

        # the update task end by deferring itself with the last PK, plus one
        # import_video calls
        self.assertNumTasksEquals(2)
        # make sure it doens't infinitely loop
        self.process_task_queues()


class UpdateSubscriptionsTestCase(TestCase):
    def test_update_subscriptions(self):
        update_subscriptions()
        self.assertNumTasksEquals(0)

        user1 = UserFactory()
        OauthToken.objects.create(user=user1)
        user2 = UserFactory()
        OauthToken.objects.create(user=user2)

        update_subscriptions()
        self.assertNumTasksEquals(2)

    def test_update_subscriptions_last_pk(self):
        user1 = UserFactory()
        OauthToken.objects.create(pk=1, user=user1)
        user2 = UserFactory()
        OauthToken.objects.create(pk=2, user=user2)

        update_subscriptions(last_pk=1)
        self.assertNumTasksEquals(1)

        self.flush_task_queues()
        update_subscriptions(last_pk=2)
        self.assertNumTasksEquals(0)

    @mock.patch('subscribae.utils.deferred')
    def test_update_subscriptions_runtime_exceeded(self, defer_mock):
        user1 = UserFactory()
        oauth1 = OauthToken.objects.create(pk=1, user=user1)
        user2 = UserFactory()
        OauthToken.objects.create(pk=2, user=user2)

        defer_mock.defer.side_effect = MockExecute([RuntimeExceededError(), None])

        update_subscriptions()
        self.assertEqual(defer_mock.defer.call_count, 2)
        self.assertEqual(defer_mock.defer.call_args_list, [
            ((update_subscriptions_for_user, oauth1.pk), {}),
            ((update_subscriptions, None), {}),  # defered task was not sent off, so we need to start from the first user again
        ])
