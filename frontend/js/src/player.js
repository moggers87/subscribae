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


function onYouTubeIframeAPIReady() {
    'use strict';
    (function($, yt) {
        var QUEUE_IS_SMALL = 5;

        var player;
        var queue = [];
        var queueIndex = -1;
        var $titleObj = $("#details-box .title");
        var $descObj = $("#details-box .description");
        var $playlistObj = $("#playlist");
        var $playlistObjScroller = $("#playlist-box .scroller");
        var queueLocked = false;

        var $playerBox = $("#player-box");
        var noVideoTitle = $playerBox.data("no-video-title");
        var noVideoDescription = $playerBox.data("no-video-description");
        var $previousButton = $(".controls .back");
        var $nextButton = $(".controls .forward");

        var apiUrl = $("#player").data("api-url");
        var csrfToken = $("#player").data("csrf");

        function fetchVideos(callback) {
            if (queueLocked) {
                return;
            }

            queueLocked = true;

            $.ajax({
                url: apiUrl,
                success: function(data, textStatus, jqXHR) {
                    apiUrl = data.next ? data.next : apiUrl;
                    callback(data.videos);
                    queueLocked = false;
                }
            });
        }

        function addVideos(videos) {
            Array.prototype.push.apply(queue, videos);
            $playlistObj.append(videos.map(function(vid) {
                return vid.html_snippet;
            }));

        }

        function popVideo(reverse) {
            var index;

            if (reverse === undefined) {
                index = ++queueIndex;
            } else {
                index = --queueIndex;
            }

            return queue[index];
        }

        function setMeta(video) {
            var $queueItem;
            var childTh = queueIndex + 1;

            $titleObj.text(video.title);
            $descObj.text(video.description);
            $playlistObj.children("div").removeClass("current-video");
            $queueItem = $playlistObj.children("div:nth-child(" + childTh + ")").addClass("current-video");

            $playlistObjScroller.scrollTop($playlistObjScroller.scrollTop() + ($queueItem.position().top - $playlistObjScroller.position().top));

        }

        function noVideo() {
            $titleObj.text(noVideoTitle);
            $descObj.text(noVideoDescription);
        }

        function finishedVideo() {
            // TODO make this a service worker that can run even if the user
            // navigates away from the page
            if (queueIndex < 0 || queueIndex >= queue.length) {
                console.error("queueIndex out of range: " + queueIndex);
                return;
            }

            $.ajax({
                url: apiUrl,
                method: "POST",
                data: {
                    id: queue[queueIndex].id,
                    csrfmiddlewaretoken: csrfToken
                }
            });
        }

        function checkQueueAndFetchMoreVideos() {
            if ((queue.length - queueIndex) < QUEUE_IS_SMALL) {
                // TODO: there's a chance that this will populate the queue
                // after popVideo has run and returned undef. We should
                // probably try and recover from that state.
                fetchVideos(addVideos);
            }
        }

        function onPlayerState(event) {
            if (event.data == yt.PlayerState.ENDED) {
                checkQueueAndFetchMoreVideos();
                finishedVideo();

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

        // controls

        function changeVideo(reverse) {
            var video;

            player.pauseVideo();

            checkQueueAndFetchMoreVideos();
            finishedVideo();

            video = popVideo(reverse);
            player.cueVideoById(video.id);
            setMeta(video);
            player.playVideo();
        }

        $previousButton.click(function() {
            if (queueIndex !== 0) {
                changeVideo(true);
            }
        });

        $nextButton.click(function() {
            if (queueIndex < (queue.length - 1)) {
                changeVideo();
            }
        });

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