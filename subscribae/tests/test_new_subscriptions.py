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

from djangae.test import TestCase
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
import mock

from subscribae.models import OauthToken, Subscription
from subscribae.tests.utils import MockExecute, UserFactory
from subscribae.utils import API_MAX_RESULTS, new_subscriptions


class NewSubscriptionTestCase(TestCase):
    def setUp(self):
        super(NewSubscriptionTestCase, self).setUp()

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

    def tearDown(self):
        mock.patch.stopall()

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

        self.assertEqual(self.subscription_mock.call_args_list, [
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

    def test_missing_oauth_token(self):
        OauthToken.objects.get(user_id=self.user.id).delete()
        self.service_patch.stop()

        new_subscriptions(self.user.id)
