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

describe("The player", function() {
    it("should define onYouTubeIframeAPIReady", function() {
        expect(onYouTubeIframeAPIReady).toBeDefined();
    });

    describe("when ready", function() {
        beforeEach(function() {
            this.html = $(`
                <div id="fixture">
                    <style>
                        #playlist-box {}
                        .scroller {
                            overflow-y: scroll;
                        }
                        #playlist {}
                        #playlist div {
                            height: 100px;
                        }
                    </style>
                    <div id="player-box"
                        data-no-video-title="No more videos"
                        data-no-video-description="Sorry, looks like you've watched everything!">
                        <div id="player"
                             data-api-url="https://example.com/videos"
                             data-viewed-api-url="https://example.com/viewed"
                             data-csrf="a1b2c3"></div>
                        <div id="playlist-box" style="height: 14px">
                            <div class="scroller" style="overflow-y: scroll">
                                <div id="playlist" style="height: 14px"></div>
                            </div>
                        </div>
                        <div id="details-box">
                            <div class="title"></div>
                            <div class="description"></div>
                        </div>
                        <div class="controls">
                            <button class="back">Back</button>
                            <button class="forward">Forward</button>
                        </div>
                    </div>
                </div>
            `);
            $("html").append(this.html);

            window.YT = jasmine.createSpy();
            window.YT.Player = jasmine.createSpy();

            spyOn(window.jQuery, "ajax");
        });

        afterEach(function() {
            $("#fixture").remove();
        });

        it("should call the API", function() {
            onYouTubeIframeAPIReady();
            expect(window.jQuery.ajax.calls.count()).toBe(1);
            expect(window.jQuery.ajax.calls.first().args[0].url).toBe("https://example.com/videos");
            expect(typeof(window.jQuery.ajax.calls.first().args[0].success)).toBe("function");
        });

        describe("the data has been fetched", function() {
            beforeEach(function() {
                onYouTubeIframeAPIReady();
                this.ajaxFunc = window.jQuery.ajax.calls.first().args[0].success;
            });

            it("should listen to the onStateChange event", function() {
                this.ajaxFunc({"videos": [{id: "123", html_snippet: "<div></div>"}]});
                expect(window.YT.Player.calls.count()).toBe(1);

                var args = window.YT.Player.calls.first().args;
                expect(typeof(args[1].events.onStateChange)).toBe('function');
            });

            it("should start with the first video", function() {
                this.ajaxFunc({"videos": [{id: "123", html_snippet: "<div></div>"}]});
                expect(window.YT.Player.calls.count()).toBe(1);

                var args = window.YT.Player.calls.first().args;
                expect(args[1].videoId).toBe("123");
            });

            it("should set the title and description correctly", function() {
                this.ajaxFunc({"videos": [{id: "123", title: "hello title", description: "hello description", html_snippet: "<div>Hello</div>"}]});

                expect(window.YT.Player.calls.count()).toBe(1);
                expect($(".title").text()).toBe("hello title");
                expect($(".description").text()).toBe("hello description");
            });

            it("should set populate the playlist", function() {
                expect($("#playlist").children().length).toBe(0);
                this.ajaxFunc({"videos": [{id: "123", title: "hello title", description: "hello description", html_snippet: "<div>Hello</div>"}]});

                expect(window.YT.Player.calls.count()).toBe(1);
                expect($("#playlist").children().length).toBe(1);
                expect($("#playlist").children().text()).toBe("Hello");
            });

            it("should work even if there are no videos", function() {
                this.ajaxFunc({"videos": []});
                expect(window.YT.Player.calls.count()).toBe(0);
                expect($(".title").text()).toBe("No more videos");
                expect($(".description").text()).toBe("Sorry, looks like you've watched everything!");
            });

            describe("and the queue is populated", function() {
                beforeEach(function() {
                    this.ajaxFunc({"videos": [
                        {id: "123", title: "first", description: "first", html_snippet: "<div>first</div>"},
                        {id: "456", title: "second", description: "second", html_snippet: "<div>second</div>"},
                    ]});
                    var playerStateEnd = 123;
                    this.fakeEvent = {data: playerStateEnd, target: {
                        playVideo: jasmine.createSpy(),
                        cueVideoById: jasmine.createSpy()
                    }};
                    this.playerEvents = window.YT.Player.calls.first().args[1].events;
                    window.YT.PlayerState = {ENDED: playerStateEnd};
                    window.YT.Player.prototype.playVideo = jasmine.createSpy();
                    window.YT.Player.prototype.cueVideoById = jasmine.createSpy();
                    window.YT.Player.prototype.pauseVideo = jasmine.createSpy();
                });

                it("should go forwards via a button press", function() {
                    expect($(".current-video").text()).toBe("first");
                    $(".controls .forward").click();
                    expect($(".current-video").text()).toBe("second");
                    expect($(".current-video").position().top).toBe($(".scroller").position().top);
                    expect(window.jQuery.ajax.calls.count()).toBe(3);
                    expect(window.jQuery.ajax.calls.argsFor(2)[0].url).toBe("https://example.com/viewed");
                    expect(window.jQuery.ajax.calls.argsFor(2)[0].data).toEqual({id: '123', csrfmiddlewaretoken: "a1b2c3"});
                    expect(window.jQuery.ajax.calls.argsFor(2)[0].method).toBe("POST");
                });

                it("should go backwards via a button press", function() {
                    $(".controls .forward").click();
                    expect($(".current-video").text()).toBe("second");
                    $(".controls .back").click();
                    expect($(".current-video").text()).toBe("first");
                    expect($(".current-video").position().top).toBe($(".scroller").position().top);
                    expect(window.jQuery.ajax.calls.count()).toBe(4);
                    expect(window.jQuery.ajax.calls.argsFor(3)[0].url).toBe("https://example.com/viewed");
                    expect(window.jQuery.ajax.calls.argsFor(3)[0].data).toEqual({id: '456', csrfmiddlewaretoken: "a1b2c3"});
                    expect(window.jQuery.ajax.calls.argsFor(3)[0].method).toBe("POST");
                });

                it("should not error when the back button is pressed at the beginning of the queue", function() {
                    $(".controls .back").click();
                    $(".controls .back").click();
                    expect($(".current-video").text()).toBe("first");
                    expect(window.jQuery.ajax.calls.count()).toBe(1);
                });

                it("should not error when the forward button is pressed at the end of the queue", function() {
                    $(".controls .forward").click();
                    $(".controls .forward").click();
                    $(".controls .forward").click();
                    expect($(".current-video").text()).toBe("second");
                    expect(window.jQuery.ajax.calls.count()).toBe(3);
                    expect(window.jQuery.ajax.calls.argsFor(2)[0].url).toBe("https://example.com/viewed");
                    expect(window.jQuery.ajax.calls.argsFor(2)[0].data).toEqual({id: '123', csrfmiddlewaretoken: "a1b2c3"});
                    expect(window.jQuery.ajax.calls.argsFor(2)[0].method).toBe("POST");
                });

                it("should progress through the queue nicely", function() {
                    expect($(".current-video").text()).toBe("first");
                    this.playerEvents.onStateChange(this.fakeEvent);
                    expect($(".title").text()).toBe("second");
                    expect($(".description").text()).toBe("second");

                    expect(this.fakeEvent.target.playVideo.calls.count()).toBe(1);
                    expect(this.fakeEvent.target.cueVideoById.calls.count()).toBe(1);
                    expect($(".current-video").text()).toBe("second");

                });

                it("should ignore player states that we don't know about", function() {
                    this.fakeEvent.data = null;
                    this.playerEvents.onStateChange(this.fakeEvent);
                    expect($(".title").text()).toBe("first");
                    expect($(".description").text()).toBe("first");

                    expect(this.fakeEvent.target.playVideo.calls.count()).toBe(0);
                    expect(this.fakeEvent.target.cueVideoById.calls.count()).toBe(0);
                });

                it("should get to the end of the queue nicely", function() {
                    this.playerEvents.onStateChange(this.fakeEvent);
                    this.playerEvents.onStateChange(this.fakeEvent);
                    expect($(".title").text()).toBe("No more videos");
                    expect($(".description").text()).toBe("Sorry, looks like you've watched everything!");

                    expect(this.fakeEvent.target.playVideo.calls.count()).toBe(1);
                    expect(this.fakeEvent.target.cueVideoById.calls.count()).toBe(1);
                });

                it("should try to fetch the next batch of videos and be ok with an empty set", function() {
                    this.ajaxFunc({next: "https://example.com/videos?page=2", videos: []});
                    this.playerEvents.onStateChange(this.fakeEvent);
                    expect(window.jQuery.ajax.calls.count()).toBe(3);
                    expect(window.jQuery.ajax.calls.argsFor(1)[0].url).toBe("https://example.com/videos?page=2");
                    expect(typeof(window.jQuery.ajax.calls.argsFor(1)[0].success)).toBe("function");
                });

                it("should not try to fetch the next batch of videos if the queue if full enough", function() {
                    this.ajaxFunc({next: "https://example.com/videos?page=2", videos: [
                        {id: 1, title: "title", description: "description", html_snippet: "<div></div>"},
                        {id: 2, title: "title", description: "description", html_snippet: "<div></div>"},
                        {id: 3, title: "title", description: "description", html_snippet: "<div></div>"},
                        {id: 4, title: "title", description: "description", html_snippet: "<div></div>"},
                        {id: 5, title: "title", description: "description", html_snippet: "<div></div>"},
                    ]});
                    this.playerEvents.onStateChange(this.fakeEvent);
                    // only one more call is made - to finished video
                    expect(window.jQuery.ajax.calls.count()).toBe(2);
                    expect(window.jQuery.ajax.calls.argsFor(1)[0].url).toBe("https://example.com/viewed");
                    // this is technically wrong, but this.ajaxFunc is actually
                    // the wrong callback. If you can work out how to get the
                    // right callback then the next line should be comparing to
                    // '123', not '456'
                    expect(window.jQuery.ajax.calls.argsFor(1)[0].data).toEqual({id: '456', csrfmiddlewaretoken: "a1b2c3"});
                    expect(window.jQuery.ajax.calls.argsFor(1)[0].method).toBe("POST");
                });
            });
        });
    });
});
