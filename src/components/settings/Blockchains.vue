<template>
  <v-container>
    <v-row>
    <template v-if="loading.initial">
      <v-progress-linear
        indeterminate
        color="primary"
      ></v-progress-linear>
    </template>
    <template v-else>
      <v-col cols="12" v-for="blockchain in blockchains" :key="blockchain.slug">
        <v-card>
          <v-card-text>
            <v-row>
            <v-col class="col-12 col-md-6">
              <v-row>
                <v-col class="col-12 col-sm-5">
                  <h2 class="primary-color">{{ blockchain.name }}</h2>
                </v-col>
                <v-col :class="{'col-12 col-sm-7': true, 'text-right': $vuetify.breakpoint.smAndUp}">
                  <v-btn
                    text
                    color="primary"
                    class="mr-2"
                    outlined
                    :disabled="blockchain.isDeleting"
                    @click="showAddOrEditBlockchainDialog(blockchain)"
                  >
                    <v-icon>mdi-pencil</v-icon>
                    &nbsp;Edit
                  </v-btn>
                  <v-btn
                    :class="{'mt-3': $vuetify.breakpoint.xsOnly}"
                    text
                    color="#e35449"
                    outlined
                    :disabled="blockchain.isDeleting"
                    :loading="loading.deletingBlockchain[blockchain.slug]"
                    @click="showConfirmDialog('blockchain-delete', blockchain)"
                  >
                    <v-icon>mdi-delete</v-icon>
                    &nbsp;delete
                  </v-btn>
                </v-col>
                </v-row>
              <v-list class="transparent pt-5">
                  <v-list-item class="px-0">
                    <v-list-item-title class="text-left" style="max-width: 80px">Node:</v-list-item-title>
                    <v-list-item-subtitle class="text-right">
                      {{ blockchain.node.name }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-divider></v-divider>
                  <v-list-item class="px-0">
                    <v-list-item-title class="text-left" style="max-width: 80px">URL:</v-list-item-title>
                    <v-list-item-subtitle class="text-right">
                      {{ blockchain.node.api_url }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-divider></v-divider>
                  <v-list-item class="px-0">
                    <v-list-item-title class="text-left" style="max-width: 80px">Archive:</v-list-item-title>
                    <v-list-item-subtitle class="text-right">
                      <v-icon color="yellow">
                        {{ blockchain.node.archive ? 'mdi-check': 'mdi-close' }}
                      </v-icon>
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-divider></v-divider>
                  <v-list-item class="px-0">
                    <v-list-item-title class="text-left" style="max-width: 80px">Default:</v-list-item-title>
                    <v-list-item-subtitle class="text-right">
                      <v-icon color="yellow">
                        {{ blockchain.default ? 'mdi-check': 'mdi-close' }}
                      </v-icon>
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item class="px-0">
                    <v-list-item-title class="text-left" style="max-width: 100px">Fetch price:</v-list-item-title>
                    <v-list-item-subtitle class="text-right">
                      <v-icon color="yellow">
                        {{ blockchain.fetch_price ? 'mdi-check': 'mdi-close' }}
                      </v-icon>
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-divider></v-divider>
                  <v-list-item class="px-0">
                    <v-list-item-title class="text-left" style="max-width: 80px">Reachable:</v-list-item-title>
                    <v-list-item-subtitle class="text-right">
                      <v-icon color="yellow">
                        <template v-if="loading.reachable[blockchain.node.slug]">
                          mdi-sync mdi-spin
                        </template>
                        <template v-else>
                          {{ reachable[blockchain.node.slug] ? 'mdi-check': 'mdi-close' }}
                        </template>
                      </v-icon>
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-divider></v-divider>
              </v-list>
              <v-btn
                color="primary"
                class="mt-3"
                outlined
                @click="bootstrapBlockchain(blockchain)"
                :loading="loading.bootstrap"
                :disabled="blockchain.isBootstraping || blockchain.isDeleting"
              >
                <v-icon>{{ blockchain.isBootstraping ? 'mdi-sync mdi-spin' : 'mdi-sync' }}</v-icon>
                &nbsp;&nbsp;Bootstrap
              </v-btn>
              <v-btn
                v-if="blockchain.isBootstraping"
                color="error"
                class="mt-3 ml-2"
                outlined
                @click="abortBootstrap(blockchain)"
                :loading="loading.abort"
              >
                <v-icon>mdi-close</v-icon>
                &nbsp;&nbsp;Abort
              </v-btn>
            </v-col>
            <v-col class="col-12 col-md-6">
              <!-- we set min-height otherwise the height is not consistent when
                   you are switching between different components and the graph
                   gets rerendered -->
              <div style="min-height: 250px; max-height: 350px; width: 100%" class="d-flex justify-center" v-if="charts[blockchain.slug]">
                <apexchart
                  style="
                    min-height: 300px;
                    max-height: 350px;
                    height: 100%;
                    min-width: 300px;
                    max-width: 350px;
                    width: 100%
                  "
                  :ref="`chart-${blockchain.slug}`"
                  type="donut"
                  :options="charts[blockchain.slug].chartOptions"
                  :series="charts[blockchain.slug].series"
                ></apexchart>
              </div>
              <v-col cols="12" class="text-center py-0">
                <template v-if="blockchain.isBootstraping">
                  Estimated time remaining: {{
                    countdown[blockchain.slug] ? countdown[blockchain.slug] : 'calculating...' }}
                </template>
                <template v-if="blockchain.isDeleting">
                  Deleting blockchain, might take some time.
                </template>
                <template v-else-if="blockchain.bootstrapInfo != null">
                  {{ blockchain.bootstrapInfo.text }}
                  <v-icon :color="blockchain.bootstrapInfo.iconColor" class="pb-3">
                    {{ blockchain.bootstrapInfo.icon }}
                  </v-icon>
                </template>
              </v-col>
            </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </template>
    </v-row>
    <br />
    <v-btn color="primary" class="mb-5" outlined @click="showAddOrEditBlockchainDialog(null)">
      Add blockchain
    </v-btn>
    <add-or-edit-blockchain-dialog
      :key="blockchainDialogKey"
      :dialog="addOrEditBlockchainDialog"
      :blockchain="addOrEditBlockchainDialogSelectedBlockchain"
      @close="closeAddOrEditBlockchainDialog(false)"
      @created="onBlockchainCreated($event)"
      @modified="closeAddOrEditBlockchainDialog(true)"
    ></add-or-edit-blockchain-dialog>
    <confirm-dialog
      v-if="confirmText"
      :dialog="confirmDialog"
      :text="confirmText"
      :loading="confirmLoading"
      :onsubmit="confirmAction"
      @close="closeConfirmDialog"
      @done="closeConfirmDialog(true)"
    ></confirm-dialog>
  </v-container>
</template>
<script>
import { createNamespacedHelpers } from 'vuex'
import AddOrEditBlockchainDialog from '@/components/AddOrEditBlockchainDialog'
import { getWebSocket, getErrorMsg } from '@/shared/helpers'
import blockchainAPI from '@/services/blockchain'
import nodeAPI from '@/services/node'
import ConfirmDialog from '@/components/ConfirmDialog'

const { mapActions, mapGetters } = createNamespacedHelpers('blockchain')

export default {
  name: 'Blockchains',
  components: {
    'add-or-edit-blockchain-dialog': AddOrEditBlockchainDialog,
    'confirm-dialog': ConfirmDialog,
  },
  data: () => ({
    loading: {
      initial: true,
      bootstrap: false,
      reachable: {},
      abort: false,
      deletingBlockchain: {},
    },
    reachable: {},
    addOrEditBlockchainDialogSelectedBlockchain: null,
    addOrEditBlockchainDialog: false,
    confirmDialog: false,
    confirmText: '',
    confirmLoading: false,
    // key to force dialog rerender
    blockchainDialogKey: 0,
    blockchains: [],
    charts: {},
    connection: null,
    // bootstrapTimes is of form: {
    //   <blockchain.slug>: [
    //     { curTimeMillisec: <t1>, loadProgress: <p1> },
    //     { curTimeMillisec: <t2>, loadProgress: <p2> },
    //   ]
    // }
    // where t1 and p1 are the first updates from the websocket, t2 and p2 are
    // the last ones. Array is cleared when bootstrap is initiated.
    bootstrapTimes: {},
    // countdown stores remaining time as string based on data in bootstrapTimes
    countdown: {},
  }),
  created: function() {
    this.connection = getWebSocket(true)
    this.connection.onerror = () => {
      if (this.readyState !== 3) {
        this.$toasted.error('websocket connection error, please refresh')
      }
    }
    this.connection.onmessage = (e) => {
      let data = JSON.parse(e.data)
      // we only show new blocks on the first page
      if (data.type === 'blockchain_deleted') {
        this.$toasted.success(`Blockchain ${data.message.slug} has been successfully deleted`)
        this.loading.deletingBlockchain[data.message.slug] = false;
        // remove blockchain from gui
        this.blockchains = this.blockchains.filter((bc) => bc.slug !== data.message.slug);
        // make sure it's removed from the blockchain-select input
        this.getBlockchains();
      } else if (data.type == 'blockchain_progress_changed') {
        const blockchainSlug = data['message']['slug']
        const load_progress = data['message']['load_progress']
        const bc = this.blockchains.find((bc) => bc.slug === blockchainSlug)
        this.updateBlockchainProgress(bc, load_progress)
      } else if (data.type == 'task_status_changed') {
        const updatedTask = data['message']
        if (updatedTask.content_object.model === 'blockchain') {
          const matchingBlockchain = this.blockchains.find(
            (bc) => bc.slug === updatedTask.content_object.data.slug)
          if (matchingBlockchain) {
            matchingBlockchain.bootstrapInfo = this.getBootstrapInfo(
              updatedTask.status, updatedTask.failure_reason)
            matchingBlockchain.isBootstraping = false;
          }
        }
      }
    }
    this.fetchBlockchains();
  },
  beforeDestroy: function() {
    this.connection.close();
  },
  methods: {
    ...mapGetters([
      'selectedBlockchain',
    ]),
    ...mapActions([
      'getBlockchains',
      'changeBlockchain',
      'resetSelectedBlockchain',
    ]),
    fetchNodeReachable: async function(nodeSlug) {
      this.loading.reachable[nodeSlug] = true
      try {
        const data = await nodeAPI.fetchReachable(nodeSlug)
        this.reachable[nodeSlug] = data
      } catch {
        this.$toasted.error('Failed to reach node: ' + nodeSlug);
      }
      this.loading.reachable[nodeSlug] = false
    },
    fetchBlockchains: async function() {
      this.loading.initial = true
      try {
        const data = await this.getBlockchains();
        for (const bc of data.results) {
          // set reachable vars to be reactive
          this.$set(this.reachable, bc.node.slug, false);
          this.$set(this.loading.reachable, bc.node.slug, false);
          // fetch node reachable
          this.fetchNodeReachable(bc.node.slug)
          // need to make object keys reactive through 'set'
          this.$set(this.countdown, bc.slug, null);
          this.$set(bc, 'bootstrapInfo', null);
          this.$set(
            bc,
            'isBootstraping',
            bc.tasks.some((task) =>
              task.type === 'bootstrap' && task.status === 'in_progress')
          );
          this.$set(
            bc,
            'isDeleting',
            bc.tasks.some((task) =>
              task.type === 'blockchain_delete' && task.status === 'in_progress')
          );
          this.$set(this.loading.deletingBlockchain, bc.slug, bc.isDeleting);
          // we don't need bootstrapTimes to be reactive
          this.resetBootstrapingData(bc)
          if (!bc.isBootstraping) {
            // set latest task info
            const curTasks = bc.tasks
              .filter((task) => task.type === 'bootstrap')
              .sort((a, b) => new Date(b.date) - new Date(a.date));
            let latestTask = null
            if (curTasks.length > 0) {
              latestTask = curTasks[curTasks.length - 1]
            }
            if (bc.load_progress === 100.0) {
              bc.bootstrapInfo = this.getBootstrapInfo('success', null)
            } else if (latestTask && latestTask.status === 'failure') {
              bc.bootstrapInfo = this.getBootstrapInfo(
                latestTask.status, latestTask.failure_reason)
            } else {
              bc.bootstrapInfo = null
            }
          }
          // we must not rerender the graphs which we've already rendered
          if (!this.charts[bc.slug]) {
            this.charts[bc.slug] = this.generateChart(bc)
          }
        }
        this.blockchains = data.results.sort((bc1, bc2) => bc1.name.localeCompare(bc2.name))
      } catch(error) {
        this.$toasted.error('Failed to fetch blockchains');
      }
      this.loading.initial = false
    },
    updateBlockchainProgress: function(blockchain, loadProgress) {
      blockchain.load_progress = loadProgress;
      const timerData = {
        curTimeMillisec: new Date().getTime(),
        loadProgress: blockchain.load_progress,
      }
      if (this.bootstrapTimes[blockchain.slug][0] === null) {
        this.bootstrapTimes[blockchain.slug] = [timerData, null]
      } else {
        this.bootstrapTimes[blockchain.slug][1] = timerData
      }
      this.updatePercent(blockchain.slug, loadProgress)
      const task = blockchain.tasks.find(
        (task) => task.type === 'bootstrap' && task.status === 'in_progress')
      if (loadProgress === 100.0) {
        blockchain.isBootstraping = false;
        // update also blockchain task
        if (task) {
          task.status = 'success'
        }
      } else if (task) {
        // if we launch bootstrap in another window then you will get updates
        // in this one, but you won't have 'time remaining' shown since
        // blockchain.tasks is not refetched - it's a rare case so we don't
        // handle it on purpose
        blockchain.isBootstraping = true;
      }
    },
    getChartId: function(blockchainSlug) {
      return `chartProgress-${blockchainSlug}`
    },
    updatePercent: function(blockchainSlug, percent) {
      this.$refs[`chart-${blockchainSlug}`][0].updateSeries(
        [ percent, 100 - percent ],
      );
      // update remaining time
      if (this.bootstrapTimes[blockchainSlug][1] !== null) {
        const missingPercent = 100.0 - this.bootstrapTimes[blockchainSlug][1].loadProgress
        const percentRaised = this.bootstrapTimes[blockchainSlug][1].loadProgress -
          this.bootstrapTimes[blockchainSlug][0].loadProgress
        const duration = this.bootstrapTimes[blockchainSlug][1].curTimeMillisec -
          this.bootstrapTimes[blockchainSlug][0].curTimeMillisec
        this.countdown[blockchainSlug] = this.getRemainingTimeRepr(
          (missingPercent/percentRaised) * duration)
      }
    },
    getRemainingTimeRepr: function(millisec) {
      const days = Math.floor(millisec / (1000 * 60 * 60 * 24));
      const hours = Math.floor((millisec % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((millisec % (1000 * 60 * 60)) / (1000 * 60));
      let res = []
      if (days) {
        res.push(`${days}d`)
      }
      if (days || hours) {
        res.push(`${hours}h`)
      }
      if (days || hours || minutes) {
        res.push(`${minutes}m`)
      }
      if (res.length === 0) {
        return '< 1m'
      }
      return res.join(' ')
    },
    generateChart: function(blockchain) {
      return {
        // blockchainSlug is not part of graph data, just there to know when we
        // already have graph for blockchain X generated
        blockchainSlug: blockchain.slug,
        series: [Number(blockchain.load_progress), 100 - Number(blockchain.load_progress)],
        chartOptions: {
          chart: {
            type: 'donut',
            foreColor: '#ffffff',
            animations: { enabled: true },
          },
          dataLabels: {
            enabled: false,
          },
          labels: ['Loaded', 'Missing'],
          colors: ['#5283ff', '#808080'],
          stroke: { show: false },
          legend: {
            position: 'top',
            fontSize: '18px',
            labels: {
              colors: '#c8c8c8',
            },
            onItemClick: {
                toggleDataSeries: false,
            },
          },
          plotOptions: {
            pie: {
              donut: {
                labels: {
                  show: true,
                  total: {
                    showAlways: true,
                    show: true,
                    label: 'Loaded',
                    color: '#ffffff',
                    fontSize: '22px',
                    formatter: (w) => {
                      return w.config.series[0] + '%'
                    },
                  },
                }
              }
            }
          },
        },
      }
    },
    showAddOrEditBlockchainDialog: function(blockchain) {
      // need to reset it since it's not enough to reset it on close event because
      // if you add a node and then open add-blockchain dialog it won't rerender
      // the component so you won't see the new node
      this.blockchainDialogKey++;
      this.addOrEditBlockchainDialogSelectedBlockchain = blockchain;
      this.addOrEditBlockchainDialog = true;
    },
    closeAddOrEditBlockchainDialog: function(refetch) {
      this.addOrEditBlockchainDialog=false;
      if (refetch) {
        this.fetchBlockchains();
      }
      this.blockchainDialogKey++;
    },
    onBlockchainCreated: async function(blockchain) {
      this.closeAddOrEditBlockchainDialog(true)
      await this.fetchBlockchains();
      if (this.selectedBlockchain() == null) {
        this.changeBlockchain(blockchain)
      }
    },
    resetBootstrapingData: function(blockchain) {
      // reset countdown data
      this.countdown[blockchain.slug] = null
      this.bootstrapTimes[blockchain.slug] = [null, null]
      blockchain.bootstrapInfo = null
    },
    bootstrapBlockchain: async function(blockchain) {
      this.resetBootstrapingData(blockchain)
      this.loading.bootstrap = true
      try {
        await blockchainAPI.bootstrapBlockchain(blockchain.slug);
        blockchain.isBootstraping = true;
        this.$toasted.success('Bootstraping in progress')
      } catch(error) {
        this.$toasted.error('Failed to bootstrap blockchain');
      }
      this.loading.bootstrap = false
    },
    abortBootstrap: async function(blockchain) {
      this.resetBootstrapingData(blockchain)
      this.loading.abort = true
      try {
        await blockchainAPI.abortBootstrap(blockchain.slug);
        blockchain.isBootstraping = false;
        this.$toasted.success('Bootstraping aborted')
      } catch(error) {
        this.$toasted.error('Failed to abort bootstrap');
      }
      this.loading.abort = false
    },
    getBootstrapInfo: function(_status, failureReason) {
      if (_status === 'failure' && failureReason == null) {
        failureReason = 'Unknown'
      }
      const statusMsgMapping = {
        failure: {
          text: `Bootstrap failed: ${failureReason}`,
          icon: 'mdi-alert',
          iconColor: 'error',
        },
        success: {
          text: 'Blockchain fully loaded',
          icon: 'mdi-party-popper',
          iconColor: 'primary',
        },
        skipped: {
          text: 'Bootstrap cancelled',
          icon: 'mdi-cancel',
          iconColor: 'warning',
        },
      }
      return statusMsgMapping[_status]
    },
    deleteBlockchain: async function(blockchain) {
      this.confirmLoading = true
      this.loading.deletingBlockchain[blockchain.slug] = true;
      try {
        await blockchainAPI.deleteBlockchain(blockchain.slug);
        if (this.selectedBlockchain().slug === blockchain.slug) {
          // select another one
          const otherBlockchains = this.blockchains.filter((bc) => bc.slug !== blockchain.slug)
          if (otherBlockchains.length > 0) {
            let changeToBlockchain = otherBlockchains[0]
            const defaultBlockchain = otherBlockchains.find((bc) => bc.default === true)
            if (defaultBlockchain) {
              changeToBlockchain = defaultBlockchain
            }
            this.changeBlockchain(changeToBlockchain)
          } else {
            this.resetSelectedBlockchain()
          }
        }
        this.$toasted.info('Blockchain is being deleted');
      } catch(error) {
        this.$toasted.error(getErrorMsg(error));
      }
      this.loading.deletingBlockchain[blockchain.slug] = false;
      this.confirmLoading = false
    },
    showConfirmDialog: function(action, element) {
      const actions = {
        'blockchain-delete': {
          text: `Are you sure you want to delete blockchain '${element.name}'?`,
          fn: this.deleteBlockchain.bind(this, element),
        },

      };
      action = actions[action];
      this.confirmText = action['text'];
      this.confirmDialog = true;
      this.confirmAction = action['fn'];
    },
    closeConfirmDialog: function(refetch=false) {
      this.confirmDialog = false;
      this.confirmText = '';
      this.confirmLoading = false;
      if (refetch) {
        this.fetchBlockchains();
      }
    },
    executeConfirmedAction: async function() {
      // make sure confirmAction finishes before refetching is called
      await this.confirmAction();
    },
  },
}
</script>
<style scoped>
.primary-color {
  color: #e5dd00;
}
</style>
