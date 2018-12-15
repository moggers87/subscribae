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

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden

from subscribae.decorators import active_user
from subscribae.models import OauthToken
from subscribae.utils import get_oauth_flow


@login_required
@active_user
def oauth_start(request):
    flow = get_oauth_flow(request.user)
    auth_uri = flow.step1_get_authorize_url()
    return HttpResponseRedirect(auth_uri)


@login_required
@active_user
def oauth_callback(request):
    if "code" in request.GET:
        auth_code = request.GET["code"]
        flow = get_oauth_flow(request.user)

        credentials = flow.step2_exchange(auth_code)
        OauthToken.objects.update_or_create(user=request.user, defaults={'data': credentials.to_json()})

        redirect_uri = reverse(request.session.get(settings.OAUTH_RETURN_SESSION_KEY, 'home'))
        return HttpResponseRedirect(redirect_uri)
    else:
        return HttpResponseForbidden("Something went wrong: %s" % request.GET)
