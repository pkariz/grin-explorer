import Vue from 'vue';
import blockchainService from '../../services/blockchain'
import blockService from '../../services/block'
import { routeTo } from '@/shared/helpers'
import { get as _get } from 'lodash';

const state = {
  blockchains: null,
  selectedBlockchain: null,
  // we keep blocks data here so that we can change block-list table easier
  // when we use the search functionality (eg. when we search 'reorgs')
  blocks: [],
  totalBlocks: 0,
  latestBlock: undefined,
  search: null,
  // latestSearch contains string that was last searched for if you're on
  // block-list page. If the last block fetch was a regular one without the
  // search value or if you're not on block-list page then the value is null
  latestSearch: null,
  // page of block-list data table
  page: 1,
  // itemsPerPage is here so that it's persisted when you move to another page
  // eg. graphs
  itemsPerPage: 10,
  // currently active tab in app.vue
  activeTab: 0,
  tabOrder: ['Blocks', 'Graphs', 'Settings'],
  // price data is in format:
  // {
  //   <blockchain.slug>: {
  //     btc_value: null,
  //     percent_change: null,
  //   },
  //   ...
  // }
  priceData: undefined,
  loading: { blocks: false },
  logos: {
    'grin': 'https://aws1.discourse-cdn.com/standard10/uploads/grin/original/1X/f96e1cdce64456785297c317e6cb84f3fab2edcb.svg',
  },
}

const getters = {
  blockchains: state => {
    return state.blockchains
  },
  selectedBlockchain: state => {
    return state.selectedBlockchain
  },
  blocks: state => {
    return state.blocks
  },
  totalBlocks: state => {
    return state.totalBlocks
  },
  loading: state => {
    return state.loading
  },
  page: state => {
    return state.page
  },
  itemsPerPage: state => {
    return state.itemsPerPage
  },
  search: state => {
    return state.search
  },
  latestSearch: state => {
    return state.latestSearch
  },
  latestBlock: state => {
    return state.latestBlock
  },
  priceData: state => {
    return state.priceData
  },
  activeTab: state => {
    return state.activeTab
  },
}

