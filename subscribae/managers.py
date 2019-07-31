from django.db.models.query import QuerySet


class VideoQuerySet(QuerySet):
    def from_subscription(self, user, subscription):
        return self.filter(user=user, subscription_id=subscription)

    def from_bucket(self, user, bucket):
        return self.filter(user=user, buckets__contains=bucket)
