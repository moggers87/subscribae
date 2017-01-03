import os

from djangae.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
import mock


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
