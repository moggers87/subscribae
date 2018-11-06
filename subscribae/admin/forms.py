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

from django.forms import ModelForm
from django.contrib.auth import get_user_model

from subscribae.forms import ErrorClassMixin
from subscribae.models import SiteConfig


class UserAddForm(ErrorClassMixin, ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["email", "is_active"]


class UserEditForm(ErrorClassMixin, ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["is_active"]


class SiteConfigForm(ErrorClassMixin, ModelForm):
    class Meta:
        model = SiteConfig
        fields = ["site_name", "footer_text"]
