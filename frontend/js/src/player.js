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

    function Queue() {
        var QUEUE_IS_SMALL = 5;

        this.queue = [];
        this.index = -1;
        this.semaphore = false;

        Object.defineProperty(this, "length", {
            get: function() {
                return this.queue.length;
            }
        });

        this.isSmall = function() {
            return (this.queue.length - this.index) < QUEUE_IS_SMALL;
        };
    }

    function SubscribaePlayer(yt, playerElement, addVideosToPlaylist, setTitleAndDescription) {
        var player;
        var queue = new Queue();
        var apiUrl = playerElement.data("api-url");
        var csrfToken = playerElement.data("csrf");
        var viewedApiUrl = playerElement.data("viewed-api-url");

        /* methods */

        function fetchVideos(callback) {
            if (queue.semaphore) {
                return;
            }

            queue.semaphore = true;

            $.ajax({
                url: apiUrl,
                success: function(data, textStatus, jqXHR) {
                    apiUrl = data.next ? data.next : apiUrl;
                    callback(data.videos);
                    queue.semaphore = false;
                }
            });
        }

        function changeVideo(reverse) {
            var video;

            if (reverse === undefined && (queue.index >= (queue.length - 1))) {
                // last item, we can go no further forward
                return;
            } else if (reverse !== undefined && queue.index === 0) {
                // first item, we can go no further back
                return;
            }

            player.pauseVideo();

            checkQueueAndFetchMoreVideos();
            finishedVideo();

            video = popVideo(reverse);
            player.cueVideoById(video.id);
            setTitleAndDescription(video);
            player.playVideo();
        }

        function addVideosToQueue(videos) {
            Array.prototype.push.apply(queue.queue, videos);
            addVideosToPlaylist(videos.map(function(vid) {
                return vid.html_snippet;
            }));
        }

        function checkQueueAndFetchMoreVideos() {
            if (queue.isSmall()) {
                // TODO: there's a chance that this will populate the queue
                // after popVideo has run and returned undef. We should
                // probably try and recover from that state.
                fetchVideos(addVideosToQueue);
            }
        }

        function finishedVideo() {
            // TODO make this a service worker that can run even if the user
            // navigates away from the page
            if (queue.index < 0 || queue.index >= queue.length) {
                console.error("queueIndex out of range: " + queue.index);
                return;
            }

            $.ajax({
                url: viewedApiUrl,
                method: "POST",
                data: {
                    id: queue.queue[queue.index].id,
                    csrfmiddlewaretoken: csrfToken
                }
            });
        }

        function popVideo(reverse) {
            var index;

            if (reverse === undefined) {
                index = ++queue.index;
            } else {
                index = --queue.index;
            }

            return queue.queue[index];
        }

        function onPlayerState(event) {
            if (event.data == yt.PlayerState.ENDED) {
                checkQueueAndFetchMoreVideos();
                finishedVideo();

                var video = popVideo();
                if (video !== undefined) {
                    event.target.cueVideoById({videoId: video.id});
                    setTitleAndDescription(video);
                    event.target.playVideo();
                } else {
                    setTitleAndDescription();
                }
            }
        }

        /* export public methods and properties */
        this.fetchVideos = fetchVideos;
        this.changeVideo = changeVideo;
        this.queue = queue;

        /* initialise player and populate queue */
        fetchVideos(function(data) {
            var video;

            addVideosToQueue(data);

            video = popVideo();

            if (video !== undefined) {
                setTitleAndDescription(video);
                // player bugs out if we don't provide it with an initial video
                player = new yt.Player(playerElement[0], {
                    videoId: video.id,
                    events: {
                        "onStateChange": onPlayerState
                    }
                });
            } else {
                setTitleAndDescription();
            }
        });
    }


    $.fn.youtube = function(yt) {
        var $this = this;

        if ($this.length > 1) {
            throw new Error("This function can only be used on a single element.");
        } else if ($this.length === 0) {
            return $this;
        }

        var player;

        var $titleObj = $("#details-box .title");
        var $descObj = $("#details-box .description");
        var $playlistObj = $("#playlist");
        var $playlistObjScroller = $("#playlist-box .scroller");

        var $playerBox = $("#player-box");
        var noVideoTitle = $playerBox.data("no-video-title");
        var noVideoDescription = $playerBox.data("no-video-description");

        // controls

        $("#player-box .controls .back").on("click", function() {
            player.changeVideo(true);
        });

        $("#player-box .controls .forward").on("click", function() {
            player.changeVideo();
        });

        function setTitleAndDescription(video) {
            var $queueItem;
            var childTh = player.queue.index + 1;

            if (video === undefined) {
                $titleObj.text(noVideoTitle);
                $descObj.text(noVideoDescription);
            } else {
                $titleObj.text(video.title);
                $descObj.text(video.description);
                $playlistObj.children("div").removeClass("current-video");
                $queueItem = $playlistObj.children("div:nth-child(" + childTh + ")").addClass("current-video");

                $playlistObjScroller.scrollTop(
                    $playlistObjScroller.scrollTop() + ($queueItem.position().top - $playlistObjScroller.position().top)
                );
            }
        }

        player = new SubscribaePlayer(yt, $this, function(videos) {$playlistObj.append(videos);}, setTitleAndDescription);
        return $this;
    };
})(jQuery);


function onYouTubeIframeAPIReady() {
    'use strict';
    $("#player").youtube(YT);
}
