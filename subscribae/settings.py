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
#    Subscribae
#    Copyright (C) 2016  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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
"""
Django settings for subscribae project.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

from djangae.settings_base import * # noqa
from django.core.urlresolvers import reverse_lazy

from .boot import get_app_config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_app_config().secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ASSETS_DEBUG = DEBUG
ASSETS_AUTO_BUILD = DEBUG

# Despite Djangae docs saying this is false by default :)
DJANGAE_CREATE_UNKNOWN_USER = False

# Application definition

INSTALLED_APPS = (
    'djangae',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'djangae.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django_assets',
    'csp',
    'cspreports',
    'djangae.contrib.gauth_datastore',
    'djangae.contrib.security',
    'subscribae',
    'subscribae.admin',
    # 'djangae.contrib.uniquetool',
)

MIDDLEWARE_CLASSES = (
    'djangae.contrib.security.middleware.AppEngineSecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'djangae.contrib.gauth.middleware.AuthenticationMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.csrf",
            ],
            'debug': True,
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

SILENCED_SYSTEM_CHECKS = [
    'djangae.E001',  # we're using Django 1.11 session csrf feature
]

CSRF_USE_SESSIONS = True

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

CSP_REPORT_URI = reverse_lazy('report_csp')
CSP_REPORTS_LOG = True
CSP_REPORTS_LOG_LEVEL = 'warning'
CSP_REPORTS_SAVE = True
CSP_REPORTS_EMAIL_ADMINS = False

ROOT_URLCONF = 'subscribae.urls'

WSGI_APPLICATION = 'subscribae.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Oauth settings
OAUTH_CONF_PATH = os.path.join(BASE_DIR, 'oauth_secrets.json')
OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

# Using a route that is not caught by appengines routing in app.yaml
STATIC_URL = '/static-dev/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django_assets.finders.AssetsFinder',
)

# STATIC_ROOT isn't uploaded to the same place as application data is, but we
# need to access the manifest file to create the correct URLs in our templates
ASSETS_MANIFEST = "file:{}".format(os.path.join(BASE_DIR, ".webassets-manifest"))
ASSETS_CACHE = False

# sensible default CSP settings, feel free to modify them
CSP_DEFAULT_SRC = ("'self'", "*.gstatic.com")
# Inline styles are unsafe, but Django error pages use them. We later remove
# `unsafe-inline` in settings_live.py
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com", "*.gstatic.com")
CSP_FONT_SRC = ("'self'", "themes.googleusercontent.com", "*.gstatic.com")
CSP_FRAME_SRC = ("'self'", "www.google.com", "www.youtube.com", "accounts.google.com", "apis.google.com",
                 "plus.google.com")
CSP_SCRIPT_SRC = ("'self'", "*.googleanalytics.com", "*.google-analytics.com", "ajax.googleapis.com")
CSP_IMG_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'", "plus.google.com", "www.google-analytics.com")


from djangae.contrib.gauth.settings import *  # noqa
