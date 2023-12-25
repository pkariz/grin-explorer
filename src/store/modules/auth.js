import { loginUser, logoutUser } from '@/services/auth';

const state = {
  user: null,
  isLoggedIn: false,
}

const getters = {
  isLoggedIn: state => {
    return state.isLoggedIn
  }
}

const actions = {
  login({ commit }, { username, password }) {
    return loginUser(username, password)
      .then(() => {
        commit({ type: 'loginSuccess', username });
        return Promise.resolve();
      }).catch((error) => {
        commit({ type: 'logout' });
        return Promise.reject(error);
      });
  },
  logout({ commit }) {
    logoutUser();
    commit('logout');
  },
}

const mutations = {
  loginSuccess(state, userId) {
    state.user = userId;
    state.isLoggedIn = true;
  },
  logout(state) {
    state.user = null;
    state.isLoggedIn = false;
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
