<template>
  <v-app :style="{background: $vuetify.theme.themes[theme].background}">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <template v-if="loading.initial">
      <v-progress-linear
        indeterminate
        color="primary"
      ></v-progress-linear>
    </template>
    <template v-else>
      <v-container
        class="d-flex justify-center align-center"
        :style="'max-width: ' + containerWidth"
      >
        <v-row class="d-flex justify-center align-center">
          <v-col
            class="d-flex align-center col-3 col-sm-1 col-md-2 flex-shrink-1 px-2"
            :style="$vuetify.breakpoint.smAndUp ? '' : 'max-width: 64px'"
          >
            <v-img
              alt="Grin Logo"
              contain
              src="https://raw.githubusercontent.com/grincc/hub/b6f99f652d1310dd44d3b1772cf4dfb1bbd18419/marketing/Logo/grin-logo.svg"
              transition="scale-transition"
              width="40"
              height="40"
              @click="routeToWrapper('blocks', { blockchain: blockchain.slug })"
              style="cursor: pointer;"
              class="pr-0"
            />
            <v-btn
              text
              class="no-active"
              v-if="$vuetify.breakpoint.mdAndUp"
              @click="tabs.find((el) => el.text === 'Blocks').clickHandler()"
            >
              Explorer
            </v-btn>
          </v-col>
          <v-col class="col-12 col-sm-5 order-10 order-sm-2 flex-grow-1" style="max-width: 90%">
            <v-text-field
              v-model="innerSearch"
              ref="searchInput"
              solo
              dense
              outlined
              hide-details="auto"
              label="Enter search term"
              @keyup.enter="performSearchWrapper();"
              :disabled="!blockchain"
            >
              <template v-slot:append>
                <v-icon
                  v-if="innerSearch"
                  color="primary"
                  class="mr-2"
                  @click="innerSearch='';"
                >mdi-close</v-icon>
                <v-icon
                  color="primary"
                  class="mr-2"
                  small
                  @click="showSearchHelpDialog = true"
                >mdi-help</v-icon>
                <v-icon color="primary">mdi-magnify</v-icon>
              </template>
            </v-text-field>
          </v-col>
          <v-col class="col-7 col-sm-4 col-md-3 order-3 order-sm-3 px-0" style="max-width: 300px">
            <v-select class="py-2"
              v-model="blockchain"
              :items="blockchains() || []"
              :loading="blockchains() === null"
              label="Blockchain"
              item-text="name"
              return-object
              hide-details="auto"
              solo
              dense
              outlined
              @change="onBlockchainChange(false)"
            >
              <template v-slot:prepend-inner>
                <v-icon color="primary">mdi-vector-link</v-icon>
              </template>
            </v-select>
          </v-col>
          <v-col class="col-1 order-4 order-sm-5 flex-shrink-1 pr-1" style="min-width: 50px">
            <v-menu
              left
              bottom
            >
              <template v-slot:activator="{ on, attrs }">
                <v-btn
                  icon
                  v-bind="attrs"
                  v-on="on"
                  color="primary"
                >
                  <v-icon>mdi-dots-vertical</v-icon>
                </v-btn>
              </template>

              <v-list
                subheader
                two-line
              >
                <v-subheader inset>Admin</v-subheader>

                <v-list-item
                  v-for="adminMenuItem in adminMenuItems"
                  :key="adminMenuItem.title"
                  @click="adminMenuItem.clickHandler"
                >
                  <v-list-item-avatar>
                    <v-icon
                      dark
                      :color="adminMenuItem.iconColor"
                    >
                      {{ adminMenuItem.icon }}
                    </v-icon>
                  </v-list-item-avatar>

                  <v-list-item-content>
                    <v-list-item-title v-text="adminMenuItem.title"></v-list-item-title>
                    <v-list-item-subtitle
                      v-text="adminMenuItem.subtitle"
                      v-if="adminMenuItem.subtitle">
                    </v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
              </v-list>
            </v-menu>
          </v-col>
          <v-col class="col-12 col-sm-4 order-11 order-sm-6 px-sm-3 pt-1 pb-0 elevation-0" :style="{
            'padding-right': $vuetify.breakpoint.smAndUp ? '0px !important': undefined,
          }">
            <v-card height="80px" class="latest-block" :style="{
              'border-right': $vuetify.breakpoint.smAndUp ? '1px solid #494a48 !important' : '0px !important',
              }">
              <v-card-title
                style="text-transform: uppercase; font-size: 1rem; font-weight: 400;"
                :class="{
                  'pt-1 pb-4': true,
                  'text-subtitle-1': $vuetify.breakpoint.smAndDown
                }"
              >
                Latest block
              </v-card-title>
              <v-card-text class="text-center">
                <v-progress-linear
                  color="primary"
                  indeterminate
                  v-if="latestBlock() === undefined"
                ></v-progress-linear>
                <v-row v-else class="align-center justify-center">
                  <h2>{{ latestBlock() ? latestBlock().height.toLocaleString() : '/' }}</h2>
                  <v-icon v-if="latestBlock()" color="primary" class="pl-2">mdi-cube-send</v-icon>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col class="col-12 col-sm-4 order-11 order-sm-6 px-sm-3 pt-1 pb-0" :style="{
            'padding-left': $vuetify.breakpoint.smAndUp ? '0px !important' : undefined,
            'padding-right': $vuetify.breakpoint.smAndUp ? '0px !important' : undefined,
          }">
            <v-card height="80px" class="supply" :style="{
              'border-right': $vuetify.breakpoint.smAndUp ? '1px solid #494a48 !important' : '0px !important',
            }">
              <v-card-title
                style="text-transform: uppercase; font-size: 1rem; font-weight: 400;"
                :class="{
                  'pt-1 pb-4': true,
                  'text-subtitle-1': $vuetify.breakpoint.smAndDown
                }"
              >
                Circulating supply
              </v-card-title>
              <v-card-text class="text-center">
                <v-progress-linear
                  color="primary"
                  indeterminate
                  v-if="latestBlock() === undefined"
                ></v-progress-linear>
                <v-row v-else class="align-center justify-center">
                  <h2>
                    <template v-if="latestBlock()">
                      {{ ((latestBlock().height + 1) * 60).toLocaleString() }}
                      <span class="primary--text">ツ</span>
                    </template>
                    <template v-else>
                      /
                    </template>
                  </h2>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col
            class="col-12 col-sm-4 order-11 order-sm-6 px-5 px-sm-3 pt-1 pb-0"
            :style="{'padding-left': $vuetify.breakpoint.smAndUp ? '0px !important': undefined }"
          >
            <v-card height="80px" class="price">
              <v-card-title
                style="text-transform: uppercase; font-size: 1rem; font-weight: 400;"
                :class="{
                  'pt-1 pb-4': true,
                  'text-subtitle-1': $vuetify.breakpoint.smAndDown
                }"
              >
                Grin price
              </v-card-title>
              <v-card-text class="text-center">
                <v-progress-linear
                  color="primary"
                  indeterminate
                  v-if="priceData() === undefined"
                ></v-progress-linear>
                <template v-else>
                  <v-row class="align-center justify-center">
                    <h2 v-if="selectedBlockchain() === null || priceData() === null || priceData()[selectedBlockchain().slug] == null">/</h2>
                    <template v-else>
                      <h2>
                        {{ priceData()[selectedBlockchain().slug].btc_value }}
                      </h2>
                      <v-icon color="orange">mdi-currency-btc</v-icon>
                      <v-icon
                        class="pl-1"
                        :color="Number(priceData()[selectedBlockchain().slug].percent_change >= 0) ? 'green' : 'red'"
                      >
                        mdi-chevron-{{ Number(priceData()[selectedBlockchain().slug].percent_change >= 0) ? 'up' : 'down' }}
                      </v-icon>
                      <span :class="Number(priceData()[selectedBlockchain().slug].percent_change >= 0) ? 'green--text' : 'red--text'">
                        <h3>{{ priceData()[selectedBlockchain().slug].percent_change }}%</h3>
                      </span>
                    </template>
                  </v-row>
                </template>
              </v-card-text>
            </v-card>
          </v-col>
          <!-- tabs -->
          <v-col class="col-12 order-12 order-sm-7 pt-2 pb-1" style="max-width: 100%">
            <v-toolbar class="main-toolbar px-5 pt-2border-bottom: thin solid rgba(255, 255, 255, 0.12)">
              <v-tabs v-model="activeTab" centered fixed-tabs>
                <v-tab
                  v-for="tab in shownTabs"
                  :key="tab.text"
                  @click="tab.clickHandler()"
                  :disabled="tab.disabled ? tab.disabled() : false"
                >
                  <v-icon
                    class="mr-2"
                    color="primary"
                    dark
                  >{{ tab.icon }}</v-icon>
                  <span v-if="$vuetify.breakpoint.smAndUp" style="font-size: 1.25rem;">{{ tab.text }}</span>
                </v-tab>
              </v-tabs>
            </v-toolbar>
          </v-col>
        </v-row>
      </v-container>
      <v-main>
        <v-container
          class="d-flex justify-center align-center pb-0"
          :style="'min-height: 765px; max-width: ' + containerWidth"
        >
          <router-view :key="$route.fullPath + customViewKey"/>
          <login-dialog
            :dialog="dialogLogin"
            :key="loginDialogKey"
            @close="dialogLogin=false; loginDialogKey += 1"
            @success="onLoginSuccess"
          ></login-dialog>
          <search-help-dialog
            :dialog="showSearchHelpDialog"
            @close="showSearchHelpDialog = false"
          ></search-help-dialog>
        </v-container>
      </v-main>
      <v-container
        class="d-flex justify-center align-center"
        :style="'max-width: ' + containerWidth"
      >
        <v-row class="d-flex justify-center align-center">
          <v-col cols="12">
            <v-footer
              style="background-color: inherit; margin: auto;"
              dark
              padless
              class="pt-5"
            >
              <v-card
                flat
                tile
                class="lighten-1 white--text text-center"
                style="width: 100%; border: 0px"
              >
                <v-divider></v-divider>
                <v-card-text class="white--text">
                  <v-tooltip
                    v-for="icon in footerIcons"
                    :key="icon.name"
                    top
                  >
                    <template v-slot:activator="{ on, attrs }">
                      <v-btn
                        v-on="on"
                        v-bind="attrs"
                        class="mx-3 white--text"
                        icon
                        @click="openInNewTab(icon.url)"
                      >
                        <v-icon size="24px">
                          {{ icon.name }}
                        </v-icon>
                      </v-btn>
                    </template>
                    <span>{{ icon.description }}</span>
                  </v-tooltip>
                </v-card-text>
              </v-card>
            </v-footer>
          </v-col>
          </v-row>
    </v-container>
    </template>
  </v-app>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import { ACCESS_TOKEN } from '@/services/auth'