const actions = {
  getBlockchains({ commit }) {
    return blockchainService.fetchBlockchains()
      .then(blockchains => {
        commit('setBlockchains', blockchains.results)
        return blockchains
      })
  },
  changeBlockchain({ commit, dispatch }, blockchain) {
    commit('setSelectedBlockchain', blockchain)
    commit('setPage', 1)
    commit('setSearch', '')
    commit('setLatestBlock', null)
    dispatch('resetBlocks')
    // getBlocks until we fetch only 'latest block'
    dispatch('getBlocks')
  },
  loadBlocks({ state, dispatch }) {
    if (!state.selectedBlockchain) {
      Vue.toasted.error("Can't get blocks - no blockchain selected");
      return
    }
    if (state.search !== '') {
      dispatch('performSearch')
    } else {
      dispatch('getBlocks')
    }
  },
  getBlocks({ commit, state }) {
    commit('setLoading', { attr: 'blocks', val: true })
    return blockService.fetchBlocks(state.selectedBlockchain.slug, state.page, state.itemsPerPage)
      .then(blocks => {
        commit('setLatestSearch', null)
        for (const block of blocks.results) {
          block.timestamp = new Date(block.timestamp)
        }
        commit('setBlocks', blocks.results)
        commit('setTotalBlocks', blocks.count)
        if (state.page === 1) {
          commit('setLatestBlock', blocks.results.length > 0 ? blocks.results[0] : null)
        }
        return blocks
      })
      .finally(() => {
        commit('setLoading', { attr: 'blocks', val: false })
      })
  },
  performSearch({ commit, state }) {
    routeTo('blocks', { blockchain: state.selectedBlockchain.slug })
    commit('setLoading', { attr: 'blocks', val: true })
    blockService.searchBlocks(
      state.selectedBlockchain.slug,
      state.search,
      state.page,
      state.itemsPerPage
    )
      .then((responseData) => {
        commit('setLatestSearch', state.search)
        const specialKeywords = ['reorgs', 'inputs', 'outputs', 'kernels']
        const searchIncludesSpecialKeyword = specialKeywords
          .filter((x) => state.search.split(' ').includes(x))
          .length > 0
        if (responseData.results.length === 0) {
          Vue.toasted.error("Search didn't match any blocks")
          commit('setBlocks', [])
          commit('setTotalBlocks', responseData.count)
        } else if (searchIncludesSpecialKeyword) {
          // got blocks where reorgs started or those that match the search
          // formula, pass that to the blocks component set timestamp as you do
          // in the store getBlocks
          for (const block of responseData.results) {
            block.timestamp = (new Date(block.timestamp)).toUTCString()
          }
          commit('setBlocks', responseData.results)
          commit('setTotalBlocks', responseData.count)
          routeTo('blocks', { blockchain: state.selectedBlockchain.slug })
        } else {
          // we should have only 1 block here
          routeTo(
            'block',
            {
              blockchain: state.selectedBlockchain.slug,
              blockHash: responseData.results[0].hash,
            }
          )
        }
      })
      .catch((error) => {
        const errMsg = _get(error, 'response.data.detail', 'Error matching searched term')
        commit('setBlocks', [])
        commit('setTotalBlocks', 0)
        routeTo('blocks', { blockchain: state.selectedBlockchain.slug })
        Vue.toasted.error(errMsg);
      })
      .finally(() => {
        commit('setLoading', { attr: 'blocks', val: false })
      })
  },
  setBlocks({ commit }, blocks) {
    commit('setBlocks', blocks)
  },
  setTotalBlocks({ commit }, totalBlocks) {
    commit('setTotalBlocks', totalBlocks)
  },
  setPage({ commit }, page) {
    commit('setPage', page)
  },
  setItemsPerPage({ commit }, itemsPerPage) {
    commit('setItemsPerPage', itemsPerPage)
  },
  setSearch({ commit }, search) {
    commit('setSearch', search)
  },
  setLatestSearch({ commit }, val) {
    commit('setLatestSearch', val)
  },
  setLoading({ commit }, { attr, val }) {
    commit('setLoading', attr, val)
  },
  resetBlocks({ commit }) {
    commit('setBlocks', [])
    commit('setTotalBlocks', 0)
  },
  setLatestBlock({ commit }, block) {
    commit('setLatestBlock', block)
  },
  setPriceData({ commit }, priceData) {
    commit('setPriceData', priceData)
  },
  setActiveTab({ commit }, activeTab) {
    commit('setActiveTab', activeTab)
  },
  resetSelectedBlockchain({ commit }) {
    commit('setSelectedBlockchain', null)
    commit('setLatestBlock', null)
    commit('setPriceData', null)
  },
}

const mutations = {
  setBlockchains(state, blockchains) {
    state.blockchains = blockchains
  },
  setSelectedBlockchain(state, blockchain) {
    state.selectedBlockchain = blockchain
    // reset data
    state.blocks = []
    state.totalBlocks = 0
    state.latestBlock = undefined
  },
  setBlocks(state, blocks) {
    state.blocks = blocks
  },
  setTotalBlocks(state, totalBlocks) {
    state.totalBlocks = totalBlocks
  },
  setPage(state, page) {
    state.page = page
  },
  setItemsPerPage(state, itemsPerPage) {
    state.itemsPerPage = itemsPerPage
  },
  setLoading(state, { attr, val }) {
    state.loading[attr] = val
  },
  setSearch(state, val) {
    state.search = val
  },
  setLatestSearch(state, search) {
    state.latestSearch = search
  },
  setLatestBlock(state, block) {
    state.latestBlock = block
  },
  setPriceData(state, val) {
    state.priceData = val
  },
  setActiveTab(state, val) {
    state.activeTab = val
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
