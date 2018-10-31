##
#    Subscribae
#    Copyright (C) 2018  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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

from djangae.test import TestCase
from django.contrib.auth import get_user_model
from google.appengine.api import users

from subscribae.backends import SubscribaeUserBackend


class UserBackendTestCase(TestCase):
    def test_is_active(self):
        email = 'user@example.com'
        get_user_model().objects.pre_create_google_user(email, is_active=True)
        google_user = users.User(email=email, _user_id='1')
        maybe_user = SubscribaeUserBackend().authenticate(google_user=google_user)

        self.assertEqual(maybe_user.email, email)
        self.assertEqual(maybe_user.is_active, True)

    def test_is_not_active(self):
        email = 'user@example.com'
        get_user_model().objects.pre_create_google_user(email, is_active=False)
        google_user = users.User(email=email, _user_id='1')
        maybe_user = SubscribaeUserBackend().authenticate(google_user=google_user)

        self.assertEqual(maybe_user, None)
