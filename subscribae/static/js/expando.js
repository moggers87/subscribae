/*!
*    Copyright (C) 2018 Matt Molyneaux <moggers87+git@moggers87.co.uk>
*
*    This file is part of Subscribae.
*
*    Subscribae is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as published by
*    the Free Software Foundation, either version 3 of the License, or
*    (at your option) any later version.
*
*    Subscribae is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*
*    You should have received a copy of the GNU Affero General Public License
*    along with Subscribae.  If not, see <http://www.gnu.org/licenses/>.
*/


(function($) {
    'use strict';

    $.fn.subscribaeExpando = function() {
        this.each(function() {
            var $this = $(this);
            var expanded = false;
            var cssClass = "expanded";
            var more = $this.data("more");
            var less = $this.data("less");

            $this.find(".more").click(function(e) {
                e.preventDefault();

                if (expanded) {
                    expanded = false;
                    $this.removeClass(cssClass);
                    $(e.target).text(more);
                } else {
                    expanded = true;
                    $this.addClass(cssClass);
                    $(e.target).text(less);
                }
            });
        });

        return this;
    };

    $(function() {
        $(".x-scroll").subscribaeExpando();
    });
})(jQuery);
