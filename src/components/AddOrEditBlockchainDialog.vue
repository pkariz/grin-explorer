<template>
  <v-row justify="center">
    <v-dialog
      v-model="dialog"
      persistent
      max-width="600px"
    >
      <v-progress-linear
        color="primary"
        indeterminate
        v-if="loading.initial"
      ></v-progress-linear>
      <v-card v-else>
        <v-card-title style="border-bottom: 4px double rgba(255, 255, 255, 0.22)">
          <span class="text-h5">{{ blockchain ? 'Edit blockchain' : 'Add Blockchain' }}</span>
        </v-card-title>
        <v-card-text>
          <v-container>

        <ValidationObserver
          v-slot="{ invalid, validated, handleSubmit }"
        >
          <v-form @submit.prevent="handleSubmit(onSubmit)">
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="name"
                  rules="required"
                  :immediate="blockchain != null"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="form.name"
                    :error-messages="errors"
                    prepend-icon="mdi-text"
                    label="Name"
                    autofocus
                  ></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="slug"
                  :immediate="true"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="form.slug"
                    :error-messages="errors"
                    prepend-icon="mdi-text"
                    label="Slug"
                    hint="Leave empty for automatic slug creation"
                  ></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="group"
                  rules="required"
                  :immediate="blockchain != null"
                  v-slot="{ errors }"
                >
                  <v-select
                    :error-messages="errors"
                    v-model="form.node"
                    :items="nodes"
                    prepend-icon="mdi-desktop-classic"
                    label="Node"
                    item-text="name"
                    item-value="id"
                    hint="Beware, changing nodes can ruin data in some cases"
                  ></v-select>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" class="d-flex d-flex-shrink-1">
                <ValidationProvider
                  name="default"
                  rules="required"
                  :immediate="true"
                  v-slot="{ errors }"
                >
                  <v-checkbox
                    :error-messages="errors"
                    v-model="form.default"
                    label="Default blockchain?"
                    color="primary"
                    required
                  ></v-checkbox>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" class="d-flex d-flex-shrink-1">
                <ValidationProvider
                  name="fetch_price"
                  rules="required"
                  :immediate="true"
                  v-slot="{ errors }"
                >
                  <v-checkbox
                    :error-messages="errors"
                    v-model="form.fetch_price"
                    label="Fetch price?"
                    hint="This should not be checked for testnets and localnets."
                    color="primary"
                    required
                  ></v-checkbox>
                </ValidationProvider>
              </v-col>
            </v-row>
            <br />
            <v-row justify="center" align="center">
              <v-spacer></v-spacer>
              <v-col>
                <v-btn
                  type="submit"
                  color="primary"
                  class="black--text"
                  block
                  :disabled="invalid || !validated"
                  :loading="loading.submit"
                  >{{ blockchain ? 'Save' : 'Add' }}</v-btn
                >
              </v-col>
              <v-spacer></v-spacer>
            </v-row>
          </v-form>
        </ValidationObserver>
          </v-container>
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
import nodeAPI from '@/services/node'
import blockchainAPI from '@/services/blockchain'

export default {
  name: 'AddOrEditBlockchainDialog',
  props: ['dialog', 'blockchain'],
  data: () => ({
    form: {
      name: '',
      slug: null,
      node: null,
      'default': false,
      fetch_price: true,
    },
    loading: { initial: true, submit: false },
    nodes: [],
  }),
  created: function() {
    if (this.blockchain) {
      this.form = {
        name: this.blockchain.name,
        slug: this.blockchain.slug,
        node: this.blockchain.node.id,
        'default': this.blockchain.default,
        fetch_price: this.blockchain.fetch_price,
      }
    }
    this.fetchNodes();
  },
  methods: {
    fetchNodes: async function() {
      this.loading.initial = true
      try {
        const data = await nodeAPI.fetchNodes();
        this.nodes = data.results;
      } catch(error) {
        this.$toasted.error('Failed to fetch nodes');
      }
      this.loading.initial = false
    },
    onSubmit: function() {
      this.loading.submit = true
      if (this.blockchain) {
        blockchainAPI.editBlockchain(this.blockchain.slug, this.form)
          .then(() => {
            this.$toasted.success('Blockchain modified');
            this.$emit('modified');
          })
          .catch(() => {
            this.$toasted.error('Invalid data');
          })
          .finally(() => {
            this.loading.submit = false
          });
      } else {
        blockchainAPI.addBlockchain(this.form)
          .then((blockchain) => {
            this.$toasted.success('Blockchain created');
            this.$emit('created', blockchain.data);
          })
          .catch(() => {
            this.$toasted.error('Invalid data');
          })
          .finally(() => {
            this.loading.submit = false
          });
      }
    },
  },
}
</script>