import { decodeJWT, getWebSocket, routeTo } from '@/shared/helpers';
import LoginDialog from './components/LoginDialog'
import SearchHelpDialog from './components/SearchHelpDialog'
import { get as _get } from 'lodash';
import '@fortawesome/fontawesome-free/css/fontawesome.min.css'



export default {
  name: 'App',
  components: {
    'login-dialog': LoginDialog,
    'search-help-dialog': SearchHelpDialog,
  },
  data() {
    return {
      innerSearch: null,
      customViewKey: 1,
      loading: { initial: true },
      containerWidth: '100%',
      dialogLogin: false,
      showSearchHelpDialog: false,
      loginDialogKey: 1,
      footerIcons: [
        { name: 'mdi-web', url: 'https://grin.mw/', description: 'website' },
        { name: 'mdi-forum', url: 'https://forum.grin.mw/', description: 'forum' },
        { name: 'fa-brands fa-keybase', url: 'https://keybase.io/team/grincoin', description: 'keybase' },
        { name: 'mdi-github', url: 'https://github.com/mimblewimble/grin', description: 'github' },
      ],
      // if you change tabs here change the order also in the vuex so that
      // routing will set the right activeTab index
      tabs: [
        {
          text: 'Blocks',
          icon: 'mdi-cube',
          clickHandler: () => {
            if (this.$router.currentRoute.name === 'blocks') {
              return
            }
            this.setPage(1)
            this.setSearch('')
            this.setLatestSearch(null)
            this.innerSearch = null
            this.routeToWrapper('blocks', {
              blockchain: this.selectedBlockchain() ? this.selectedBlockchain().slug : '',
            })
          },
          show: () => true,
        },
        {
          text: 'Graphs',
          icon: 'mdi-chart-line',
          clickHandler: () => {
            this.setSearch('')
            this.setLatestSearch(null)
            this.innerSearch = null
            this.routeToWrapper('graphs', {
              blockchain: this.selectedBlockchain() ? this.selectedBlockchain().slug : '',
            })
          },
          show: () => true,
          disabled: () => !this.selectedBlockchain(),
        },
        {
          text: 'Settings',
          icon: 'mdi-cog',
          clickHandler: () => {
            this.setSearch('')
            this.setLatestSearch(null)
            this.innerSearch = null
            this.routeToWrapper('settings')
          },
          show: () => this.isLoggedIn(),
        },
      ]
    }
  },
  watch: {
    // watcher so that when you set 'innerSearch' value to empty (either through
    // deleting characters or clicking search's 'close' btn) it refetches blocks
    innerSearch: {
      handler (newValue, oldValue) {
        if (oldValue && newValue === '' && this.latestSearch()) {
          this.performSearchWrapper()
        }
      },
    },
  },
  created: async function() {
    this.innerSearch = this.search()
    this.makeWebSocketConnection()
    this.logoutIfNeeded()
    this.containerWidth = this.getContainerWidth()
    this.loading.initial = true
    // NOTE: we only set active tab here, the clickHandler will be called after
    // the blockchains are fetched and the default one is automatically selected
    this.setActiveTab(this.tabs
      .map((tab) => tab.text)
      .indexOf(_get(this.$route, 'meta.tab', 'Blocks'))
    )
    try {
      const data = await this.getBlockchains();
      // at the start randomly select one blockchain, could use vuex/default
      // or smth similar in the future
      if (data.results.length > 0) {
        if (this.$route.params.blockchain) {
          // select the one in the url
          this.blockchain = data.results.filter(
            (bc) => bc.slug === this.$route.params.blockchain)[0]
        } else {
          // select the default one, if multiple blockchains have 'default' set
          // to true then pick the first one
          try {
            const defaultBlockchains = data.results.filter((bc) => bc.default)
            if (defaultBlockchains.length === 0) {
              throw 'No default blockchain'
            }
            this.blockchain = defaultBlockchains[0]
          } catch {
            // there is no default chain, pick the first one
            this.blockchain = data.results[0]
            this.$toasted.info('Please set one blockchain as default in settings')
          }
        }
        this.onBlockchainChange(true)
      } else {
        this.setLatestBlock(null)
      }
    } catch(error) {
      this.$toasted.error('Failed to fetch blockchains');
    }
    this.loading.initial = false
  },
  beforeDestroy: function() {
    this.connection.close();
  },
  computed: {
    blockchain: {
      get () {
        return this.$store.getters['blockchain/selectedBlockchain']
      },
      set (value) {
        this.$store.commit('blockchain/setSelectedBlockchain', value)
      }
    },
    shownTabs() {
      return this.tabs.filter((tab) => tab.show())
    },
    activeTab: {
      get () {
        return this.$store.getters['blockchain/activeTab']
      },
      set (value) {
        this.$store.commit('blockchain/setActiveTab', value)
      }
    },
    theme() {
      return (this.$vuetify.theme.dark) ? 'dark' : 'light'
    },
    adminMenuItems() {
      const items = [];
      if (this.isLoggedIn()) {
        items.push({
          color: 'blue',
          icon: 'mdi-logout',
          iconColor: 'green',
          title: 'Logout',
          clickHandler: this.performLogout,
        })
      } else {
        items.push({
          color: 'blue',
          icon: 'mdi-login',
          iconColor: 'green',
          title: 'Login',
          clickHandler: this.showLoginDialog,
        })
      }
      return items;
    },
  },
  methods: {
    ...mapGetters({
      blockchains: 'blockchain/blockchains',
      isLoggedIn: 'auth/isLoggedIn',
      selectedBlockchain: 'blockchain/selectedBlockchain',
      blocks: 'blockchain/blocks',
      totalBlocks: 'blockchain/totalBlocks',
      search: 'blockchain/search',
      latestSearch: 'blockchain/latestSearch',
      latestBlock: 'blockchain/latestBlock',
      page: 'blockchain/page',
      itemsPerPage: 'blockchain/itemsPerPage',
      priceData: 'blockchain/priceData',
    }),
    ...mapActions({
      getBlockchains: 'blockchain/getBlockchains',
      setBlocks: 'blockchain/setBlocks',
      loadBlocks: 'blockchain/loadBlocks',
      changeBlockchain: 'blockchain/changeBlockchain',
      performSearch: 'blockchain/performSearch',
      setSearch: 'blockchain/setSearch',
      setLatestSearch: 'blockchain/setLatestSearch',
      setLatestBlock: 'blockchain/setLatestBlock',
      setTotalBlocks: 'blockchain/setTotalBlocks',
      setPriceData: 'blockchain/setPriceData',
      setActiveTab: 'blockchain/setActiveTab',
      setPage: 'blockchain/setPage',
      logout: 'auth/logout',
    }),
    makeWebSocketConnection: function() {
      this.connection = getWebSocket()
      this.connection.onmessage = (e) => {
        let data = JSON.parse(e.data)
        // we only show new blocks on the first page
        if (
          data.type == 'new_block' &&
          this.selectedBlockchain() != null &&
          this.selectedBlockchain().slug === data.message.blockchain.slug
        ) {
          const block = data['message']
          block.timestamp = (new Date(block.timestamp)).toUTCString()
          this.setLatestBlock(block)
          // we don't show new blocks if we are currently showing search results
          // or are on another page or on a route which is not 'blocks'
          if (
            this.$router.currentRoute.name !== 'blocks' ||
            this.search() ||
            this.page() !== 1
          ) {
            return
          }
          const newBlocks = [...this.blocks()]
          // if the blockchain has not been bootstrapped yet, it might not have
          // enough blocks shown on the block-list page, so only pop if needed
          if (newBlocks.length >= this.itemsPerPage()) {
            newBlocks.pop()
          }
          newBlocks.unshift(block);
          this.setBlocks(newBlocks)
          this.setTotalBlocks(this.totalBlocks() + 1)
          // set animation in setTimeout so that data-table has time to update
          setTimeout(() => {
            const el = document.querySelector("tbody>tr:first-of-type")
            if (el != null) {
              el.classList.add('newblock')
            }
          }, 0)
        } else if (data.type === 'reorged') {
          this.$toasted.info(`Reorg spotted on chain ${data.message}!`)
          if (
            data.message === this.selectedBlockchain().slug &&
            !this.search() &&
            this.$router.currentRoute.name === 'blocks' &&
            this.page() === 1
          ) {
            // need to update blocks
            this.getBlocks()
          }
        } else if (data.type === 'price_update') {
          this.setPriceData(data.message)
        }
      }
    },
    logoutIfNeeded: function() {
      if (this.isLoggedIn()) {
        const jwt = window.localStorage.getItem(ACCESS_TOKEN)
        if (!jwt) {
          this.performLogout()
        }
        try {
          const decodedJWT = decodeJWT(jwt)
          if (Date.now() >= decodedJWT.exp * 1000) {
            throw 'jwt expired'
          }
        } catch {
          this.performLogout()
        }
      }
    },
    getContainerWidth: function() {
      if (this.$vuetify.breakpoint.xsOnly) {
        return '100%'
      }
      if (this.$vuetify.breakpoint.mdAndUp) {
        return '1200px'
      }
      return '80%'
    },
    onBlockchainChange: function(initial) {
      this.changeBlockchain(this.blockchain)
      // on initial load we don't want to redirect otherwise if the user goes on
      // block-detail url he will be redirected to block-list which is not what
      // we want
      if (!initial) {
        this.setPage(1)
        this.setSearch('')
        this.innerSearch = null
        this.routeToWrapper('blocks', {
          blockchain: this.selectedBlockchain() ? this.selectedBlockchain().slug : '',
        })
      }
    },
    routeToWrapper: function(routeName, params = {}) {
      return routeTo(routeName, params)
    },
    performSearchWrapper: function() {
      this.$refs.searchInput.blur()
      if (!this.selectedBlockchain()) {
        return
      }
      this.setSearch(this.innerSearch)
      this.setActiveTab(0)
      const curPage = this.page()
      this.setPage(1)
      if (this.$router.currentRoute.name !== 'blocks') {
        this.routeToWrapper('blocks', {
          blockchain: this.selectedBlockchain() ? this.selectedBlockchain().slug : '',
        })
      } else if (curPage === 1) {
        // if curPage !== 1 and we're on 'blocks' page we have 'page' watcher,
        // which means that loadblocks gets triggered by this.setPage(1), so we
        // shouldn't trigger it again
        this.loadBlocks()
      }
    },
    onLoginSuccess: function() {
      this.dialogLogin = false;
      this.loginDialogKey += 1;
    },
    performLogout: function() {
      this.logout().then(() => {
        this.routeToWrapper('blocks');
      });
    },
    showLoginDialog: function() {
      this.dialogLogin = true;
    },
    openInNewTab: function(url) {
      window.open(url, '_blank', 'noreferrer');
    },
  },
};
</script>
<style>
.price {
  border: 0px !important;
  border-bottom: 1px solid !important;
  border-color: #494a48 !important;
  border-radius: 0px 4px 0px 0px !important;
  box-shadow: none !important;
}
.supply {
  border: 0px !important;
  border-right: 1px solid !important;
  border-bottom: 1px solid !important;
  border-color: #494a48 !important;
  border-radius: 0px !important;
  box-shadow: none !important;
}
.latest-block {
  border: 0px !important;
  border-bottom: 1px solid !important;
  border-color: #494a48 !important;
  border-radius: 4px 0px 0px 0px !important;
  box-shadow: none !important;
}
.v-btn--active.no-active::before {
  opacity: 0 !important;
}
.v-toolbar__content > .v-tabs, .v-toolbar__extension > .v-tabs {
  height: 40px !important;
}
.main-toolbar > .v-toolbar__content {
  padding-top: 0px;
}
.main-toolbar {
  border-radius: 5px !important;
  background-color: #1b1b16 !important;
  box-shadow: none !important;
}
/* table background */
.theme--dark.v-data-table {
  background-color: #1b1b16 !important;
}
/* table row hover background */
.theme--dark.v-data-table > .v-data-table__wrapper > table > tbody > tr:hover:not(.v-data-table__expanded__content):not(.v-data-table__empty-wrapper) {
  background: #323232 !important;
}

.theme--dark .v-card {
  border: 5px ridge #8d8c8c32;
  background-color: #1b1b16 !important;
}


</style>
