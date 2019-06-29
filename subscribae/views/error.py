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
##
#    Copyright (C) 2013-2015 Jessica Tallon, Matt Molyneaux
#
#    This file is part of Inboxen.
#
#    Inboxen is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Inboxen is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with Inboxen.  If not, see <http://www.gnu.org/licenses/>.
##

import logging

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, UnreadablePostError
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

_log = logging.getLogger(__name__)


class ErrorView(TemplateView):
    error_message = None
    error_code = None

    headline = _("Some sort of error or something")
    template_name = "subscribae/error.html"

    def dispatch(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        output = self.render_to_response(context, status=self.error_code)
        output.render()
        return output

    def get_context_data(self, **kwargs):
        kwargs["error_message"] = self.get_error_message()
        kwargs["error_code"] = self.get_error_code()
        kwargs["headline"] = self.headline
        return super(ErrorView, self).get_context_data(**kwargs)

    def get_error_message(self):
        """Returns a short error message to be displayed to the user"""
        if self.error_message is None:
            raise ImproperlyConfigured("Set 'error_message' or override 'get_error_message'")
        else:
            return self.error_message

    def get_error_code(self):
        """Returns the numeric HTTP status code"""
        if self.error_code is None:
            raise ImproperlyConfigured("Set 'error_code' or override 'get_error_code'")
        else:
            return self.error_code

    def get_template_names(self):
        templates = ["{0}.html".format(self.get_error_code())]
        templates.extend(super(ErrorView, self).get_template_names())
        return templates

    @classonlymethod
    def as_view(cls, **initkwargs):
        """A very stripped down version of as_view that will work with the
        error handler *check* code"""
        # grumbles grumbles

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            # change this to self.setup() when we're on Django 2.2
            self.request = request
            self.args = args
            self.kwargs = kwargs
            return self.dispatch(request, *args, **kwargs)

        return view


not_found = ErrorView.as_view(
    error_message=_("We can't find this."),
    error_code=404,
    headline=_("Not Found"),
)


permission_denied = ErrorView.as_view(
    error_message=_("You're not allowed."),
    error_code=403,
    headline=_("Permission Denied"),
)


csrf_failure = ErrorView.as_view(
    error_message=_("Hmm, I don't like this"),
    error_code=403,
    headline=_("CSRF Check Failed"),
)


server_error = ErrorView.as_view(
    error_message=_("I broke something."),
    error_code=500,
    headline=_("Error"),
)


bad_request = ErrorView.as_view(
    error_message=_("What is this?"),
    error_code=400,
    headline=_("Bad Request"),
)


@csrf_exempt
@require_POST
def csp_report(request):
    """Simple CSP report view"""
    try:
        _log.warning("CSP Report: %s", request.body)
    except UnreadablePostError:
        pass
    return HttpResponse("")
