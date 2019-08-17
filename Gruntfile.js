module.exports = function(grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON("package.json"),
        dirs: {
            build: "frontend/build",
            thirdparty: "node_modules",
            js: "frontend/js",
            css: "frontend/css",
        },
        clean: {
            build: ["<%= dirs.build %>"],
        },
        concat: {
            options: {
                sourceMap: true
            },
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
                sourceMap: {
                    includeSources: true
                },
                sourceMapIn: function(path) {
                    return path + ".map";
                },
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
                map: {
                    inline: false,
                    sourcesContent: true
                },
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
            publicCss: {
                src: ["<%= dirs.css %>/public.css"],
                dest: "<%= dirs.build %>/compiled/public.css"
            },
            adminCss: {
                src: ["<%= dirs.css %>/admin.css"],
                dest: "<%= dirs.build %>/compiled/admin.css"
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

    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks("grunt-contrib-concat");
    grunt.loadNpmTasks("grunt-contrib-uglify");
    grunt.loadNpmTasks('@lodder/grunt-postcss');
    grunt.loadNpmTasks('grunt-karma');
    grunt.loadNpmTasks('grunt-contrib-jshint');

    grunt.registerTask("default", ["clean", "concat", "uglify", "postcss"]);
    grunt.registerTask("tests", ["karma:firefox", "karma:chrome"]);
};
