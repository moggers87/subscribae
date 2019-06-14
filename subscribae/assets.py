# -*- coding: utf-8 -*-
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

import os

from django.conf import settings
from django_assets import Bundle, register
from webassets.filter import ExternalTool, get_filter
from webassets.utils import working_directory


class PostCSS(ExternalTool):
    # Taken from WeAssets e3e82114324ffd6cf1a2877976a1de08c515eb10
    # Copyright (c) 2008, Michael Elsdörfer <http://elsdoerfer.name>
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions
    # are met:
    #
    #     1. Redistributions of source code must retain the above copyright
    #        notice, this list of conditions and the following disclaimer.
    #
    #     2. Redistributions in binary form must reproduce the above
    #        copyright notice, this list of conditions and the following
    #        disclaimer in the documentation and/or other materials
    #        provided with the distribution.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
    # FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
    # COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
    # INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
    # BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    # LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    # CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    # LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
    # ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    # POSSIBILITY OF SUCH DAMAGE.
    """Processes CSS code using `PostCSS <http://postcss.org/>`_.

    Requires the ``postcss`` executable to be available externally.
    To install it, you might be able to do::

        $ npm install --global postcss

    You should also install the plugins you want to use::

        $ npm install --global postcss-cssnext

    You can configure postcss in ``postcss.config.js``:

    .. code-block:: javascript

        module.exports = {
            plugins: [
                require('postcss-cssnext')({
                  // optional configuration for cssnext
                })
            ],
        };

    *Supported configuration options*:

    POSTCSS_BIN
        Path to the postcss executable used to compile source files. By
        default, the filter will attempt to run ``postcss`` via the
        system path.

    POSTCSS_EXTRA_ARGS
        Additional command-line options to be passed to ``postcss`` using this
        setting, which expects a list of strings.

    """
    name = 'postcss'

    options = {
        'binary': 'POSTCSS_BIN',
        'extra_args': 'POSTCSS_EXTRA_ARGS',
    }

    max_debug_level = None

    def input(self, in_, out, source_path, **kw):
        # Set working directory to the source file so that includes are found
        args = [self.binary or 'postcss']
        if self.extra_args:
            args.extend(self.extra_args)
        with working_directory(filename=source_path):
            self.subprocess(args, out, in_)


node_modules = os.path.join(settings.BASE_DIR, "node_modules")
ugly = get_filter("uglifyjs", binary=os.path.join(node_modules, ".bin", "uglifyjs"),
                  extra_args=["--comments", "/^!/", "-m", "-c"])
postcss = get_filter(PostCSS, binary=os.path.join(node_modules, ".bin", "postcss"))


js = Bundle(
    "thirdparty/jquery/dist/jquery.js",
    "js/player.js",
    "js/expando.js",
    filters=(ugly,),
    output="compiled/js/website.%(version)s.js",
)
register("main_js", js)


css = Bundle(
    "css/subscribae.css",
    filters=(postcss,),
    output="compiled/css/website.%(version)s.css",
)
register("main_css", css)
