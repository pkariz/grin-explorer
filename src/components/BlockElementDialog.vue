<template>
  <v-row justify="center">
    <v-dialog
      v-model="dialogWrapper"
      max-width="900px"
      @click:outside="$emit('close')"
    >
      <v-card>
        <v-card-title style="border-bottom: 4px double rgba(255, 255, 255, 0.22)">
          <span class="text-h5 primary-color">{{ title }}</span>
        </v-card-title>
        <v-card-text class="pt-3">
          <v-list class="transparent">
            <template v-for="(attr, index) in attrs">
              <v-list-item
                :key="attr.name"
                class="px-0"
              >
                <v-list-item-title class="text-left" style="max-width: 130px">{{ attr.repr }}:</v-list-item-title>
                <v-list-item-subtitle class="text-right py-2" style="white-space: normal">
                  {{ attr.getLinkPrepend ? attr.getLinkPrepend(item, item[attr.name]) : '' }}
                  <router-link
                    v-if="attr.link && attr.link(item, item[attr.name])"
                    :to="attr.link(item, item[attr.name])"
                  >
                    {{ getValueFn(item, attr.name) }}
                  </router-link>
                  <span v-else>
                    {{ getValueFn(item, attr.name) }}
                  </span>
                  <v-fab-transition v-if="attr.copy !== undefined && getValueFn(item, attr.name) !== '/'">
                    <v-icon
                      class="pa-1"
                      v-if="attr.copy"
                      color="yellow"
                    >
                      mdi-check
                    </v-icon>
                    <v-icon class="pa-1"
                      v-else
                      @click.stop="copyText(item[attr.name], attr)"
                    >
                      mdi-content-copy
                    </v-icon>
                  </v-fab-transition>
                  {{ attr.getLinkAppend ? attr.getLinkAppend(item, item[attr.name]) : '' }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-divider
                v-if="index < attrs.length - 1"
                :key="index"
              ></v-divider>
            </template>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            text
            @click="$emit('close')"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-row>
</template>
<script>
import { copyToClipboard } from '@/shared/helpers';

export default {
  name: 'BlockElementDialog',
  props: ['dialog', 'title', 'item', 'attrs', 'getValueFn'],
  data: () => ({
    dialogWrapper: true,
  }),
  created: function() {
    this.dialogWrapper = this.dialog
  },
  watch: {
    dialog: {
      handler () {
        this.dialogWrapper = this.dialog
      },
    },
  },
  methods: {
    copyText: function(text, attr) {
      copyToClipboard(text);
      attr.copy = true;
      setTimeout(() => {
        attr.copy = false;
      }, 2000);
    },
  },
}
</script>
<style scoped>
.primary-color {
  color: #e5dd00;
}
</style>
