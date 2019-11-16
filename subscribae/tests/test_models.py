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
import mock

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
        sub1 = SubscriptionFactory(user=user)
        sub2 = SubscriptionFactory(user=user)
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


class AddTitlesSubscriptionTestCase(TestCase):
    def setUp(self):
        super(AddTitlesSubscriptionTestCase, self).setUp()

        self.service_patch = mock.patch('subscribae.utils.get_service')
        self.service_mock = self.service_patch.start()

        self.channel_mock = self.service_mock.return_value.channels.return_value.list

        self.channel_mock.return_value.execute.return_value = {
            'items': [
                {
                    'id': '123',
                    'snippet': {
                        "title": "henlo",
                        "description": "bluh bluh",
                    },
                },
                {
                    'id': '456',
                    'snippet': {
                        "title": "bye-q",
                        "description": "blah blah",
                    },
                },
            ],
        }

    def tearDown(self):
        mock.patch.stopall()

    def test_model_method(self):
        sub = SubscriptionFactory(channel_id="123")
        with self.assertRaises(AttributeError):
            sub.title
        with self.assertRaises(AttributeError):
            sub.description

        sub.add_titles()

        self.assertEqual(sub.title, "henlo")
        self.assertEqual(sub.description, "bluh bluh")

    def test_queryset_method(self):
        SubscriptionFactory(channel_id="123")
        SubscriptionFactory(channel_id="456")

        subs = Subscription.objects.all()
        for obj in subs:
            with self.assertRaises(AttributeError):
                obj.title
            with self.assertRaises(AttributeError):
                obj.description

        titled_subs = subs.add_titles()
        for obj in titled_subs:
            self.assertNotEqual(obj.title, None)
            self.assertNotEqual(obj.description, None)

    def test_empty_queryset_method(self):
        Subscription.objects.all().add_titles()


class AddTitlesVideoTestCase(TestCase):
    def setUp(self):
        super(AddTitlesVideoTestCase, self).setUp()

        self.service_patch = mock.patch('subscribae.utils.get_service')
        self.service_mock = self.service_patch.start()

        self.video_mock = self.service_mock.return_value.videos.return_value.list

        self.video_mock.return_value.execute.return_value = {
            'items': [
                {
                    'id': '123',
                    'snippet': {
                        "title": "henlo",
                        "description": "bluh bluh",
                    },
                },
                {
                    'id': '456',
                    'snippet': {
                        "title": "bye-q",
                        "description": "blah blah",
                    },
                },
            ],
        }

    def tearDown(self):
        mock.patch.stopall()

    def test_model_method(self):
        vid = VideoFactory(youtube_id="123")
        with self.assertRaises(AttributeError):
            vid.title
        with self.assertRaises(AttributeError):
            vid.description

        vid.add_titles()

        self.assertEqual(vid.title, "henlo")
        self.assertEqual(vid.description, "bluh bluh")

    def test_queryset_method(self):
        VideoFactory(youtube_id="123")
        VideoFactory(youtube_id="456")

        vids = Video.objects.all()
        for obj in vids:
            with self.assertRaises(AttributeError):
                obj.title
            with self.assertRaises(AttributeError):
                obj.description

        titled_vids = vids.add_titles()
        for obj in titled_vids:
            self.assertNotEqual(obj.title, None)
            self.assertNotEqual(obj.description, None)

    def test_empty_queryset_method(self):
        Video.objects.all().add_titles()
