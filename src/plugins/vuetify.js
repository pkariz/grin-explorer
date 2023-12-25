import Vue from 'vue';
import Vuetify from 'vuetify/lib/framework';

Vue.use(Vuetify);

export default new Vuetify({
  icons: {
    iconfont: 'mdi',
  },
  theme: {
    themes: {
      dark: {
        primary: '#e5dd00',
        accent: '#e5dd00',
        background: '#1b1b16',
      },
    },
    dark: true,
  },
});
