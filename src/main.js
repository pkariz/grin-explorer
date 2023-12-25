import Vue from 'vue'
import App from '@/App.vue'

import store from '@/store'
import router from '@/router'
import vuetify from './plugins/vuetify'
import '@/plugins/vee-validate'
import '@/plugins/vue-toasted'
import '@/plugins/apexcharts'


Vue.config.productionTip = false

const vue = new Vue({
  store,
  router,
  vuetify,
  render: h => h(App)
})

vue.$mount('#app')
