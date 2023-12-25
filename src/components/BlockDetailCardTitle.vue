<template>
  <v-card-title>
    <v-icon
      color="primary"
      dark
    >mdi-cube</v-icon>
    <h3>&nbsp;&nbsp;Block ({{ block.height }}){{ block.prev_hash === '0000000000000000000000000000000000000000000000000000000000000000' ? ' - Genesis' : ''}}</h3>
    <v-spacer></v-spacer>
    <v-col v-if="$vuetify.breakpoint.xsOnly" cols="12" class="py-0"></v-col>
    <v-btn
      @click="routeToWrapper(
        'block',
        {
          blockchain: selectedBlockchain().slug,
          blockHash: block.prev_hash,
        }
      )"
      :disabled="block.prev_hash === '0000000000000000000000000000000000000000000000000000000000000000'"
      :class="{'mr-4': true, 'mt-5': $vuetify.breakpoint.xsOnly }"
    >
      <v-icon>mdi-arrow-left-circle</v-icon>
    </v-btn>
    <v-spacer v-if="$vuetify.breakpoint.xsOnly"></v-spacer>
    <v-btn
      @click="routeToWrapper(
        'block',
        {
          blockchain: selectedBlockchain().slug,
          blockHash: block.next_hash,
        }
      )"
      :disabled="block.next_hash === null"
      :class="{'mt-5': $vuetify.breakpoint.xsOnly }"
    >
      <v-icon>mdi-arrow-right-circle</v-icon>
    </v-btn>
    <v-col
      class="px-0 text-right"
      cols="12"
      v-for="next_reorg in block.next_block_reorgs"
      :key="next_reorg.id"
    >
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            v-on="on"
            v-bind="attrs"
            @click="routeToWrapper(
              'block',
              {
                blockchain: selectedBlockchain().slug,
                blockHash: next_reorg.start_reorg_block.hash,
              }
            )"
          >
            <v-icon
              color="red"
              class="mr-3"
            >
              mdi-call-split
            </v-icon>
            <v-icon color="error" class="mr-1">mdi-arrow-right-circle</v-icon>
          </v-btn>
        </template>
        <span>Fork to block {{ next_reorg.start_reorg_block.hash }}</span>
      </v-tooltip>
    </v-col>
    <v-alert v-if="block.reorg != null" type="error" class="mt-5" style="word-break: normal">
      This block has been reorged. Inputs, outputs and kernels of this block
      might not exist on the main chain. Inputs and outputs data
      (eg. 'spent' and 'confirmations') are related to reorged chain, not
      the main chain!
    </v-alert>
  </v-card-title>
</template>
<script>
import { createNamespacedHelpers } from 'vuex'
import { routeTo } from '@/shared/helpers'

const { mapGetters } = createNamespacedHelpers('blockchain')

export default {
  name: 'BlockDetailCardTitle',
  props: ['block'],
  data: () => ({}),
  methods: {
    ...mapGetters([
      'selectedBlockchain',
    ]),
    routeToWrapper: function(routeName, params = {}) {
      return routeTo(routeName, params)
    },
  },
}
</script>
