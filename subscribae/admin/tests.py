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

import os

from djangae.test import TestCase, inconsistent_db
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse

from subscribae.admin.views import admin_for_superusers, user_index, user_add, user_edit, index, USER_PAGE_SIZE


class AdminForSuperusersTestCase(TestCase):
    def setUp(self):
        self.wrapped_func = admin_for_superusers(lambda x: x)

    def test_anon_user(self):
        request = HttpResponse()
        request.path = "/"
        request.user = AnonymousUser()

        with self.assertRaises(Http404):
            self.wrapped_func(request)

    def test_normal_user(self):
        request = HttpResponse()
        request.path = "/"
        request.user = get_user_model()
        request.user.is_superuser = False

        with self.assertRaises(Http404):
            self.wrapped_func(request)

    def test_super_user(self):
        request = HttpResponse()
        request.path = "/"
        request.user = get_user_model()
        request.user.is_superuser = True

        self.assertEqual(self.wrapped_func(request), request)

    def test_decorates_decorates(self):
        self.assertEqual(self.wrapped_func._subscribae_decorators, [admin_for_superusers])


class AdminIndexTestCase(TestCase):
    def setUp(self):
        super(AdminIndexTestCase, self).setUp()
        # TODO consider mocking rather than changing the environment
        os.environ['USER_EMAIL'] = 'test@example.com'
        os.environ['USER_ID'] = '1'
        os.environ['USER_IS_ADMIN'] = '1'
        self.user = get_user_model().objects.create(username='1', email='test@example.com', is_superuser=True)

    def tearDown(self):
        del os.environ['USER_EMAIL']
        del os.environ['USER_ID']
        del os.environ['USER_IS_ADMIN']
        super(AdminIndexTestCase, self).tearDown()

    def test_decorator(self):
        self.assertEqual(index._subscribae_decorators, [admin_for_superusers])

    def test_get(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)


class UserIndexTestCase(TestCase):
    def setUp(self):
        super(UserIndexTestCase, self).setUp()
        # TODO consider mocking rather than changing the environment
        os.environ['USER_EMAIL'] = 'test@example.com'
        os.environ['USER_ID'] = '1'
        os.environ['USER_IS_ADMIN'] = '1'
        self.user = get_user_model().objects.create(username='1', email='test@example.com', is_superuser=True)

    def tearDown(self):
        del os.environ['USER_EMAIL']
        del os.environ['USER_ID']
        del os.environ['USER_IS_ADMIN']
        super(UserIndexTestCase, self).tearDown()

    def test_decorator(self):
        self.assertEqual(user_index._subscribae_decorators, [admin_for_superusers])

    def test_get(self):
        response = self.client.get(reverse("admin:user-index"))
        self.assertEqual(response.status_code, 200)

    def test_pagination_before(self):
        other_user = get_user_model().objects.create(username="2", email='test2@example.com')
        first, second = sorted([self.user, other_user], key=lambda x: x.pk)

        response = self.client.get("%s?before=%s" % (reverse("admin:user-index"), second.pk))
        self.assertEqual(list(response.context["users"]), [first])

        response = self.client.get("%s?before=%s" % (reverse("admin:user-index"), first.pk))
        self.assertEqual(list(response.context["users"]), [])

    def test_pagination_after(self):
        other_user = get_user_model().objects.create(username="2", email='test2@example.com')
        first, second = sorted([self.user, other_user], key=lambda x: x.pk)

        response = self.client.get("%s?after=%s" % (reverse("admin:user-index"), first.pk))
        self.assertEqual(list(response.context["users"]), [second])

        response = self.client.get("%s?after=%s" % (reverse("admin:user-index"), second.pk))
        self.assertEqual(list(response.context["users"]), [])

    def test_pagination_neither(self):
        for i in range(USER_PAGE_SIZE + 1):
            get_user_model().objects.create(username="test%s" % i, email='test%s@example.com' % i)

        response = self.client.get(reverse("admin:user-index"))
        self.assertEqual(len(response.context["users"]), USER_PAGE_SIZE)

    def test_new_user(self):
        with inconsistent_db():
            new_user = get_user_model().objects.create(username="ec", email="ec@example.com")

            response = self.client.get((reverse("admin:user-index")))
            self.assertEqual(list(response.context["users"]), [self.user])

            response = self.client.get("%s?new_user=%s" % (reverse("admin:user-index"), new_user.pk))
            self.assertItemsEqual(list(response.context["users"]), [new_user, self.user])


class UserAddTestCase(TestCase):
    def setUp(self):
        super(UserAddTestCase, self).setUp()
        # TODO consider mocking rather than changing the environment
        os.environ['USER_EMAIL'] = 'test@example.com'
        os.environ['USER_ID'] = '1'
        os.environ['USER_IS_ADMIN'] = '1'
        self.user = get_user_model().objects.create(username='1', email='test@example.com', is_superuser=True)

    def tearDown(self):
        del os.environ['USER_EMAIL']
        del os.environ['USER_ID']
        del os.environ['USER_IS_ADMIN']
        super(UserAddTestCase, self).tearDown()

    def test_decorator(self):
        self.assertEqual(user_add._subscribae_decorators, [admin_for_superusers])

    def test_get(self):
        response = self.client.get(reverse("admin:user-add"))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        data = {"email": "test2@example.com", "is_active": True}
        response = self.client.post(reverse("admin:user-add"), data)
        user = get_user_model().objects.get(email="test2@example.com")
        self.assertEqual(user.is_active, True)

        self.assertRedirects(response, "%s?new_user=%s" % (reverse("admin:user-index"), user.pk))

    def test_post_invalid_data(self):
        data = {"email": "test2@@example.com", "is_active": True}
        response = self.client.post(reverse("admin:user-add"), data)
        self.assertEqual(response.status_code, 200)

        self.assertFalse(get_user_model().objects.filter(email="test2@@example.com").exists())


class UserEditTestCase(TestCase):
    def setUp(self):
        super(UserEditTestCase, self).setUp()
        # TODO consider mocking rather than changing the environment
        os.environ['USER_EMAIL'] = 'test@example.com'
        os.environ['USER_ID'] = '1'
        os.environ['USER_IS_ADMIN'] = '1'
        self.user = get_user_model().objects.create(username='1', email='test@example.com',
                                                    is_superuser=True, is_active=True)

    def tearDown(self):
        del os.environ['USER_EMAIL']
        del os.environ['USER_ID']
        del os.environ['USER_IS_ADMIN']
        super(UserEditTestCase, self).tearDown()

    def test_decorator(self):
        self.assertEqual(user_edit._subscribae_decorators, [admin_for_superusers])

    def test_get(self):
        response = self.client.get(reverse("admin:user-edit", kwargs={"user_id": self.user.id}))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        data = {"is_active": False}
        response = self.client.post(reverse("admin:user-edit", kwargs={"user_id": self.user.id}), data)
        self.assertRedirects(response, reverse("admin:user-index"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, False)

    def test_404_post(self):
        response = self.client.post(reverse("admin:user-edit", kwargs={"user_id": "123"}), {})
        self.assertEqual(response.status_code, 404)

    def test_404_get(self):
        response = self.client.get(reverse("admin:user-edit", kwargs={"user_id": "123"}))
        self.assertEqual(response.status_code, 404)
