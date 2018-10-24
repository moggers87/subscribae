module.exports = {
    plugins: [
        require("postcss-import")({
            path: [
            ]
        }),
        require("postcss-cssnext")({
            features: {
                rem: false
            }
        }),
        require("cssnano")({
            autoprefixer: false
        }),
    ]
};
