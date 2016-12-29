from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.views import serve

import session_csrf
session_csrf.monkeypatch()

from django.contrib import admin
admin.autodiscover()

from subscribae import views as sub_views

urlpatterns = (
    url(r'^$', sub_views.home, name='home'),
    url(r'^bucket/(?P<bucket>.+)$', sub_views.bucket, name='bucket'),
    url(r'^subscription/(?P<subscription>.+)$', sub_views.subscription, name='subscription'),
    url(r'^video/(?P<video>.+)$', sub_views.video, name='video'),
    url(r'^sync$', sub_views.sync_subscription, name='sync'),
    url(r'^authorise$', sub_views.oauth_start, name='authorise'),
    url(r'^oauth2callback$', sub_views.oauth_callback, name='oauth2callback'),

    url(r'^_ah/', include('djangae.urls')),

    url(r'^csp/', include('cspreports.urls')),

    url(r'^auth/', include('djangae.contrib.gauth.urls')),
)

if settings.DEBUG:
    urlpatterns += tuple(static(settings.STATIC_URL, view=serve, show_indexes=True))
