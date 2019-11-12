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

from datetime import timedelta
import unittest

from djangae.test import TestCase
from django.utils import timezone
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
import mock

from subscribae.models import OauthToken
from subscribae.tests.utils import MockExecute, SubscriptionFactory, UserFactory
from subscribae.utils import import_videos, subscriptions, update_subscriptions


class UpdateSubscriptionsForUsersTestCase(TestCase):
    def setUp(self):
        super(UpdateSubscriptionsForUsersTestCase, self).setUp()

        self.service_patch = mock.patch('subscribae.utils.get_service')
        self.service_mock = self.service_patch.start()

        self.subscription_mock = self.service_mock.return_value.subscriptions.return_value.list
        self.channel_mock = self.service_mock.return_value.channels.return_value.list

        self.subscription_mock.return_value.execute = MockExecute([
            {
                'items': [
                    {
                        'snippet': {
                            'resourceId': {'channelId': '123'},
                            'thumbnails': {},
                        },
                    },
                    {
                        'snippet': {
                            'resourceId': {'channelId': '456'},
                            'thumbnails': {},
                        },
                    },
                ],
            },
        ])

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

    def tearDown(self):
        mock.patch.stopall()

    def test_subscriptions(self):
        last_week = timezone.now() - timedelta(7)
        sub1 = SubscriptionFactory.create(user=self.user, channel_id="123", last_update=last_week)
        sub2 = SubscriptionFactory.create(user=self.user, channel_id="456", last_update=last_week)

        subscriptions(self.user.id)
        self.assertEqual(self.subscription_mock.call_count, 1)
        self.assertEqual(self.channel_mock.call_count, 1)

        sub1.refresh_from_db()
        self.assertNotEqual(sub1.last_update, last_week)

        sub2.refresh_from_db()
        self.assertNotEqual(sub2.last_update, last_week)

        # two import_video calls
        self.assertNumTasksEquals(2)
        # make sure it doens't infinitely loop
        self.process_task_queues()

    @unittest.skip("this needs to change to page_token")
    def test_update_subscriptions_with_last_pk(self):
        last_week = timezone.now() - timedelta(7)
        sub1 = SubscriptionFactory.create(user=self.user, channel_id="123", last_update=last_week)
        sub2 = SubscriptionFactory.create(user=self.user, channel_id="456", last_update=last_week)
        first, second = sorted([sub1, sub2], key=lambda x: x.pk)

        self.subscription_mock.return_value.execute.return_value['items'] = [{
            'snippet': {
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

        subscriptions(self.user.id, last_pk=first.id)
        self.assertEqual(self.subscription_mock.call_count, 1)
        self.assertEqual(self.channel_mock.call_count, 1)

        first.refresh_from_db()
        self.assertEqual(first.last_update, last_week)

        second.refresh_from_db()
        self.assertNotEqual(second.last_update, last_week)

        # the update task end by deferring itself with the last PK, plus one
        # import_video calls
        self.assertNumTasksEquals(2)
        # make sure it doens't infinitely loop
        self.process_task_queues()

    @mock.patch('subscribae.utils.deferred')
    def test_subscriptions_with_runtime_exceeded_error(self, defer_mock):
        defer_mock.defer.side_effect = MockExecute([RuntimeExceededError(), None])

        last_week = timezone.now() - timedelta(7)
        sub1 = SubscriptionFactory.create(user=self.user, channel_id="123", last_update=last_week)
        sub2 = SubscriptionFactory.create(user=self.user, channel_id="456", last_update=last_week)

        subscriptions(self.user.id)
        self.assertEqual(self.subscription_mock.call_count, 1)
        self.assertEqual(self.channel_mock.call_count, 1)
        self.assertEqual(defer_mock.defer.call_count, 2)

        sub1.refresh_from_db()
        sub2.refresh_from_db()

        self.assertEqual(
            defer_mock.defer.call_args_list[0],
            ((import_videos, self.user.id, sub1.pk, sub1.upload_playlist, []), {"only_first_page": False})
        )
        self.assertEqual(defer_mock.defer.call_args_list[1],
                         ((subscriptions, self.user.id, None), {}))

        self.assertNotEqual(sub1.last_update, last_week)

        self.assertEqual(sub2.last_update, last_week)

    def test_missing_oauth_token(self):
        OauthToken.objects.get(user_id=self.user.id).delete()
        last_week = timezone.now() - timedelta(7)
        SubscriptionFactory.create(user=self.user, channel_id="123", last_update=last_week)
        SubscriptionFactory.create(user=self.user, channel_id="456", last_update=last_week)
        self.service_patch.stop()

        # should raise no exceptions
        subscriptions(self.user.id)


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
        user1 = UserFactory(pk=1)
        OauthToken.objects.create(pk=1, user=user1)
        user2 = UserFactory(pk=2)
        OauthToken.objects.create(pk=2, user=user2)

        update_subscriptions(last_pk=1)
        self.assertNumTasksEquals(1)

        self.flush_task_queues()
        update_subscriptions(last_pk=2)
        self.assertNumTasksEquals(0)

    @mock.patch('subscribae.utils.deferred')
    def test_update_subscriptions_runtime_exceeded(self, defer_mock):
        user1 = UserFactory(pk=1)
        oauth1 = OauthToken.objects.create(pk=1, user=user1)
        user2 = UserFactory(pk=2)
        OauthToken.objects.create(pk=2, user=user2)

        defer_mock.defer.side_effect = MockExecute([RuntimeExceededError(), None])

        update_subscriptions()
        self.assertEqual(defer_mock.defer.call_count, 2)
        self.assertEqual(defer_mock.defer.call_args_list, [
            ((subscriptions, oauth1.pk), {}),
            # defered task was not sent off, so we need to start from the first user again
            ((update_subscriptions, None), {}),
        ])
