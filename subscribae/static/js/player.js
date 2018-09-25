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
        var player, apiUrl;
        var queue = [];
        var $titleObj = $("#details-box .title");
        var $descObj = $("#details-box .description");

        function fetchVideos(callback) {
            $.ajax(apiUrl, {
                success: function(data, textStatus, jqXHR) {
                    apiUrl = data.next;
                    callback(data.videos);
                }
            });
        }

        function addVideos(videos) {
            Array.prototype.push.apply(queue, videos);
        }

        function popVideo() {
            return queue.shift();
        }

        function setMeta(video) {
            $titleObj.text(video.title);
            $descObj.text(video.description);
        }

        function onPlayerState(event) {
            if (event.data == yt.PlayerState.ENDED) {
                var video = popVideo();
                event.target.cueVideoById({videoId: video.id});
                setMeta(video);
                event.target.playVideo();
            }
        }

        apiUrl = $("#player").data("api-url");
        fetchVideos(function(data) {
            var video;

            addVideos(data);

            video = popVideo();
            setMeta(video);
            // player bugs out if we don't provide it with an initial video
            player = new yt.Player('player', {
                height: 390,
                width: 640,
                videoId: video.id,
                events: {
                    "onStateChange": onPlayerState
                }
            });

        });
    })(jQuery, YT);
}
