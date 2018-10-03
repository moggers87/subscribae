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


def gae_login(user):
    # TODO consider mocking rather than changing the environment
    os.environ['USER_EMAIL'] = user.email
    os.environ['USER_ID'] = user.username


def gae_logout():
    # TODO consider mocking rather than changing the environment
    try:
        del os.environ['USER_EMAIL']
    except KeyError:
        pass

    try:
        del os.environ['USER_ID']
    except KeyError:
        pass
