import { get as _get } from 'lodash';
import router from '@/router'


export function copyToClipboard(str) {
  const el = document.createElement('textarea');
  el.addEventListener('focusin', e => e.stopPropagation());
  el.value = str;
  document.body.appendChild(el);
  el.select();
  document.execCommand('copy');
  document.body.removeChild(el);
}


export function getWebSocket(authenticated=false) {
    const BACKEND_URL = String(process.env.VUE_APP_BACKEND_URL)
    const domain = BACKEND_URL.split('/').filter((x) => x !== '')[1]
    let url = `ws://${domain}/ws/socket-server/`
    if (authenticated) {
      url += 'admin/'
    }
    return new WebSocket(url)
}


export function getErrorMsg(error) {
  const responseData = _get(error, 'response.data', {});
  let messages = [];
  if (Array.isArray(responseData)) {
    // DRF's ValidationError returns list of messages in data
    messages = responseData;
  } else {
    // some DRF exceptions return an object in form key: msg[]
    for (const [key, msgArray] of Object.entries(responseData)) {
      messages.push(`${key}:`);
      messages = messages.concat(msgArray.map((msg) => `&nbsp;&nbsp;- ${msg}`));
    }
  }
  if (messages.length === 0) {
    const statusCode = _get(error, 'response.status', null)
    const statusText = _get(error, 'response.status', null)
    if (statusCode) {
      messages.push(`(${statusCode}) ${statusText}`)
    } else {
      messages.push('Unknown error')
    }
  }
  return messages.join('<br>');
}


export function decodeJWT(token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
}


export function routeTo(routeName, params = {}) {
  const currentRouteFullPath = router.resolve({
    name: router.currentRoute.name,
    params: router.currentRoute.params
  }).resolved.fullPath
  const newRouteFullPath = router.resolve({
    name: routeName,
    params: params
  }).resolved.fullPath
  if (newRouteFullPath !== currentRouteFullPath) {
    router.push({ name: routeName, params: params });
  }
}


export function getDateRepr(date) {
  const splitted = date.toUTCString().split(' ')
  return `${splitted[2]} ${splitted[1]}`
}
