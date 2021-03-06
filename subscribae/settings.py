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
ASSETS_AUTO_BUILD = False

# Djangae should create users for us
DJANGAE_CREATE_UNKNOWN_USER = True

# Application definition

INSTALLED_APPS = (
    'djangae',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'djangae.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.forms',
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
                "subscribae.context_processors.site_config",
            ],
            'debug': True,
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

SILENCED_SYSTEM_CHECKS = [
    'djangae.E001',  # we're using Django 1.11 session csrf feature
]

CSRF_USE_SESSIONS = True
CSRF_FAILURE_VIEW = "subscribae.views.error.csrf_failure"

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

OAUTH_RETURN_SESSION_KEY = 'subscribae-oauth-return-url-name'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

# Using a route that is not caught by appengines routing in app.yaml
STATIC_URL = '/static-dev/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
STATICFILES_STORAGE = 'subscribae.storage.ManifestOutsideOfStaticFilesStorage'
STATIC_MANIGEST_PATH = os.path.join(BASE_DIR, ".staticmanifest.json")

STATICFILES_DIRS = [
    "frontend/build/compiled",
]


# sensible default CSP settings, feel free to modify them
CSP_DEFAULT_SRC = ("'self'", "*.gstatic.com")
# Inline styles are unsafe, but Django error pages use them. We later remove
# `unsafe-inline` in settings_live.py
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_FONT_SRC = ("'self'",)
CSP_FRAME_SRC = ("'self'", "https://www.youtube.com")
CSP_SCRIPT_SRC = ("'self'", "https://www.youtube.com", "https://s.ytimg.com")
CSP_IMG_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'",)


from djangae.contrib.gauth.settings import *  # noqa

AUTH_USER_MODEL = "subscribae.SubscribaeUser"
