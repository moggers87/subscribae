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

from django.conf.urls import url

from subscribae.admin import views


urlpatterns = (
    url(r'^$', views.index, name='index'),
    url(r'^users/$', views.user_index, name='user-index'),
    url(r'^users/add_user/$', views.user_add, name='user-add'),
    url(r'^users/edit_user/(?P<user_id>[a-zA-Z0-9\.]+)/$', views.user_edit, name='user-edit'),
)
