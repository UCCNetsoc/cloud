import Vue from 'vue'
import App from './App.vue'
// import './registerServiceWorker'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import './global.css'
import 'material-design-icons-iconfont/dist/material-design-icons.css'
import 'typeface-roboto'

import { easterEgg } from './easterEgg'
import { openApiLoadSpec } from './api/openapi'

// window.addEventListener('load', () => {
openApiLoadSpec().then(() => {
  easterEgg()
  Vue.config.productionTip = true
  new Vue({
    router,
    store,
    vuetify,
    render: h => h(App)
  }).$mount('#app')
}).catch(() => {
  window.alert('UCC Netsoc API is down. Contact a SysAdmin on the UCC Netsoc Discord (https://discord.netsoc.co)')
})
// })
