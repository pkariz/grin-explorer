<template>
  <v-container fluid class="pa-0 mx-0" style="min-height: 750px;">
    <template v-if="loading().search">
      <v-progress-linear
        indeterminate
        color="primary"
      ></v-progress-linear>
    </template>
  <v-col cols="12" class="pa-0 mx-0" v-else>
    <v-data-table
      :headers="headers"
      :items="blocks() || []"
      :loading="blocks() === null || loading().blocks"
      class="elevation-0 mb-0 pt-5 block-table"
      :server-items-length="totalBlocks()"
      :options.sync="options"
      :footer-props="{
        showFirstLastPage: true,
        'items-per-page-options': [10, 20, 50],
      }"
      disable-sort
      item-key="hash"
      :no-data-text="errorMsg ? errorMsg : 'There are no blocks.'"
      @update:page="setPage($event); loadBlocks()"
      @update:items-per-page="setItemsPerPage($event); loadBlocks()"
    >
      <template v-slot:[`item.height`]="{ item }">
        <router-link :to="`/${item.blockchain.slug}/blocks/${item.hash}/`">{{ item.height }}</router-link>

        <v-tooltip
          top
          v-for="starting_reorg_block in item.starting_reorg_blocks"
          :key="starting_reorg_block.hash"
        >
          <template v-slot:activator="{ on, attrs }">
            <v-icon
              color="red"
              class="ml-3"
              v-on="on"
              v-bind="attrs"
              @click.stop="routeToWrapper('block', { blockHash: starting_reorg_block.hash })"
            >
              mdi-call-split
            </v-icon>
          </template>
          <span>Fork to block {{ starting_reorg_block.hash }}</span>
        </v-tooltip>
      </template>
      <template v-slot:[`item.timestamp`]="{ item }">
        {{ getFormattedDate(item.timestamp)}}
      </template>
    </v-data-table>
    <template v-if="$vuetify.breakpoint.xsOnly && firstBlocksLoaded && loading().blocks">
      <v-progress-linear
        indeterminate
        color="primary"
      ></v-progress-linear>
    </template>
  </v-col>
  </v-container>
</template>

<script>
import { createNamespacedHelpers } from 'vuex'
import { routeTo } from '@/shared/helpers'
import moment from 'moment'

const { mapGetters, mapActions, mapState } = createNamespacedHelpers('blockchain')

export default {
  name: 'Blocks',
  data: () => ({
    headers: [
      { text: 'Height', value: 'height', 'class': 'primary-color' },
      { text: 'Timestamp', value: 'timestamp', 'class': 'primary-color' },
      { text: '# Kernels', value: 'nr_kernels', 'class': 'primary-color' },
      { text: '# Inputs', value: 'nr_inputs', 'class': 'primary-color' },
      { text: '# Outputs', value: 'nr_outputs', 'class': 'primary-color' },
    ],
    options: { sortBy: ['height'], sortDesc: [true] },
    errorMsg: null,
    firstBlocksLoaded: false,
  }),
  watch: {
    '$store.state.blockchain.page': function() {
      // need to update this.options.page otherwise if you search for 'reorgs'
      // datatable's footer data is wrong
      this.options.page = this.$store.state.blockchain.page
    },
    '$store.state.blockchain.itemsPerPage': function() {
      this.options.itemsPerPage = this.$store.state.blockchain.itemsPerPage
    },
    '$store.state.blockchain.blocks': function() {
      this.firstBlocksLoaded = true;
    },
  },
  created: function() {
    this.options.page = this.page()
    this.options.itemsPerPage = this.itemsPerPage()
    this.loadBlocks()
  },
  methods: {
    ...mapState([
      'search',
    ]),
    ...mapGetters([
      'selectedBlockchain',
      'blocks',
      'loading',
      'totalBlocks',
      'page',
      'itemsPerPage',
    ]),
    ...mapActions([
      'loadBlocks',
      'setBlocks',
      'resetBlocks',
      'setTotalBlocks',
      'setPage',
      'setSearch',
      'setItemsPerPage',
    ]),
    routeToWrapper: function(routeName, params = {}) {
      return routeTo(routeName, params)
    },
    getFormattedDate: function (date) {
      return moment(date).format('YYYY-MM-DD HH:mm:ss');
    }
  },
}
</script>
<style scoped>
.btn-action {
  width: 125px;
}

>>>.v-data-table caption {
  margin-top: 10px;
  margin-bottom: 20px;
  font-weight: 500;
  font-size: x-large;
}

.custom-caption {
  color: #bfbfbf;
}

>>>.primary-color {
  color: #484740 !important;
}

>>>.v-data-table > .v-data-table__wrapper > table > thead > tr > th {
  font-size: 1rem !important;
}

>>>.v-data-footer {
  font-size: 1rem !important;
}

>>>.v-data-footer__select .v-select__selections .v-select__selection--comma {
  font-size: 1rem !important;
}

>>>tbody > tr.newblock {
  animation: blinker 1.5s linear;
}

@keyframes blinker {
  0% {
    opacity: 0;
    background: #e5dd00;
  }
}

.block-table {
  border-width: 5px !important;
}

@media only screen and (min-width: 600px) {
  >>>td {
    padding-top: 20px !important;
    padding-bottom: 20px !important;
  }
  >>>tr > td:first-child {
    border-left: thin solid rgba(255, 255, 255, 0.22);
  }
  >>>tr > td:last-child {
    border-right: thin solid rgba(255, 255, 255, 0.22);
  }
  >>>tr > th {
    border-top: medium double rgba(255, 255, 255, 0.22);
  }
  >>>tr > th:first-child {
    border-left: medium double rgba(255, 255, 255, 0.22);
    border-radius: 6px 0px 0px 0px;
  }
  >>>tr > th:last-child {
    border-right: medium double rgba(255, 255, 255, 0.22);
    border-radius: 0px 6px 0px 0px;
  }
  >>>thead {
    background-color: #e5dd00;
  }
  >>>thead th {
    color: #484740 !important;
  }
}
@media only screen and (max-width: 600px) {
  >>>tbody > tr {
    border: medium solid rgba(255, 255, 255, 0.12);
    margin-bottom: 5px;
  }
}

>>>tbody tr:nth-of-type(even) {
  background-color: rgba(62, 62, 62, .55);
}

@media all and (max-width: 599.9999px) {
  >>>.v-data-footer {
    justify-content: center;
    padding-bottom: 8px;
  }
  >>>.v-data-footer__select {
    margin: 0 auto;
    padding-bottom: 5px;
  }

  >>>.v-data-footer__pagination {
    width: 100%;
    margin: 0;
    padding-bottom: 5px;
  }

  >>>.v-application--is-ltr .v-data-footer__select .v-select {
    margin: 5px 0 5px 13px;
  }
  >>>.v-application--is-rtl .v-data-footer__select .v-select {
    margin: 5px 13px 5px 0;
  }
}

</style>
