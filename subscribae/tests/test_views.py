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

import os

from djangae.test import TestCase, inconsistent_db
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from google.appengine.api import users
import mock

from subscribae.models import OauthToken
from subscribae.tests.utils import BucketFactory, SubscriptionFactory, VideoFactory


class ViewTestCase(TestCase):
    """Mostly just smoke tests to make sure things are working"""
    def setUp(self):
        super(ViewTestCase, self).setUp()
        # TODO consider mocking rather than changing the environment
        os.environ['USER_EMAIL'] = 'test@example.com'
        os.environ['USER_ID'] = '1'
        self.user = get_user_model().objects.create(username='1', email='test@example.com', is_active=True)

    def tearDown(self):
        del os.environ['USER_EMAIL']
        del os.environ['USER_ID']
        super(ViewTestCase, self).tearDown()

    def test_home(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_overview_empty(self):
        response = self.client.get(reverse('overview'))
        self.assertEqual(response.status_code, 200)

    def test_overview_has_items(self):
        subscriptions = SubscriptionFactory.create_batch(2, user=self.user)
        buckets = [BucketFactory(user=self.user), BucketFactory(user=self.user, subs=[subscriptions[0]])]
        videos = [VideoFactory(user=self.user, buckets=[buckets[1]], subscription=subscriptions[0]),
                  VideoFactory(user=self.user)]

        response = self.client.get(reverse('overview'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(videos[0].ordering_key, response.content)
        self.assertNotIn(videos[1].ordering_key, response.content)

    def test_bucket(self):
        response = self.client.get(reverse('bucket', kwargs={'bucket': 1}))
        self.assertEqual(response.status_code, 404)

        bucket = BucketFactory(title='Cheese')
        response = self.client.get(reverse('bucket', kwargs={'bucket': bucket.pk}))
        self.assertEqual(response.status_code, 404)

        bucket.user = self.user
        bucket.save()
        response = self.client.get(reverse('bucket', kwargs={'bucket': bucket.pk}))
        self.assertEqual(response.status_code, 200)

        subscription = SubscriptionFactory(user=self.user)
        self.assertEqual(len(bucket.subs_ids), 0)
        data = {
            'title': 'Games',
            'subs': [subscription.pk],
        }
        response = self.client.post(reverse('bucket', kwargs={'bucket': bucket.pk}), data)

        bucket.refresh_from_db()

        self.assertRedirects(response, reverse('bucket', kwargs={'bucket': bucket.pk}))
        self.assertEqual(bucket.title, 'Games')
        self.assertEqual(bucket.subs_ids, set([subscription.pk]))

        new_bucket = BucketFactory(title='Cheese', user=self.user)
        response = self.client.post(reverse('bucket', kwargs={'bucket': new_bucket.pk}), data)
        self.assertEqual(response.status_code, 200)

    def test_bucket_start(self):
        bucket = BucketFactory(title='Cheese', user=self.user)
        response = self.client.get(reverse('bucket', kwargs={'bucket': bucket.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["start"], None)
        self.assertNotIn("?start=", response.content)

        video_id = "bluhbluhvideo"
        response = self.client.get("{}?start={}".format(reverse('bucket', kwargs={'bucket': bucket.pk}), video_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["start"], video_id)
        self.assertIn("?start={}".format(video_id), response.content)

    def test_bucket_new(self):
        self.assertEqual(len(self.user.bucket_set.all()), 0)
        data = {
            'title': 'Games',
        }
        response = self.client.post(reverse('bucket-new'), data)
        self.assertEqual(len(self.user.bucket_set.all()), 1)
        bucket = self.user.bucket_set.first()
        self.assertRedirects(response, reverse('bucket', kwargs={'bucket': bucket.pk}))

        self.assertEqual(bucket.title, 'Games')
        self.assertEqual(bucket.subs_ids, set())

        response = self.client.post(reverse('bucket-new'), data)
        self.assertEqual(len(self.user.bucket_set.all()), 1)
        self.assertEqual(response.status_code, 200)

    def test_bucket_new_inconsistent(self):
        with inconsistent_db():
            bucket = BucketFactory(title='Cheese', user=self.user)
            response = self.client.get(reverse('bucket', kwargs={'bucket': bucket.pk}))
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

    def test_sync(self):
        response = self.client.get(reverse('sync'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('authorise'))
        self.assertNumTasksEquals(0)

        OauthToken.objects.create(user=self.user)

        response = self.client.get(reverse('sync'))
        self.assertEqual(response.status_code, 200)
        self.assertNumTasksEquals(1)

    def test_update_subscriptions_cron(self):
        response = self.client.get(reverse('update-subscriptions-cron'))
        self.assertEqual(response.status_code, 403)
        self.assertNumTasksEquals(0)

        with mock.patch("djangae.environment.is_in_cron"):
            response = self.client.get(reverse('update-subscriptions-cron'))
            self.assertEqual(response.status_code, 200)
            self.assertNumTasksEquals(1)

    def test_source(self):
        response = self.client.get(reverse('source'))
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

    def test_logout(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], users.create_logout_url(reverse("home")))
