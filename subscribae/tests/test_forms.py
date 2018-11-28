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

from subscribae.forms import BucketEditForm
from subscribae.tests.utils import BucketFactory, SubscriptionFactory, UserFactory


class FormsTestCase(TestCase):
    def test_bucket_edit_subs_qs(self):
        bucket = BucketFactory()
        other_user = UserFactory()

        my_subs = SubscriptionFactory.create_batch(2, user=bucket.user)
        SubscriptionFactory.create_batch(2, user=other_user)  # other subs

        form = BucketEditForm(instance=bucket)
        subs = list(form.fields["subs"].queryset)

        self.assertEqual(len(subs), 2)
        self.assertCountEqual(subs, list(my_subs))
