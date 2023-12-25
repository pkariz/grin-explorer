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
      <template v-if="nodeGroups.length > 0">
        <v-col cols="12" v-for="nodeGroup in nodeGroups" :key="nodeGroup.slug">
          <v-card>
            <v-card-title>
              <v-row>
                <v-col :cols="$vuetify.breakpoint.xsOnly ? '12': '6'">
                  <span class="primary-color">Group:</span>&nbsp;{{ nodeGroup.name }}
                </v-col>
                <v-col
                  :cols="$vuetify.breakpoint.xsOnly ? '12': '6'"
                  :class="{'text-right': $vuetify.breakpoint.smAndUp}"
                >
                  <v-btn text color="primary" outlined @click="showAddOrEditNodeDialog(null, nodeGroup)">
                    Add node
                  </v-btn>
                  <v-btn
                    text
                    :class="{ 'ml-2': $vuetify.breakpoint.smAndUp, 'mt-2': $vuetify.breakpoint.xsOnly }"
                    color="#e35449"
                    outlined
                    @click="showConfirmDialog('nodegroup-delete', nodeGroup)"
                  >
                    <v-icon>mdi-delete</v-icon>
                    &nbsp;delete
                  </v-btn>
                </v-col>
              </v-row>
            </v-card-title>
            <v-card-text :class="{'px-0': $vuetify.breakpoint.xsOnly}">
              <v-row v-for="node in nodeGroup.nodes" :key="node.slug" class="ma-2" style="border: 2px groove grey;">
                  <v-col cols="12">
                    <v-row class="pa-2">
                      <v-col class="col-12 col-sm-6">
                        <h2 class="text-left"><span class="primary-color">Node:</span>&nbsp;{{ node.name }}</h2>
                      </v-col>
                      <v-col :class="{'col-12 col-sm-6': true, 'text-right': $vuetify.breakpoint.smAndUp}">
                        <v-btn text color="primary" class="mr-2" outlined @click="showAddOrEditNodeDialog(node, nodeGroup)">
                          <v-icon>mdi-pencil</v-icon>
                          &nbsp;Edit
                        </v-btn>
                        <v-btn :class="{'mt-3': $vuetify.breakpoint.xsOnly}" text color="#e35449" outlined @click="showConfirmDialog('node-delete', node)">
                          <v-icon>mdi-delete</v-icon>
                          &nbsp;delete
                        </v-btn>
                      </v-col>
                    </v-row>
                  </v-col>
                  <v-col cols="12">

                    <v-list class="transparent">
                      <v-divider></v-divider>
                      <!-- api url -->
                      <v-list-item class="px-3">
                        <!-- if we have v-list-item-content wrapper it will put both in a separate line,
                             we want this on mobile but not otherwise. This solution is horrible but it
                             works and fixing this is low priority -->
                        <v-list-item-content v-if="$vuetify.breakpoint.xsOnly">
                          <v-list-item-title class="text-left" style="max-width: 80px"><strong>URL:</strong></v-list-item-title>
                          <v-list-item-subtitle class="text-left">
                            {{ node.api_url }}
                          </v-list-item-subtitle>
                        </v-list-item-content>
                        <template v-else>
                          <v-list-item-title class="text-left" style="max-width: 80px"><strong>URL:</strong></v-list-item-title>
                          <v-list-item-subtitle class="text-right">
                            {{ node.api_url }}
                          </v-list-item-subtitle>
                        </template>
                      </v-list-item>
                      <v-divider></v-divider>
                      <!-- username -->
                      <v-list-item class="px-3">
                        <v-list-item-content v-if="$vuetify.breakpoint.xsOnly">
                          <v-list-item-title class="text-left" style="max-width: 80px"><strong>Username:</strong></v-list-item-title>
                          <v-list-item-subtitle class="text-left">
                            {{ node.api_username }}
                          </v-list-item-subtitle>
                        </v-list-item-content>
                        <template v-else>
                          <v-list-item-title class="text-left" style="max-width: 80px"><strong>Username:</strong></v-list-item-title>
                          <v-list-item-subtitle class="text-right">
                            {{ node.api_username }}
                          </v-list-item-subtitle>
                        </template>
                      </v-list-item>
                      <v-divider></v-divider>
                      <!-- password -->
                      <v-list-item class="px-3">
                        <v-list-item-content v-if="$vuetify.breakpoint.xsOnly">
                          <v-list-item-title class="text-left" style="max-width: 150px">
                            <strong>Password:</strong>
                            &nbsp;&nbsp;
                            <v-fab-transition>
                              <v-icon
                                v-if="showPassword[node.slug]"
                                color="yellow"
                                @click="showPassword[node.slug] = false"
                              >
                                mdi-eye-off
                              </v-icon>
                              <v-icon
                                v-else
                                @click.stop="showPassword[node.slug] = true"
                                color="yellow"
                              >
                                mdi-eye
                              </v-icon>
                            </v-fab-transition>
                          </v-list-item-title>
                          <v-list-item-subtitle class="text-left">
                            {{ showPassword[node.slug] ? node.api_password : '***************' }}
                          </v-list-item-subtitle>
                        </v-list-item-content>
                        <template v-else>
                          <v-list-item-title class="text-left" style="max-width: 80px"><strong>Password:</strong></v-list-item-title>
                          <v-list-item-subtitle class="text-right">
                            {{ showPassword[node.slug] ? node.api_password : '********************' }}
                            &nbsp;&nbsp;
                            <v-fab-transition>
                              <v-icon
                                v-if="showPassword[node.slug]"
                                color="yellow"
                                @click="showPassword[node.slug] = false"
                              >
                                mdi-eye-off
                              </v-icon>
                              <v-icon
                                v-else
                                @click.stop="showPassword[node.slug] = true"
                                color="yellow"
                              >
                                mdi-eye
                              </v-icon>
                            </v-fab-transition>
                          </v-list-item-subtitle>
                        </template>
                      </v-list-item>
                      <v-divider></v-divider>
                      <!-- archive -->
                      <v-list-item class="px-3">
                        <v-list-item-content v-if="$vuetify.breakpoint.xsOnly">
                          <v-list-item-title class="text-left" style="max-width: 80px"><strong>Archive:</strong></v-list-item-title>
                          <v-list-item-subtitle class="text-left">
                            <v-icon color="yellow">
                              {{ node.archive ? 'mdi-check': 'mdi-close' }}
                            </v-icon>
                          </v-list-item-subtitle>
                        </v-list-item-content>
                        <template v-else>
                          <v-list-item-title class="text-left" style="max-width: 80px"><strong>Archive:</strong></v-list-item-title>
                          <v-list-item-subtitle class="text-right">
                            <v-icon color="yellow">
                              {{ node.archive ? 'mdi-check': 'mdi-close' }}
                            </v-icon>
                          </v-list-item-subtitle>
                        </template>
                      </v-list-item>
                    </v-list>
                  </v-col>
                </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </template>
      <template v-else>
        <v-col cols="12">
          <v-card>
            <v-card-title>
              No node groups
            </v-card-title>
          </v-card>
        </v-col>
      </template>
    </template>
    </v-row>
    <br />
    <v-btn color="primary" class="mb-3" outlined @click="showAddNodeGroupDialog">
      Add node group
    </v-btn>
    <add-or-edit-node-dialog
      v-if="addOrEditNodeDialogSelectedGroup != null"
      :dialog="addOrEditNodeDialog"
      :group="addOrEditNodeDialogSelectedGroup"
      :node="addOrEditNodeDialogSelectedNode"
      @close="closeAddOrEditNodeDialog(false)"
      @created="closeAddOrEditNodeDialog(true)"
      @modified="closeAddOrEditNodeDialog(true)"
    ></add-or-edit-node-dialog>
    <add-node-group-dialog
      :key="addNodeGroupDialogKey"
      :dialog="addNodeGroupDialog"
      @close="closeAddNodeGroupDialog(false)"
      @created="closeAddNodeGroupDialog(true)"
    ></add-node-group-dialog>
    <confirm-dialog
      v-if="confirmText"
      :dialog="confirmDialog"
      :text="confirmText"
      @close="closeConfirmDialog"
      @confirmed="executeConfirmedAction(); closeConfirmDialog()"
    ></confirm-dialog>
  </v-container>
