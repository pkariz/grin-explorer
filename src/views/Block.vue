<template>
  <v-container fluid class="pa-0 mx-0" style="min-height: 850px">
  <v-progress-linear
    color="primary"
    indeterminate
    v-if="loading.initial"
  ></v-progress-linear>
  <template v-else-if="block !== null">
    <v-card>
      <block-detail-card-title :block="block"></block-detail-card-title>
      <v-card-text :class="{ 'px-1': $vuetify.breakpoint.xsOnly, 'pb-0': true }">
        <block-detail-header :block="block" :trimValueFn="trimValue"></block-detail-header>
      </v-card-text>
    </v-card>
    <br>
    <v-card>
      <v-card-text>
        <v-row>
          <v-col cols="5" class="text-center">
            <h3 style="color: white">Inputs ({{ block.inputs.length }})</h3>
          </v-col>
          <v-col cols="2" class="text-center">
            <v-icon
              color="primary"
              dark
            >mdi-transfer-right</v-icon>
          </v-col>
          <v-col cols="5" class="text-center">
            <h3 style="color: white">Outputs ({{ block.outputs.length }})</h3>
          </v-col>
        </v-row>
        <v-divider class="my-5"></v-divider>
        <v-row>
          <v-col cols="5" class="text-center d-inline-block">
            <div
              v-for="(input, index) in block.inputs.slice(0, numShowIOElements)"
              :key="input.commitment"
              class="io"
            >
              <v-row class="align-center">
                <v-col
                  :class="{
                    'col-12 col-12 col-sm-10 col-md-11 flex-grow-1 flex-shrink-0 pt-3': true,
                    'pr-0 pl-5': $vuetify.breakpoint.smAndUp
                  }"
                  :style="{'padding-top': index === 0 && $vuetify.breakpoint.xsOnly ? '44px !important': ''}"
                >
                  {{ trimValue(input.commitment, 'io') }}
                </v-col>
                <v-col :class="{ 'col-12 col-12 col-sm-2 col-md-1 flex-shrink-1 flex-grow-0 pr-0 pl-0': true, 'pt-2': $vuetify.breakpoint.smAndUp, 'pt-0': $vuetify.breakpoint.xsOnly }">
                  <v-btn
                    class="float-sm-right"
                    icon
                    @click="showElementDetails(input, 'input')"
                  >
                    <v-icon>mdi-chevron-down</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            </div>
          </v-col>
          <v-col
            cols="2"
            class="text-center d-inline-block d-flex align-center justify-center"
          >
            <v-icon
              color="primary"
              dark
            >mdi-transfer-right</v-icon>
          </v-col>
          <v-col cols="5" class="text-center d-inline-block">
            <div
              v-for="output in block.outputs.slice(0, numShowIOElements)"
              :key="output.commitment"
              class="io"
            >
              <v-row class="align-center">
                <v-col
                  :class="{
                    'd-flex align-center justify-center pl-4': true,
                    'pb-2': $vuetify.breakpoint.xsOnly,
                    'col-12 col-sm-2 col-md-1 float-sm-left': true,
                  }"
                  v-if="output.output_type === 'Coinbase'"
                >
                  <v-icon
                    color="primary"
                    dark
                  >mdi-pickaxe</v-icon>
                </v-col>
                <v-col
                  :class="{
                    'pt-0 flex-grow-1': output.output_type === 'Coinbase' && $vuetify.breakpoint.xsOnly,
                    'pl-3 pt-3 pr-0 flex-grow-1': output.output_type === 'Coinbase' && !$vuetify.breakpoint.xsOnly,
                    'pt-3 pl-5 pr-0 flex-grow-1': output.output_type !== 'Coinbase' && !$vuetify.breakpoint.xsOnly,
                    'col-sm-8 col-md-10': output.output_type === 'Coinbase',
                    'col-sm-10 col-md-11': output.output_type !== 'Coinbase',
                  }"
                >
                  {{ trimValue(output.commitment, 'io') }}
                </v-col>
                <v-col
                  :class="{
                    'col-sm-2 col-md-1 col-12 flex-shrink-1 flex-grow-0': true,
                    'pt-2 pl-0 pr-0': $vuetify.breakpoint.smAndUp,
                    'pt-0': $vuetify.breakpoint.xsOnly
                  }"
                >
                  <v-btn
                    class="float-sm-right"
                    icon
                    @click="showElementDetails(output, 'output')"
                  >
                    <v-icon>mdi-chevron-down</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            </div>
          </v-col>
          <v-col cols="12" class="text-center" v-if="maxIOelements > 10">
            <v-btn
              elevation="0"
              small
              @click="triggerElementNumberChange('io')"
            >
              {{ numShowIOElements !== maxIOelements ? `show more (${numShowIOElements}/${maxIOelements})` : 'show less' }}
              <v-icon>mdi-chevron-{{ numShowIOElements !== maxIOelements ? 'down': 'up' }}</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    <br>
    <v-card>
      <v-card-text>
        <v-row>
          <v-col cols="12" class="text-center">
            <v-icon
              color="primary"
              dark
            >mdi-fingerprint</v-icon>
            <h3 class="d-inline-block kernel-heading">
              &nbsp;&nbsp;Kernels ({{ block.kernels.length }})
            </h3>
          </v-col>
        </v-row>
        <v-divider class="my-5"></v-divider>
        <v-row class="pt-7">
        <v-col cols="12" class="text-center d-inline-block">
          <div
            v-for="kernel in block.kernels.slice(0, numShowKernelElements)"
            :key="kernel.excess"
          >
            <v-row class="mb-3 justify-center">
              <v-col :class="{'io': true, 'pt-0': kernel.features !== 'Coinbase' && $vuetify.breakpoint.xsOnly }" style="max-width: 720px" cols="12">
                <v-row class="align-center">
                  <v-col
                    :cols="$vuetify.breakpoint.xsOnly ? '12' : '1'"
                    :class="{
                      'd-flex align-center justify-center': true,
                      'pb-0': $vuetify.breakpoint.xsOnly,
                      'pl-7': $vuetify.breakpoint.smAndUp,
                    }"
                  >
                    <v-icon
                      color="primary"
                      dark
                      v-if="kernel.features === 'Coinbase'"
                    >mdi-pickaxe</v-icon>
                  </v-col>
                  <v-spacer></v-spacer>
                  <v-col
                    :cols="!$vuetify.breakpoint.xsOnly ? '11': '12'"
                    class="d-flex flex-grow-1 align-center justify-center"
                  >
                    {{ trimValue(kernel.excess, 'io') }}
                    <v-spacer></v-spacer>
                    <v-btn
                      class="float-sm-right"
                      icon
                      @click="showElementDetails(kernel, 'kernel')"
                    >
                      <v-icon>mdi-chevron-down</v-icon>
                    </v-btn>
                    <v-spacer></v-spacer>
                  </v-col>
                </v-row>
              </v-col>
            </v-row>
          </div>
        </v-col>
        <v-col cols="12" class="text-center" v-if="maxKernelelements > 10">
          <v-btn
            elevation="0"
            small
            @click="triggerElementNumberChange('kernels')"
          >
            {{ numShowKernelElements !== maxKernelelements ? `show more (${numShowKernelElements}/${maxKernelelements})` : 'show less' }}
            <v-icon>mdi-chevron-{{ numShowKernelElements !== maxKernelelements ? 'down': 'up' }}</v-icon>
          </v-btn>
        </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    <block-element-dialog
      v-if="elementDialogItem"
      class="d-none"
      :dialog="showElementDialog"
      :title="elementDialogTitle"
      :item="elementDialogItem"
      :attrs="elementDialogAttrs"
      :getValueFn="elementGetValue"
      @close="showElementDialog = false"
    ></block-element-dialog>
  </template>
  <template v-else>
  No block data
  </template>
  </v-container>
