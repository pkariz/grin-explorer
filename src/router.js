import Vue from 'vue'
import Router from 'vue-router'
import Blocks from '@/views/Blocks.vue'
import Block from '@/views/Block.vue'
import Settings from '@/views/Settings.vue'
import Graphs from '@/views/Graphs.vue'
import store from './store/index';

Vue.use(Router)

const router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/:blockchain/blocks/:blockHash',
      name: 'block',
      component: Block,
      props: route => ({
        blockchain: route.params.blockchain,
        blockHash: route.params.blockHash,
      }),
      meta: { tab: 'Blocks' },
    },
    {
      path: '/:blockchain/blocks',
      name: 'blocks',
      component: Blocks,
      props: route => ({ blockchain: route.params.blockchain }),
      meta: { tab: 'Blocks' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings,
      meta: { requiresAuth: true, tab: 'Settings' },
    },
    {
      path: '/:blockchain/graphs',
      name: 'graphs',
      component: Graphs,
      props: route => ({ blockchain: route.params.blockchain }),
      meta: { tab: 'Graphs' },
    },
    {
      path: '*',
      redirect: () => {
        const selectedBlockchain = store.getters['blockchain/selectedBlockchain'];
        return {
          name: 'blocks',
          params: {
            blockchain: selectedBlockchain ? selectedBlockchain.slug : '',
          },
        }
      },
    },
  ],
});

// handle require_auth meta property on routes
router.beforeEach((to, from, next) => {
  // set activeTab
  const match = to.matched.find((record) => record.meta.tab)
  if (match) {
    const idx = store.state.blockchain.tabOrder.indexOf(match.meta.tab)
    if (idx !== -1) {
      store.dispatch('blockchain/setActiveTab', idx)
    }
  }
  // require auth on some routes
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (store.getters['auth/isLoggedIn']) {
      next();
      return;
    }
    Vue.toasted.error('Session expired, please login again');
    next({ name: 'blocks' });
  } else {
    next();
  }
});

export default router;
