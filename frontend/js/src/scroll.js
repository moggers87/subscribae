/*!
*    Copyright (C) 2019 Matt Molyneaux <moggers87+git@moggers87.co.uk>
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

    $.fn.scroller = function() {
        this.each(function() {
            var $this = $(this);
            var items = $this.find(".item");
            var scroller = $this.find(".scroller")[0];

            function isVisible(el, container) {
                var scrollLeft = container.offsetLeft + container.scrollLeft;
                // is the right edge of the child inside the right edge of the parent?
                return el.offsetLeft + el.offsetWidth <= container.offsetWidth + scrollLeft &&
                    // is the left edge of the child inside the left edge of the parent?
                    el.offsetLeft >= scrollLeft;
            }

            function findVisible() {
                /* return the indices of the currently visible items */
                var start = null;
                var end = null;
                for (var i = 0; i < items.length; i++) {
                    var visible = isVisible(items[i], scroller);
                    if (start === null && visible) {
                        start = i;
                    } else if (start !== null && end === null && !visible) {
                        end = i - 1;
                    }
                }
                if (start === null) {
                    start = 0;
                }
                if (end === null) {
                    end = items.length - 1;
                }
                return [start, end];
            }

            $this.find(".scroll-left").on("click", function() {
                var visibleIdx = findVisible();
                var diffIdx = Math.max((visibleIdx[1] - visibleIdx[0]), 1);
                var newIdx = Math.max((visibleIdx[0] - diffIdx), 0);
                scroller.scrollLeft = items[newIdx].offsetLeft - scroller.offsetLeft;
            });

            $this.find(".scroll-right").on("click", function() {
                var visibleIdx = findVisible();
                var diffIdx = Math.max(visibleIdx[1] - visibleIdx[0], 1);
                var newIdx = Math.min(visibleIdx[1] + diffIdx, items.length - 1);
                scroller.scrollLeft = items[newIdx].offsetLeft - scroller.offsetLeft;
            });
        });

        return this;
    };

    $(function() {
        $(".x-scroll").scroller();
    });
})(jQuery);
