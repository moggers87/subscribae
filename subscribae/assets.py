##
#    Subscribae
#    Copyright (C) 2018  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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

import os

from django.conf import settings
from django_assets import Bundle, register
from webassets.filter import get_filter


node_modules = os.path.join(settings.BASE_DIR, "node_modules")
ugly = get_filter("uglifyjs", binary=os.path.join(node_modules, ".bin", "uglifyjs"),
                  extra_args=["--comments", "/^!/", "-m", "-c"])


js = Bundle(
    "thirdparty/jquery/dist/jquery.js",
    "js/test.js",
    filters=(ugly,),
    output="compiled/js/test.%(version)s.js",
)
register("main_js", js)
