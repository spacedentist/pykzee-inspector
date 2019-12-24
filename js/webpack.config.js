const path = require("path");
const webpack = require("webpack");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

const dev = true;

module.exports = {
  entry: "./src/main.js",
  output: {
    filename: "inspector.js",
    path: path.resolve(__dirname, "../pykzee/inspector/resources/static"),
    publicPath: "/static/",
  },
  module: {
    rules: [
      {
        test: /\.(js|svelte)$/,
        exclude: /\/node_modules\//,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env"],
          },
        },
      },
      {
        test: /\.svelte$/,
        use: {
          loader: "svelte-loader",
          options: {
            generate: "dom",
            css: true,
            emitCss: true,
            hydratable: false,
            dev,
          },
        },
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, "css-loader"],
      },
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "style.css",
    }),
    new webpack.optimize.LimitChunkCountPlugin({
      maxChunks: 1,
    }),
  ],
};
