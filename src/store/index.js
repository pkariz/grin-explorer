import Vue from 'vue'
import Vuex from 'vuex'
import auth from './modules/auth'
import blockchain from './modules/blockchain'
import createPersistedState from 'vuex-persistedstate';

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    auth,
    blockchain,
  },
  plugins: [
    createPersistedState({
      paths: ['auth'],
    }),
  ],
})
