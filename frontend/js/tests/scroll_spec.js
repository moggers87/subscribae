/*!
*    Subscribae
*    Copyright (C) 2019  Matt Molyneaux <moggers87+git@moggers87.co.uk>
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

describe("The scroller plugin", function() {
    beforeEach(function() {
        this.html = $(`<div id="fixture">
            <div class="scroll-left"></div>
            <div class="scroll-right"></div>
            <div class="scroller">
                <div class="item">item 1</div>
                <div class="item">item 2</div>
                <div class="item">item 3</div>
            </div>
        </div>`);
        $("html").append(this.html);
        this.addCss = function() {
            $(".scroller").css({
                "overflow": "scroll",
                "width": "300px",
                "display": "flex",
                "flex": "0 0 auto"
            });
            $(".item").css({
                "min-width": "200px",
                "display": "inline-block"
            });
        };
        $("#fixture").scroller();
    });

    afterEach(function() {
        $("#fixture").remove();
    });

    it("should be available as a jQuery plugin", function() {
        expect(jQuery.fn.scroller).toBeDefined();
    });

    it("should do nothing when there is no need to scroll", function() {
        var scroller = this.html.find(".scroller")[0];
        var initialScroll = scroller.scrollLeft;

        $(".scroll-left").trigger("click");
        expect(scroller.scrollLeft).toEqual(initialScroll);

        $(".scroll-right").trigger("click");
        expect(scroller.scrollLeft).toEqual(initialScroll);
    });

    it("should scroll to the next item", function() {
        this.addCss();

        scroller = this.html.find(".scroller")[0];

        $(".scroll-right").trigger("click");
        expect(scroller.scrollLeft).toEqual(200);

    });

    it("should scroll to the previous item", function() {
        var scroller;
        this.addCss();

        scroller = this.html.find(".scroller")[0];
        scroller.scrollLeft = 400;

        $(".scroll-left").trigger("click");
        expect(scroller.scrollLeft).toEqual(200);
    });
});
