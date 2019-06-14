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

from django.contrib.auth import get_user_model
from django.utils import timezone

from subscribae.models import Bucket, Subscription, Video
import factory
import factory.fuzzy


class MockExecute(object):
    '''A callable that iterates over return values

    Useful for mocking functions/methods that have varying output. Exceptions
    must be instantiated.
    '''
    def __init__(self, return_values):
        self.return_values = return_values[:]
        self.return_values.reverse()

    def __call__(self, *args, **kwargs):
        try:
            self.last_value = self.return_values.pop()
        except IndexError:
            pass

        if isinstance(self.last_value, BaseException):
            raise self.last_value
        else:
            return self.last_value


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'john%s' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)

    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Call `create_user` rather than `create`

        Happily ignores `django_get_or_create`
        """
        manager = cls._get_manager(model_class)

        return manager.create_user(*args, **kwargs)


class BucketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bucket

    user = factory.SubFactory(UserFactory)
    last_update = factory.LazyFunction(timezone.now)
    title = factory.fuzzy.FuzzyText()


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    user = factory.SubFactory(UserFactory)
    last_update = factory.LazyFunction(timezone.now)
    channel_id = factory.Sequence(lambda n: u"%d" % n)


class VideoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Video

    user = factory.SubFactory(UserFactory)
    subscription = factory.SubFactory(SubscriptionFactory)

    title = factory.fuzzy.FuzzyText()
    description = factory.fuzzy.FuzzyText()
    youtube_id = factory.fuzzy.FuzzyText()
    published_at = factory.LazyFunction(timezone.now)
