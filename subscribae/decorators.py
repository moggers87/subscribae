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

from functools import wraps

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404


def active_user(fn):
    @wraps(fn)
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise ImproperlyConfigured("Use login_required before this decorator")
        elif request.user.is_active:
            return fn(request, *args, **kwargs)
        else:
            raise Http404("User is not active")

    return inner
