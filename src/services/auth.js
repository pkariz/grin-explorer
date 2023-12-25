import axios from 'axios';
import Vue from 'vue';
import store from '@/store/index';
import router from '@/router'
import { decodeJWT } from '@/shared/helpers';

const BACKEND_URL = String(process.env.VUE_APP_BACKEND_URL);
const ACCESS_TOKEN = 'access_token';
const API_TIMEOUT = 10000;

const api = axios.create({
  baseURL: BACKEND_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    accept: 'application/json',
  },
});

const loginUser = (username, password) => {
  return api.post('/account/token/', { username, password })
    .then((response) => {
      if (!response.data.access) {
        throw Error('got invalid ACCESS TOKEN: ' + response.data.access);
      }
      window.localStorage.setItem(ACCESS_TOKEN, response.data.access);
      return response.data;
    }).catch((error) => {
      throw error;
    });
};

const logoutUser = () => {
  window.localStorage.removeItem(ACCESS_TOKEN);
};

const errorInterceptor = (error) => {
  if (error.response === undefined) {
    throw new Error("Connection to the server failed");
  }
  if (error.response.status === 401) {
    if (store.state.auth.isLoggedIn) {
      store.dispatch('auth/logout');
      Vue.toasted.error('Session expired, please login again');
    } else {
      Vue.toasted.error('Please login to view this page');
    }
    if (router.currentRoute.name !== 'blocks') {
      router.push({ name: 'blocks', params: { blockchain: store.state.blockchain.selectedBlockchain.slug} });
      store.dispatch('blockchain/loadBlocks')
    }
  }
  throw error;
};

api.interceptors.response.use(
  (response) => response, // default
  (error) => errorInterceptor(error),
);
api.interceptors.request.use(
  (config) => {
    const jwt = window.localStorage.getItem(ACCESS_TOKEN);
    if (jwt) {
      // verify that jwt hasn't expired
      const decodedJWT = decodeJWT(jwt)
      if (Date.now() >= decodedJWT.exp * 1000) {
        store.dispatch('auth/logout');
        return config
      }
      config.headers['Authorization'] = `Bearer ${jwt}`;
    }
    return config;
  });

export {
  BACKEND_URL,
  ACCESS_TOKEN,
  API_TIMEOUT,
  api,
  loginUser,
  logoutUser,
  errorInterceptor, 
};
