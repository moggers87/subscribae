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

from datetime import datetime

from djangae.test import TestCase
from pytz import UTC

from subscribae.models import Bucket, SiteConfig, Subscription, Video, create_composite_key
from subscribae.tests.utils import BucketFactory, SubscriptionFactory, UserFactory, VideoFactory


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
        VideoFactory(published_at=datetime(1997, 8, 16, 19, 20, 30, 450000, tzinfo=UTC), youtube_id="1")
        VideoFactory(published_at=datetime(1997, 6, 16, 19, 20, 30, 450000, tzinfo=UTC), youtube_id="4")
        VideoFactory(published_at=datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC), youtube_id="2")
        VideoFactory(published_at=datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC), youtube_id="3")

        videos = Video.objects.all()

        self.assertEqual(
            [i.published_at for i in videos],
            [
                datetime(1997, 6, 16, 19, 20, 30, 450000, tzinfo=UTC),
                datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC),
                datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC),
                datetime(1997, 8, 16, 19, 20, 30, 450000, tzinfo=UTC),
            ]
        )

        self.assertEqual(
            [i.ordering_key for i in videos],
            [
                create_composite_key(str(datetime(1997, 6, 16, 19, 20, 30, 450000, tzinfo=UTC)), "4"),
                create_composite_key(str(datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC)), "2"),
                create_composite_key(str(datetime(1997, 7, 16, 19, 20, 30, 450000, tzinfo=UTC)), "3"),
                create_composite_key(str(datetime(1997, 8, 16, 19, 20, 30, 450000, tzinfo=UTC)), "1"),
            ]
        )

    def test_footer_render(self):
        conf = SiteConfig()
        conf.footer_text = """{{ object.site_name }}"""

        output = conf.render_footer()
        self.assertEqual(output, "cool.example.com")

    def test_video_from_subscription(self):
        user = UserFactory()
        sub1 = SubscriptionFactory(user=user, title="test1")
        sub2 = SubscriptionFactory(user=user, title="test2")
        video = VideoFactory(user=user, subscription=sub2)

        videos1 = Video.objects.from_subscription(user=user, subscription=sub1)
        videos2 = Video.objects.from_subscription(user=user, subscription=sub2)

        self.assertEqual(len(videos1), 0)
        self.assertEqual(len(videos2), 1)
        self.assertEqual(videos2[0], video)

    def test_video_from_bucket(self):
        user = UserFactory()
        bucket1 = BucketFactory(user=user, title="test1")
        bucket2 = BucketFactory(user=user, title="test2")
        video = VideoFactory(user=user, buckets=[bucket2])

        videos1 = Video.objects.from_bucket(user=user, bucket=bucket1)
        videos2 = Video.objects.from_bucket(user=user, bucket=bucket2)

        self.assertEqual(len(videos1), 0)
        self.assertEqual(len(videos2), 1)
        self.assertEqual(videos2[0], video)
