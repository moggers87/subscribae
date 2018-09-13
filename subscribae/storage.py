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

import json
import os

from django.conf import settings
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ManifestOutsideOfStaticFilesStorage(ManifestStaticFilesStorage):
    manifest_name = settings.STATIC_MANIGEST_PATH

    def read_manifest(self):
        try:
            with open(self.manifest_name, "rb") as manifest:
                return manifest.read().decode('utf-8') or None
        except IOError:
            return None

    def save_manifest(self):
        payload = {'paths': self.hashed_files, 'version': self.manifest_version}
        if os.path.exists(self.manifest_name):
            os.remove(self.manifest_name)
        contents = json.dumps(payload).encode('utf-8')

        with open(self.manifest_name, "wb") as manifest:
            manifest.write(contents)
