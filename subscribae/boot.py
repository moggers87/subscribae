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

from os.path import abspath, dirname, exists, join
import sys

PROJECT_DIR = dirname(dirname(abspath(__file__)))
SITEPACKAGES_DIR = join(PROJECT_DIR, "sitepackages")
DEV_SITEPACKAGES_DIR = join(SITEPACKAGES_DIR, "dev")
PROD_SITEPACKAGES_DIR = join(SITEPACKAGES_DIR, "prod")
APPENGINE_DIR = join(DEV_SITEPACKAGES_DIR, "google_appengine")


def fix_path(include_dev_libs_path=False):
    """ Insert libs folder(s) and SDK into sys.path. The one(s) inserted last take priority. """
    if include_dev_libs_path:
        if exists(APPENGINE_DIR) and APPENGINE_DIR not in sys.path:
            sys.path.insert(1, APPENGINE_DIR)

        if DEV_SITEPACKAGES_DIR not in sys.path:
            sys.path.insert(1, DEV_SITEPACKAGES_DIR)

    if SITEPACKAGES_DIR not in sys.path:
        sys.path.insert(1, PROD_SITEPACKAGES_DIR)

    # some quick magic to "fix" conflicts between the appengine SDK and protobuf
    # see https://github.com/google/protobuf/issues/1296#issuecomment-264264926
    try:
        # protobuf might be installed globally, or not at all.
        import google.protobuf  # noqa
    except ImportError:
        pass
    import google.appengine  # noqa


def get_app_config():
    """Returns the application configuration, creating it if necessary."""
    from django.utils.crypto import get_random_string
    from google.appengine.ext import ndb

    class Config(ndb.Model):
        """A simple key-value store for application configuration settings."""
        secret_key = ndb.StringProperty()

    # Create a random SECRET_KEY
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'

    @ndb.transactional()
    def txn():
        # Get or create the Config in a transaction, so that if it doesn't exist we don't get 2
        # threads creating a Config object and one overwriting the other
        key = ndb.Key(Config, 'config')
        entity = key.get()
        if not entity:
            entity = Config(key=key)
            entity.secret_key = get_random_string(50, chars)
            entity.put()
        return entity
    return txn()
