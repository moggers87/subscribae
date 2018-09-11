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

from datetime import datetime

from djangae.test import TestCase
from django.utils import timezone
from google.appengine.runtime import DeadlineExceededError as RuntimeExceededError
from pytz import UTC
import mock

from subscribae.models import Bucket, Subscription, Video
from subscribae.tests.utils import BucketFactory, SubscriptionFactory, VideoFactory


class ModelTestCase(TestCase):
    def test_default_bucket_ordering(self):
        BucketFactory(title="test2")
        BucketFactory(title="test1")
        BucketFactory(title="test3")

        buckets = Bucket.objects.all()

        self.assertEqual(
            [i.title for i in buckets],
            ["test1", "test2", "test3"]
        )

    def test_default_subscription_ordering(self):
        SubscriptionFactory(title="test2")
        SubscriptionFactory(title="test1")
        SubscriptionFactory(title="test3")

        subscriptions = Subscription.objects.all()

        self.assertEqual(
            [i.title for i in subscriptions],
            ["test1", "test2", "test3"]
        )

    def test_default_video_ordering(self):
        VideoFactory(published_at=datetime(1997, 8, 16, 19, 20, 30, 450000, tzinfo=UTC))
        VideoFactory(published_at=datetime(1997, 6, 16, 19, 20, 30, 450000, tzinfo=UTC))
        VideoFactory(published_at=datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC))

        videos = Video.objects.all()

        self.assertEqual(
            [i.published_at for i in videos],
            [
                datetime(1997, 6, 16, 19, 20, 30, 450000, tzinfo=UTC),
                datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC),
                datetime(1997, 8, 16, 19, 20, 30, 450000, tzinfo=UTC),
            ]
        )
