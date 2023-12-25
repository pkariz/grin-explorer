<template>
  <div v-if="loading.initial" style="width: 100%; min-height: 765px; border: 5px ridge #8d8c8c32">
    <v-progress-linear
      color="primary"
      indeterminate
    ></v-progress-linear>
  </div>
  <div v-else style="width: 100%">
    <template v-if="graphs.length > 0">
      <div style="min-height: 765px; border: 5px ridge #8d8c8c32">
      <v-card
        class="mx-auto"
        width="100%"
        style="border: 0px; border-bottom: 1px solid #8d8c8c32"
        v-for="(graph, index) in graphs"
        :key="index"
      >
        <v-card-text>
          <apexchart v-if="graph.data != null" :type="graph.type" height="400" :options="graph.data.chartOptions" :series="graph.data.series"></apexchart>
        </v-card-text>
      </v-card>
      </div>
    </template>
    <span class="warning" v-else>No graph has been generated yet, please wait a few minutes</span>
  </div>
</template>

<script>

import { createNamespacedHelpers } from 'vuex'
import blockchainService from '@/services/blockchain'
import { getDateRepr } from '@/shared/helpers'

const { mapGetters } = createNamespacedHelpers('blockchain')


export default {
  name: 'Graphs',
  data: () => ({
    loading: { initial: true },
    graphs: [],
  }),
  created () {
    this.fetchGraphs()
  },
  methods: {
    ...mapGetters([
      'selectedBlockchain',
    ]),
    fetchGraphs: function() {
      this.loading.initial = true
      blockchainService.fetchGraphs(this.selectedBlockchain().slug)
        .then((data) => {
          if (data.transaction_graph === null) {
            this.graphs = []
          }
          this.graphs = [
            {
              type: 'line',
              data: this.generate_tx_graph_data(data.transaction_graph),
            },
          ];
        })
        .catch(() => {
          this.$toasted.error('Failed to fetch graphs');
        })
        .finally(() => {
          setTimeout(() => {
            this.loading.initial = false
          }, 0)
        })
    },
    generate_tx_graph_data: function(graphData) {
      if (graphData == null) {
        return null
      }
      return {
        series: [
          {
            name: 'Transactions',
            type: 'line',
            data: graphData.map((el) => el.kernels),
          },
          {
            name: 'Inputs',
            type: 'column',
            data: graphData.map((el) => el.inputs),
          },
          {
            name: 'Outputs',
            type: 'column',
            data: graphData.map((el) => el.outputs),
          },
        ],
        chartOptions: {
          colors: ['#FEB019', '#008FFB', '#00E396'],
          chart: {
            height: '100%',
            type: 'line',
            stacked: false,
            toolbar: {
              show: true,
              tools: {
                download: true,
                selection: false,
                zoom: false,
                zoomin: false,
                zoomout: false,
                pan: false,
                reset: false,
              },
            },
          },
          markers: {
            size: 1,
            shape: 'square',
          },
          dataLabels: {
            enabled: true,
            enabledOnSeries: [0],
          },
          stroke: {
            width: [4, 1, 1],
          },
          title: {
            text: 'Transaction count',
            align: 'center',
            style: {
              color: '#e5dd00',
              fontSize: '16px',
            },
          },
          xaxis: {
            categories: graphData.map((el) => getDateRepr(new Date(`${el.date}T00:00:00Z`))),
            labels: {
              style: {
                colors: '#FFFFFF',
              }
            },
            tooltip: {
              enabled: false
            }
          },
          yaxis: [
            {
              min: 0,
              // set max 5% above the highest number
              max: Math.floor(Math.max(...graphData.map(
                (el) => Math.max(el.kernels, el.inputs, el.outputs))) * 1.05),
              axisTicks: {
                show: true,
              },
              axisBorder: {
                show: true,
                color: '#FEB019'
              },
              labels: {
                style: {
                  colors: '#FEB019',
                },
              },
              title: {
                text: "Number of transactions",
                style: {
                  color: '#FEB019',
                }
              },
            },
          ],
          tooltip: {
            fixed: {
              enabled: true,
              position: 'topLeft',
              offsetY: 50,
              offsetX: 70
            },
            cssClass: 'chart-tooltip',
            theme: true,
          },
          legend: {
            labels: {
              colors: '#c8c8c8',
            },
          },
        },
      }
    },
  },
}
</script>
<style>
.chart-tooltip {
  border: 2px solid;
  background-color: #1b1b16;
  color: #c8c8c8;
}
.apexcharts-tooltip-title {
  border-bottom: 2px solid;
  text-align: center;
  font-weight: 900;
  font-size: 14px !important;
  background-color: #383838;
}
.apexcharts-menu {
  border: 2px solid;
  background: #1b1b16 !important;
  color: #c8c8c8;
}
.apexcharts-menu-item:not(:last-child) {
  border-bottom: 1px groove;
}
</style>
