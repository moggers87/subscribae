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
import logging

from djangae.db.consistency import ensure_instance_consistent
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.template.response import TemplateResponse

from subscribae.admin.forms import UserAddForm, UserEditForm


_log = logging.getLogger(__name__)

USER_PAGE_SIZE = 50


def admin_for_superusers(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        if not request.user.is_superuser:
            _log.info("%s is not an admin, but tried to access %s", request.user, request.path)
            raise Http404("Admins must be Superusers")

        return func(request, *args, **kwargs)

    # private api to check that decorators have been added
    inner.__dict__.setdefault("_subscribae_decorators", [])
    inner.__dict__["_subscribae_decorators"].append(admin_for_superusers)

    return inner


@admin_for_superusers
def index(request):
    return TemplateResponse(request, "admin/index.html", {})


@admin_for_superusers
def user_index(request):
    user_qs = get_user_model().objects.all()

    before = request.GET.get("before")
    after = request.GET.get("after")
    new_user = request.GET.get("new_user")

    if before is not None:
        user_qs = user_qs.order_by("pk").filter(pk__lt=before)
    elif after is not None:
        user_qs = user_qs.order_by("-pk").filter(pk__gt=after)
    else:
        user_qs = user_qs.order_by("pk")
        if new_user is not None:
            user_qs = ensure_instance_consistent(user_qs, new_user)

    user_qs = user_qs[:USER_PAGE_SIZE]

    return TemplateResponse(request, "admin/user_index.html", {"users": user_qs})


@admin_for_superusers
def user_add(request):
    if request.method == "POST":
        form = UserAddForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            # All index view to bypass EC
            return HttpResponseRedirect("%s?new_user=%s" % (reverse('admin:user-index'), user.pk))
    else:
        form = UserAddForm()

    return TemplateResponse(request, 'admin/user_add.html', {"form": form})


@admin_for_superusers
def user_edit(request, user_id):
    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        raise Http404

    if request.method == "POST":
        form = UserEditForm(instance=user, data=request.POST)
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect(reverse('admin:user-index'))
    else:
        form = UserEditForm(instance=user)

    return TemplateResponse(request, 'admin/user_edit.html', {"form": form})