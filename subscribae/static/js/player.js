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
        var QUEUE_IS_SMALL = 5;

        var player, apiUrl;
        var queue = [];
        var queueIndex = 0;
        var $titleObj = $("#details-box .title");
        var $descObj = $("#details-box .description");
        var $playlistObj = $("#playlist");

        var $playerBox = $("#player-box");
        var noVideoTitle = $playerBox.data("no-video-title");
        var noVideoDescription = $playerBox.data("no-video-description");

        function fetchVideos(callback) {
            $.ajax(apiUrl, {
                success: function(data, textStatus, jqXHR) {
                    apiUrl = data.next ? data.next : apiUrl;
                    callback(data.videos);
                }
            });
        }

        function addVideos(videos) {
            Array.prototype.push.apply(queue, videos);
            $playlistObj.append(videos.map(function(vid) {
                return vid.html_snippet;
            }));

        }

        function popVideo() {
            return queue[queueIndex++];
        }

        function setMeta(video) {
            $titleObj.text(video.title);
            $descObj.text(video.description);
        }

        function noVideo() {
            $titleObj.text(noVideoTitle);
            $descObj.text(noVideoDescription);
        }

        function onPlayerState(event) {
            if (event.data == yt.PlayerState.ENDED) {
                if ((queue.length - queueIndex) < QUEUE_IS_SMALL) {
                    // TODO: there's a chance that this will populate the queue
                    // after popVideo has run and returned undef. We should
                    // probably try and recover from that state.
                    fetchVideos(addVideos);
                }

                var video = popVideo();
                if (video !== undefined) {
                    event.target.cueVideoById({videoId: video.id});
                    setMeta(video);
                    event.target.playVideo();
                } else {
                    noVideo();
                }
            }
        }

        apiUrl = $("#player").data("api-url");
        fetchVideos(function(data) {
            var video;

            addVideos(data);

            video = popVideo();

            if (video !== undefined) {
                setMeta(video);
                // player bugs out if we don't provide it with an initial video
                player = new yt.Player('player', {
                    videoId: video.id,
                    events: {
                        "onStateChange": onPlayerState
                    }
                });
            } else {
                noVideo();
            }
        });
    })(jQuery, YT);
}