</template>
<script>
import nodeGroupAPI from '@/services/nodegroup'
import nodeAPI from '@/services/node'
import AddOrEditNodeDialog from '@/components/AddOrEditNodeDialog'
import AddNodeGroupDialog from '@/components/AddNodeGroupDialog'
import ConfirmDialog from '@/components/ConfirmDialog'
import { getErrorMsg } from '@/shared/helpers'

export default {
  name: 'Nodes',
  components: {
    'add-or-edit-node-dialog': AddOrEditNodeDialog,
    'add-node-group-dialog': AddNodeGroupDialog,
    'confirm-dialog': ConfirmDialog,
  },
  data: () => ({
    loading: { initial: true, deletingNode: {}, deletingNodeGroup: {} },
    nodeGroups: [],
    addOrEditNodeDialog: false,
    // selectedNode is present when we edit the node
    addOrEditNodeDialogSelectedNode: null,
    // selectedGroup is present when we add or edit the node --> we pass it when
    // we edit the node because our node serializer only returns nodegroup PK
    addOrEditNodeDialogSelectedGroup: null,
    addNodeGroupDialog: false,
    addNodeGroupDialogKey: 0,
    confirmDialog: false,
    confirmText: '',
    showPassword: {},
  }),
  created: function() {
    this.fetchNodeGroups(true);
  },
  methods: {
    fetchNodeGroups: async function(initial=false) {
      this.loading.initial = true
      try {
        const data = await nodeGroupAPI.fetchNodeGroups();
        this.nodeGroups = data.results;
        if (initial) {
          for (const nodeGroup of this.nodeGroups) {
            // need to make object keys reactive through 'set'
            this.$set(this.loading.deletingNodeGroup, nodeGroup.slug, false);
            for (const node of nodeGroup.nodes) {
              // need to make object keys reactive through 'set'
              this.$set(this.showPassword, node.slug, false);
              this.$set(this.loading.deletingNode, node.slug, false);
            }
          }
        }
      } catch(error) {
        this.$toasted.error('Failed to fetch node groups');
      }
      this.loading.initial = false
    },
    showAddOrEditNodeDialog: function(node, group) {
      this.addOrEditNodeDialogSelectedNode = node;
      this.addOrEditNodeDialogSelectedGroup = group;
      this.addOrEditNodeDialog = true;
    },
    closeAddOrEditNodeDialog: function(refetch) {
      this.addOrEditNodeDialog=false;
      this.addOrEditNodeDialogSelectedGroup=null;
      this.addOrEditNodeDialogSelectedNode=null;
      if (refetch) {
        this.fetchNodeGroups();
      }
    },
    showAddNodeGroupDialog: function() {
      this.addNodeGroupDialogKey++;
      this.addNodeGroupDialog = true;
    },
    closeAddNodeGroupDialog: function(refetch) {
      this.addNodeGroupDialog = false;
      if (refetch) {
        this.fetchNodeGroups();
      }
    },

    deleteNode: async function(node) {
      this.loading.deletingNode[node.slug] = true;
      try {
        await nodeAPI.deleteNode(node.slug);
        this.$toasted.success('Node deleted');
      } catch(error) {
        this.$toasted.error(getErrorMsg(error));
      }
      this.loading.deletingNode[node.slug] = false;

    },

    deleteNodeGroup: async function(nodeGroup) {
      this.loading.deletingNodeGroup[nodeGroup.slug] = true;
      try {
        await nodeGroupAPI.deleteNodeGroup(nodeGroup.slug);
        this.$toasted.success('Node group deleted');
      } catch(error) {
        this.$toasted.error(getErrorMsg(error));
      }
      this.loading.deletingNodeGroup[nodeGroup.slug] = false;
    },
    showConfirmDialog: function(action, element) {
      const actions = {
        'node-delete': {
          text: `Are you sure you want to delete node '${element.name}'?`,
          fn: this.deleteNode.bind(this, element),
        },
        'nodegroup-delete': {
          text: `Are you sure you want to delete node group '${element.name}'?`,
          fn: this.deleteNodeGroup.bind(this, element),
        },

      };
      action = actions[action];
      this.confirmText = action['text'];
      this.confirmDialog = true;
      this.confirmAction = action['fn'];
    },
    closeConfirmDialog: function() {
      this.confirmDialog = false;
      this.confirmText = '';
    },
    executeConfirmedAction: async function() {
      // make sure confirmAction finishes before refetching is called
      await this.confirmAction();
      this.fetchNodeGroups();
    },
  },
}
</script>
<style scoped>
.primary-color {
  color: #e5dd00;
}
</style>
