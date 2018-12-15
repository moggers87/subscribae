##
#    Copyright (C) 2018  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
import mock

from subscribae.decorators import active_user


@active_user
def mock_view(request):
    return "hello"


class ActiveUserTestCase(TestCase):
    def test_user_inactive(self):
        request = mock.Mock()
        request.user = get_user_model()()

        with self.assertRaises(Http404):
            mock_view(request)

    def test_user_active(self):
        request = mock.Mock()
        request.user = get_user_model()()
        request.user.is_active = True

        self.assertEqual(mock_view(request), "hello")

    def test_user_anon(self):
        request = mock.Mock()
        request.user = AnonymousUser()

        with self.assertRaises(ImproperlyConfigured):
            mock_view(request)
