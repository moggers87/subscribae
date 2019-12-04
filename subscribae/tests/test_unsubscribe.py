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

from subscribae import utils


class UnsubscribeTestCase(TestCase):
    def test_unsubscribe(self):
        user = UserFactory()
        sub = SubscriptionFactory(user=user)
        utils.unsubscriptions(user.pk)

        with self.assertRaises(Subscription.DoesNotExist):
            sub.refresh_from_db()

    def test_with_last_pk(self):
        pass
