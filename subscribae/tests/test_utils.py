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
from google.appengine.api import memcache
import mock

from subscribae.models import OauthToken
from subscribae.tests.utils import UserFactory
from subscribae.utils import get_service


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
