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

    $.fn.overviewVideoFetcher = function() {
        this.each(function() {
            var $this = $(this);
            var bucketUrl = $this.data("bucket-url");
            var apiUrl = $this.data("api-url");

            $.ajax({
                url: apiUrl,
                success: function(data, textStatus, jqXHR) {
                    $this.find(".spinner").remove();
                    $this.append(data.videos.map(function(vid) {
                        var url = bucketUrl + "?start=" + vid.ordering_key;
                        return "<a href=\"" + url + "\">" + vid.html_snippet + "</a>";
                    }));
                }
            });
        });

        return this;
    };

    $(function() {
        $(".bucket-list .videos").overviewVideoFetcher();
    });
})(jQuery);
