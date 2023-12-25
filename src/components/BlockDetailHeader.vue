<template>
  <div>
    <v-simple-table class="mt-5 mainTable">
      <template v-slot:default>
        <tbody>
          <tr
            v-for="field in fields"
            :key="field.text"
          >
            <td class="text-capitalize primary-color" style="border-bottom: thin solid rgba(255, 255, 255, 0.12)">
              <h3>{{ field.text }}</h3>
            </td>
            <td
              style="text-align: right; word-break: break-word;border-bottom: thin solid rgba(255, 255, 255, 0.12)"
              class="pl-0 py-1"
            >
              {{ trimValueFn(getValue(field.attr), field.attr) }}
              <v-fab-transition v-if="field.copy">
                <v-icon
                  v-if="copied[field.attr]"
                  color="yellow"
                >
                  mdi-check
                </v-icon>
                <v-icon
                  v-else
                  @click.stop="copyText(getValue(field.attr), field.attr)"
                >
                  mdi-content-copy
                </v-icon>
              </v-fab-transition>
            </td>
          </tr>
        </tbody>
      </template>
    </v-simple-table>
    <v-expand-transition>
      <v-simple-table class="mt-0 extraTable" v-show="showExtraRows" style="border-top-style: none !important;">
        <template v-slot:default>
          <tbody>
            <tr
              v-for="field in extraFields"
              :key="field.text"
            >
              <td class="text-capitalize primary-color" style="border-bottom: thin solid rgba(255, 255, 255, 0.12)">
                <h3>{{ field.text }}</h3>
              </td>
              <td
                style="text-align: right; word-break: break-word;border-bottom: thin solid rgba(255, 255, 255, 0.12)"
                class="pl-0 py-1"
              >
                <template v-if="field.transform">
                  {{ field.transform(getValue(field.attr), field.attr) }}
                </template>
                <template v-else>
                  {{ trimValueFn(getValue(field.attr), field.attr) }}
                </template>
                <v-fab-transition v-if="field.copy">
                  <v-icon
                    v-if="copied[field.attr]"
                    color="yellow"
                  >
                    mdi-check
                  </v-icon>
                  <v-icon
                    v-else
                    @click.stop="copyText(getValue(field.attr), field.attr)"
                  >
                    mdi-content-copy
                  </v-icon>
                </v-fab-transition>
              </td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
    </v-expand-transition>

    <v-col cols="12" class="text-center">
        <v-btn
          icon
          large
          @click="toggleExtraRows()"
        >
          <v-icon>{{ showExtraRows ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
        </v-btn>
    </v-col>
  </div>
</template>
<script>
import { copyToClipboard, routeTo } from '@/shared/helpers';
import { get as _get } from 'lodash';

export default {
  name: 'BlockDetailHeaderCardText',
  props: ['block', 'trimValueFn'],
  data: () => ({
    fields: [
      { attr: 'hash', text: 'hash', copy: true },
      { attr: 'timestamp', text: 'timestamp' },
      { attr: 'header.total_difficulty', text: 'total difficulty' },
      { attr: 'weight', text: 'weight' },
      { attr: 'fee', text: 'fee' },
      { attr: 'confirmations', text: 'confirmations' },
    ],
    extraFields: [
      { attr: 'header.version', text: 'version' },
      { attr: 'header.kernel_root', text: 'kernel root', copy: true },
      { attr: 'header.output_root', text: 'output root', copy: true },
      { attr: 'header.range_proof_root', text: 'range proof root', copy: true },
      { attr: 'header.kernel_mmr_size', text: 'kernel mmr size' },
      { attr: 'header.output_mmr_size', text: 'output mmr size' },
      { attr: 'header.nonce', text: 'nonce' },
      { attr: 'header.edge_bits', text: 'edge bits' },
      { attr: 'header.secondary_scaling', text: 'secondary scaling' },
      { attr: 'header.total_kernel_offset', text: 'total kernel offset', copy: true },
      {
        attr: 'header.edge_bits',
        text: 'PoW algo',
        transform: (edgeBits) => edgeBits === 29 ? 'cuckARoo-29' : `cuckAToo-${edgeBits}`,
      },
      {
        attr: 'header.cuckoo_solution',
        text: 'cuckoo solution',
        transform: (solution) => '[ ' + solution.split(',').join(', ') +' ]',
        copy: true,
      },
    ],
    copied: {},
    showExtraRows: false,
  }),
  created () {
    for (const obj of this.fields.concat(this.extraFields).filter((el) => el.copy)) {
      this.$set(this.copied, obj['attr'], false)
    }
  },
  methods: {
    routeToWrapper: function(routeName, params = {}) {
      return routeTo(routeName, params)
    },
    getValue: function(attr) {
      if (attr === 'weight') {
        return `${this.block.weight} / 40000 (${this.block.weight / 40000}%)`
      }
      return _get(this.block, attr)
    },
    copyText: function(text, attr) {
      copyToClipboard(text);
      this.copied[attr] = true;
      setTimeout(() => {
        this.copied[attr] = false;
      }, 2000);
    },
    toggleExtraRows: function() {
      this.showExtraRows = !this.showExtraRows
    },
  },
}
</script>
<style scoped>
.primary-color {
  color: #e5dd00;
}
.extraTable {
  border-top-right-radius: 0px !important;
  border-top-left-radius: 0px !important;
}
.mainTable {
  border-bottom-right-radius: 0px !important;
  border-bottom-left-radius: 0px !important;
}
</style>
