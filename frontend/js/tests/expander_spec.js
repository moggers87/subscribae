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

describe("The Expando plugin", function() {
    beforeEach(function() {
        this.html = $(`
            <div id="fixture">
                <div class="expander">
                    <div class="scroller"></div>
                    <div class="more"><button>Show more</button></div>
                </div>
            </div>
        `);
        $("html").append(this.html);
        this.html.find(".expander").subscribaeExpando();
    });

    afterEach(function() {
        $("#fixture").remove();
    });

    it("should be available as a jQuery plugin", function() {
        expect(jQuery.fn.subscribaeExpando).toBeDefined();
    });


    it("should apply the expander class when clicked", function() {
        expect($(".expander").attr("class")).toBe("expander");
        $(".more button").click();
        expect($(".expander").attr("class")).toBe("expander expanded");
    });

    it("should remove the expander class when clicked", function() {
        expect($(".expander").attr("class")).toBe("expander");
        $(".more button").click();
        $(".more button").click();
        expect($(".expander").attr("class")).toBe("expander");
    });
});
