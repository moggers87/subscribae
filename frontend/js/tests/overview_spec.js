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

describe("The overviewVideoFetcher plugin", function() {
    beforeEach(function(){
        this.html = $(`
            <div id="fixture" data-bucket-url="blah" data-api-url="bluh">
                <div class="spinner"></div>
            </div>
        `);
        $("html").append(this.html);
        spyOn(window.jQuery, "ajax");
    });

    afterEach(function() {
        $("#fixture").remove();
    });

    it("should be available as a jQuery plugin", function() {
        expect(jQuery.fn.overviewVideoFetcher).toBeDefined();
    });

    it("should fetch from the correct api", function() {
        $("#fixture").overviewVideoFetcher();

        expect(window.jQuery.ajax.calls.count()).toBe(1);
        expect(window.jQuery.ajax.calls.first().args[0].url).toBe("bluh");
        expect(typeof(window.jQuery.ajax.calls.first().args[0].success)).toBe("function");
    });

    it("should append html_snippet to the current element wrapped in an anchor tag", function() {
        $("#fixture").overviewVideoFetcher();
        window.jQuery.ajax.calls.first().args[0].success({"videos": [{id: "123", ordering_key: "321", html_snippet: "<div id=\"snippet\"></div>"}]});

        expect($("#snippet").parent()[0].tagName).toEqual("A");
        expect($("#snippet").parent()[0].pathname).toEqual("/blah");
        expect($("#snippet").parent()[0].search).toEqual("?start=321");
    });

    it("should remove the spinner once loaded", function() {
        $("#fixture").overviewVideoFetcher();
        window.jQuery.ajax.calls.first().args[0].success({"videos": [{id: "123", ordering_key: "321", html_snippet: "<div id=\"snippet\"></div>"}]});

        expect($(".spinner").length).toBe(0);
    });
});
