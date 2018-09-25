/*!
*    Subscribae
*    Copyright (C) 2018  Matt Molyneaux <moggers87+git@moggers87.co.uk>
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU General Public License as published by
*    the Free Software Foundation, either version 3 of the License, or
*    (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU General Public License for more details.
*
*    You should have received a copy of the GNU General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

function onYouTubeIframeAPIReady() {
    'use strict';
    (function($, yt) {
        var apiUrl, player;

        function onPlayerReady(event) {
            player.playVideo({videoId: "Vyjzj9DA3u4"});
        }

        apiUrl = $("#player").data("api-url");
        player = new yt.Player('player', {
            height: 390,
            width: 640,
            events: {
                "onReady": onPlayerReady
            }
        });
    })(jQuery, YT);
};
