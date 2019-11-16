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

from django.db.models.query import QuerySet


class VideoQuerySet(QuerySet):
    def from_subscription(self, user, subscription):
        return self.filter(user=user, subscription_id=subscription)

    def from_bucket(self, user, bucket):
        return self.filter(user=user, buckets__contains=bucket)

    def add_titles(self):
        """Fetches titles and descriptions for Videos

        Returns a generator, rather than another queryset
        """
        from subscribae.utils import video_add_titles
        return video_add_titles(self)


class SubscriptionQuerySet(QuerySet):
    def add_titles(self):
        """Fetches titles and descriptions for Subscriptions

        Returns a generator, rather than another queryset
        """
        from subscribae.utils import subscription_add_titles
        return subscription_add_titles(self)
