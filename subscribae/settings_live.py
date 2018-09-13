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

from subscribae.settings import *  # noqa: F403

SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 2592000  # 30 days
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True

# Using a route that is caught by appengines app.yaml, be sure to collectstatic before
# doing a deploy
STATIC_URL = '/static/'

SECURE_REDIRECT_EXEMPT = [
    # App Engine doesn't use HTTPS internally, so the /_ah/.* URLs need to be exempt.
    # Django compares these to request.path.lstrip("/"), hence the lack of preceding /
    r"^_ah/"
]

DEBUG = False
ASSETS_DEBUG = DEBUG
ASSETS_AUTO_BUILD = DEBUG

# Remove unsafe-inline from CSP_STYLE_SRC. It's there in default to allow
# Django error pages in DEBUG mode render necessary styles
if "'unsafe-inline'" in CSP_STYLE_SRC:  # noqa: F405
    CSP_STYLE_SRC = list(CSP_STYLE_SRC)  # noqa: F405
    CSP_STYLE_SRC.remove("'unsafe-inline'")  # noqa: F405
    CSP_STYLE_SRC = tuple(CSP_STYLE_SRC)  # noqa: F405

# Add the cached template loader for the Django template system (not for Jinja)
for template in TEMPLATES:  # noqa: F405
    template['OPTIONS']['debug'] = False
    if template['BACKEND'] == 'django.template.backends.django.DjangoTemplates':
        # Wrap the normal loaders with the cached loader
        template['OPTIONS']['loaders'] = [
            ('django.template.loaders.cached.Loader', template['OPTIONS']['loaders'])
        ]
