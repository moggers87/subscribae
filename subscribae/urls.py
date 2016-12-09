from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.views import serve

import session_csrf
session_csrf.monkeypatch()

from django.contrib import admin
admin.autodiscover()

urlpatterns = (
    url(r'^$', 'subscribae.views.home', name='home'),
    url(r'^bucket/(?P<bucket>.+$', 'subscribae.views.bucket', name='bucket'),
    url(r'^subscription/(?P<subscription>.+$', 'subscribae.views.subscription', name='subscription'),
    url(r'^video/(?P<video>.+$', 'subscribae.views.video', name='video'),

    url(r'^_ah/', include('djangae.urls')),

    # Note that by default this is also locked down with login:admin in app.yaml
    url(r'^admin/', include(admin.site.urls)),

    url(r'^csp/', include('cspreports.urls')),

    url(r'^auth/', include('djangae.contrib.gauth.urls')),
)

if settings.DEBUG:
    urlpatterns += tuple(static(settings.STATIC_URL, view=serve, show_indexes=True))