</template>

<script>
import { createNamespacedHelpers } from 'vuex'
import blockService from '../services/block'
import BlockElementDialog from '@/components/BlockElementDialog'
import BlockDetailCardTitle from '@/components/BlockDetailCardTitle'
import BlockDetailHeader from '@/components/BlockDetailHeader'
import { copyToClipboard, routeTo } from '@/shared/helpers';

const { mapGetters, mapActions } = createNamespacedHelpers('blockchain')


export default {
  name: 'Blocks',
  components: {
    'block-element-dialog': BlockElementDialog,
    'block-detail-card-title': BlockDetailCardTitle,
    'block-detail-header': BlockDetailHeader,
  },
  props: ['blockHash'],
  data: () => ({
    block: null,
    numShowIOElements: 10,
    numShowKernelElements: 10,
    maxIOelements: 10,
    maxKernelelements: 10,
    defaultNumElements: 10,
    elementIncrease: 20,
    loading: { initial: true },
    copied: {
      hash: false,
    },
    showElementDialog: false,
    elementDialogTitle: '',
    elementDialogItem: null,
    elementDialogAttrs: null,
    inputAttrs: [
      { name: 'commitment', repr: 'commitment', copy: false },
      {
        name: 'created_in',
        repr: 'created in',
        link: (item, val) => {
          return val == null ?
            null :
            { name: 'block', params: { blockHash: val[1] } }
        },
      },
    ],
    outputAttrs: [
      { name: 'commitment', repr: 'commitment', copy: false },
      { name: 'output_type', repr: 'type' },
      {
        name: 'spent_in',
        repr: 'spent',
        getLinkPrepend: (item, val) => val == null ? 'no' : 'yes (',
        getLinkAppend: (item, val) => val == null ? '' : ')',
        link: (item, val) => {
          return val == null ?
            null :
            { name: 'block', params: { blockHash: val[1] } }
        },
      },
      { name: 'proof', repr: 'proof', copy: false },
      { name: 'proof_hash', repr: 'proof hash', copy: false },
      { name: 'merkle_proof', repr: 'merkle proof', copy: false },
      { name: 'mmr_index', repr: 'mmr index' },
    ],
    kernelAttrs: [
      { name: 'excess', repr: 'excess', copy: false },
      { name: 'features', repr: 'features' },
      { name: 'fee', repr: 'fee' },
      { name: 'fee_shift', repr: 'fee shift' },
      { name: 'lock_height', repr: 'lock height' },
      { name: 'excess_sig', repr: 'excess sig', copy: false },
    ],
  }),
  created: function() {
    this.fetchBlock()
  },
  methods: {
    ...mapGetters([
      'selectedBlockchain',
    ]),
    ...mapActions([
      'changeBlockchain',
    ]),
    fetchBlock: function() {
      this.loading.initial = true
      blockService.fetchBlock(this.selectedBlockchain().slug, this.blockHash)
        .then((block) => {
          block.timestamp = (new Date(block.timestamp)).toUTCString()
          block.weight = this.getWeight(block)
          block.inputs.sort((a, b) => a.commitment.localeCompare(b.commitment))
          // miner output is always first
          block.outputs.sort((a, b) =>
            a.output_type === 'Coinbase' ?
              -1 :
              (b.output_type === 'Coinbase' ? 1 : a.commitment.localeCompare(b.commitment))
          )
          // miner kernel is always first
          block.kernels.sort((a, b) =>
            a.features === 'Coinbase' ?
              -1 :
              (b.features === 'Coinbase' ? 1 : a.excess.localeCompare(b.excess))
          )
          /* block.kernels.sort((a, b) => a.excess.localeCompare(b.excess)) */
          block.fee = block.kernels.map((k) => k.fee).reduce((a, b) => a + b, 0) / 1000000000
          this.maxIOelements = Math.max(block.inputs.length, block.outputs.length)
          this.maxKernelelements = block.kernels.length
          this.numShowIOElements = Math.min(this.numShowIOElements, this.maxIOelements)
          this.numShowKernelElements = Math.min(this.numShowKernelElements, this.maxKernelelements)
          this.block = block
        })
        .catch(() => {
          this.$toasted.error('Failed to fetch block');
        })
        .finally(() => {
          setTimeout(() => {
            this.loading.initial = false
          }, 0)
        })
    },
    getWeight: function(block) {
      return block.inputs.length +
        block.outputs.length * 21 +
        block.kernels.length * 3
    },
    trimValue: function(value, attr) {
      const trimAttrs = [
        'hash', 'proof', 'proof_hash', 'merkle_proof',
        'excess_sig',
      ]
      if (trimAttrs.includes(attr)) {
        if (this.$vuetify.breakpoint.xsOnly) {
          return value.substring(0,4) + '...' + value.slice(-4)
        }
      }
      return value;
    },
    routeToWrapper: function(routeName, params = {}) {
      return routeTo(routeName, params)
    },
    copyText: function(text, attr) {
      copyToClipboard(text);
      this.copied[attr] = true;
      setTimeout(() => {
        this.copied[attr] = false;
      }, 2000);
    },
    showElementDetails: function(element, _type) {
      // we show additional info in a dialog
      this.elementDialogItem = element
      if (_type === 'input') {
        this.elementDialogTitle = 'Input details'
        this.elementDialogAttrs = this.inputAttrs
      } else if (_type === 'output') {
        this.elementDialogTitle = 'Output details'
        this.elementDialogAttrs = this.outputAttrs
      } else if (_type === 'kernel') {
        this.elementDialogTitle = 'Kernel details'
        this.elementDialogAttrs = this.kernelAttrs
      } else {
        this.$toasted.error('Invalid element type')
        return
      }
      this.showElementDialog = true
    },
    elementGetValue: function(item, attr) {
      if (["spent_in", "created_in"].includes(attr)) {
        return item[attr] ? item[attr][0] : "";
      }
      return item[attr] != null ? this.trimValue(item[attr], attr) : "/"
    },
    triggerElementNumberChange: function(changeType) {
      if (changeType === 'io') {
        if (this.numShowIOElements < this.maxIOelements) {
          this.numShowIOElements += this.elementIncrease
          if (this.numShowIOElements > this.maxIOelements) {
            this.numShowIOElements = this.maxIOelements
          }
        } else {
          this.numShowIOElements = this.defaultNumElements
        }
      } else {
        if (this.numShowKernelElements < this.maxKernelelements) {
          this.numShowKernelElements += this.elementIncrease
          if (this.numShowKernelElements > this.maxKernelelements) {
            this.numShowKernelElements = this.maxKernelelements
          }
        } else {
          this.numShowKernelElements = this.defaultNumElements
        }

      }
    },
  },
}
</script>
<style scoped>
.primary-color {
  color: #e5dd00;
}

.io {
  margin-bottom: 10px;
  background-color: #3d3d3d;
  border-radius: 15px;
  padding: 10px 15px;
  word-break: break-word;
  /* monospace so that the width of all characters is the same */
  font-family: Monospace;
}

.kernel-heading {
  color: white;
  height: 24px;
  vertical-align: middle;
}
</style>
