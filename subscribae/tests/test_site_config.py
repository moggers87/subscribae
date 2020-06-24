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

from django.test import TestCase
from django.core.cache import cache
import mock

from subscribae import context_processors, utils
from subscribae.models import SiteConfig


class SiteConfigTestCase(TestCase):
    def test_get_config_creates(self):
        self.assertEqual(SiteConfig.objects.count(), 0)
        utils.get_site_config()
        self.assertEqual(SiteConfig.objects.count(), 1)

    def test_get_config_creates_only_one(self):
        conf = SiteConfig.objects.create(id=utils.SITE_CONFIG_ID)
        new_conf = utils.get_site_config()
        self.assertEqual(conf.id, new_conf.id)

    def test_get_config_ignores_other_ids(self):
        conf = SiteConfig.objects.create(id=utils.SITE_CONFIG_ID + 10)
        new_conf = utils.get_site_config()
        self.assertNotEqual(conf.id, new_conf.id)

    def test_get_config_uses_module_cache(self):
        cache.set(utils.SITE_CONFIG_CACHE_KEY, "somethingthatsnotamodelobject")
        conf = utils.get_site_config()

        self.assertEqual(conf, "somethingthatsnotamodelobject")


class SiteConfigContextTestCase(TestCase):
    @mock.patch("subscribae.context_processors.get_site_config")
    def test_context_processor(self, get_config_mock):
        ctx = context_processors.site_config(None)
        self.assertEqual(get_config_mock.call_count, 1)
        self.assertEqual(ctx.keys(), ["site_config"])
        self.assertEqual(ctx["site_config"], get_config_mock.return_value)
