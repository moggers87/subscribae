##
#    Copyright 2014 Potato London Ltd.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may not use
#    this file except in compliance with the License. You may obtain a copy of the
#    License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software distributed
#    under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#    CONDITIONS OF ANY KIND, either express or implied. See the License for the
#    specific language governing permissions and limitations under the License.
##
##
#    Copyright (C) 2016  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.views import serve

from subscribae.views import api, misc, oauth, tasks

handler400 = "subscribae.views.error.bad_request"
handler403 = "subscribae.views.error.permission_denied"
handler404 = "subscribae.views.error.not_found"
handler500 = "subscribae.views.error.server_error"

urlpatterns = (
    url(r'^$', misc.home, name='home'),
    url(r'^overview$', misc.overview, name='overview'),
    url(r'^bucket/new$', misc.bucket_new, name='bucket-new'),
    url(r'^bucket/edit/(?P<bucket>.+)$', misc.bucket_edit, name='bucket-edit'),
    url(r'^bucket/(?P<bucket>.+)$', misc.bucket, name='bucket'),
    url(r'^subscription/(?P<subscription>.+)$', misc.subscription, name='subscription'),
    url(r'^sync$', misc.sync_subscription, name='sync'),
    url(r'^authorise$', oauth.oauth_start, name='authorise'),
    url(r'^oauth2callback$', oauth.oauth_callback, name='oauth2callback'),
    url(r'^source', misc.source, name='source'),
    url(r'^logout', misc.logout, name='logout'),

    # api
    url(r'^api/bucket/(?P<bucket>.+)/videos$',
        api.bucket_video, name='bucket-video-api'),
    url(r'^api/bucket/(?P<bucket>.+)/videos/viewed$',
        api.bucket_video_viewed, name='bucket-video-viewed-api'),
    url(r'^api/subscription/(?P<subscription>.+)/videos$',
        api.subscription_video, name='subscription-video-api'),
    url(r'^api/subscription/(?P<subscription>.+)/videos/viewed$',
        api.subscription_video_viewed, name='subscription-video-viewed-api'),

    # crons
    url(r'^cron/update_subscriptions$', tasks.update_subscriptions_cron, name='update-subscriptions-cron'),

    url(r'^_ah/', include('djangae.urls')),

    url(r'^csp/', include('cspreports.urls')),

    url(r'^auth/', include('djangae.contrib.gauth.urls')),

    url(r'^admin/', include('subscribae.admin.urls', namespace='admin')),
)

if settings.DEBUG:
    urlpatterns += tuple(static(settings.STATIC_URL, view=serve, show_indexes=True))
    urlpatterns += (
        url(r'^styleguide$', misc.styleguide, name='styleguide'),
    )
