<template>
  <v-card class="mx-auto" width="100%" style="min-height: 850px">
    <v-card-title>
      <v-tabs fixed-tabs>
        <v-tab
          v-for="tab in tabs"
          :key="tab.name"
          @click="selectedTab = tab.component"
        >
          <v-icon
            class="mr-2"
            color="primary"
            dark
          >{{ tab.icon }}</v-icon>
          <span v-if="$vuetify.breakpoint.smAndUp">{{ tab.text }}</span>
        </v-tab>
      </v-tabs>
    </v-card-title>
    <v-card-text :class="{'px-0': $vuetify.breakpoint.xsOnly}">
      <!-- NOTE: we don't have keep-alive here otherwise apexcharts would throw
      an error here when switching to 'nodes' tab -->
      <component :is="selectedTab" style="height: 100%"></component>
    </v-card-text>
  </v-card>
</template>

<script>
import Blockchains from '@/components/settings/Blockchains.vue';
import Nodes from '@/components/settings/Nodes.vue';

export default {
  name: 'Settings',
  data: () => ({
    tabs: [
      {
        name: 'blockchains',
        text: 'Blockchains',
        icon: 'mdi-cube',
        component: Blockchains,
      },
      {
        name: 'nodes',
        text: 'Nodes',
        icon: 'mdi-desktop-classic',
        component: Nodes,
      },
    ],
    selectedTab: Blockchains,
  }),
}
</script>
<style>
.theme--dark.v-tabs > .v-tabs-bar {
  background-color: inherit !important;
}
</style>
