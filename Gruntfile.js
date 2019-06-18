module.exports = function(grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON("package.json"),
        dirs: {
            build: "frontend/build",
            thirdparty: "node_modules",
            js: "frontend/js",
            css: "frontend/css",
        },
        concat: {
            dist: {
                src: ["<%= dirs.thirdparty %>/jquery/dist/jquery.js", "<%= dirs.js %>/src/*.js"],
                dest: "<%= dirs.build %>/src/website.js",
                nonnull: true
            }
        },
        uglify: {
            options: {
                mangle: true,
                compress: true,
                output: {
                    comments: /^!/
                }
            },
            dist: {
                src: ["<%= dirs.build %>/src/website.js"],
                dest: "<%= dirs.build %>/compiled/website.min.js"
            }
        },
        postcss: {
            options: {
                failOnError: true,
                processors: [
                    require("postcss-import"),
                    require('postcss-preset-env')({
                        stage: 1,
                        features: {
                            'color-mod-function': {
                                unresolved: 'warn'
                            },
                            'custom-properties': {
                                preserve: false
                            },
                            'nesting-rules': true
                        }
                    }),
                    require("cssnano")({
                        autoprefixer: false
                    }),
                ]
            },
            dist: {
                src: ["<%= dirs.css %>/subscribae.css"],
                dest: "<%= dirs.build %>/compiled/website.css"
            }
        },
        karma: {
            options: {
                client: {
                    jasmine: {
                        random: true,
                        stopSpecOnExpectationFailure: false
                    }
                },
                configFile: "karma.conf.js",
                preprocessors: {"<%= dirs.js %>/src/*.js": ["coverage"]},
                files: [
                    "<%= dirs.thirdparty %>/jquery/dist/jquery.js",
                    "<%= dirs.js %>/src/*.js",
                    "<%= dirs.js %>/tests/*.js"
                ]
            },
            chrome: {
                singleRun: true,
                browsers: ["ChromeMaybeHeadless"]
            },
            firefox: {
                singleRun: true,
                browsers: ["Firefox"]
            },
            chromeDebug: {
                singleRun: false,
                browsers: ["ChromeMaybeHeadless"]
            },
            firefoxDebug: {
                singleRun: false,
                browsers: ["Firefox"]
            }
        },
        jshint: {
            options: {jshintrc: true},
            all: ["."]
        }
    });
    grunt.loadNpmTasks("grunt-contrib-concat");
    grunt.loadNpmTasks("grunt-contrib-uglify");
    grunt.loadNpmTasks('@lodder/grunt-postcss');
    grunt.loadNpmTasks('grunt-karma');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.registerTask("default", ["concat", "uglify", "postcss"]);
    grunt.registerTask("tests", ["karma:firefox", "karma:chrome"]);
};
