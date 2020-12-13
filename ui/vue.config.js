const path = require("path");
const vueSrc = "./src";

module.exports = {
  transpileDependencies: [
    'vuetify'
  ],
  devServer: {
    // If you're developing on a VM
    // This is required if you're visiting an npm run serve
    // without a localhost URL
    disableHostCheck: true
  },
  configureWebpack: {
    resolve: {
      alias: {
        "@": path.resolve(__dirname, vueSrc)
      },
      extensions: ['.js', '.vue', '.json']
    }
  }
}
