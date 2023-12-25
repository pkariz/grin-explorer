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
          <span class="text-h5">{{ node ? 'Edit node' : 'Add node' }}</span>
        </v-card-title>
        <v-card-text>
          <v-container>
        <ValidationObserver
          v-slot="{ invalid, validated, handleSubmit }"
        >
          <v-form @submit.prevent="handleSubmit(onSubmit)">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-if="node == null"
                  v-model="form.group"
                  prepend-icon="mdi-group"
                  label="Group"
                  readonly
                ></v-text-field>
                <ValidationProvider
                  name="group"
                  rules="required"
                  :immediate="node != null"
                  v-slot="{ errors }"
                  v-else
                >
                  <v-select
                    :error-messages="errors"
                    v-model="form.group"
                    :items="nodeGroups"
                    prepend-icon="mdi-group"
                    label="Group"
                    item-text="name"
                    item-value="slug"
                  ></v-select>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="name"
                  rules="required"
                  :immediate="node != null"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="form.name"
                    :error-messages="errors"
                    prepend-icon="mdi-text"
                    label="Name"
                    :autofocus="node == null"
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
                  name="api url"
                  rules="required"
                  :immediate="node != null"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="form.api_url"
                    :error-messages="errors"
                    prepend-icon="mdi-link"
                    label="Foreign API url"
                  ></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="api username"
                  rules="required"
                  :immediate="node != null"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="form.api_username"
                    :error-messages="errors"
                    prepend-icon="mdi-account"
                    label="API username"
                  ></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="api password"
                  rules="required"
                  :immediate="node != null"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    :type="showPassword ? 'text' : 'password'"
                    v-model="form.api_password"
                    :error-messages="errors"
                    prepend-icon="mdi-lock"
                    :append-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append="showPassword=!showPassword"
                    label="API password"
                  ></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" class="d-flex d-flex-shrink-1">
                <ValidationProvider
                  name="archive"
                  rules="required"
                  :immediate="true"
                  v-slot="{ errors }"
                >
                  <v-checkbox
                    :error-messages="errors"
                    v-model="form.archive"
                    label="Archive node"
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
                  >{{ node ? 'Save' : 'Add' }}</v-btn
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
import nodeGroupAPI from '@/services/nodegroup'
import nodeAPI from '@/services/node'

export default {
  name: 'AddOrEditNodeDialog',
  props: ['dialog', 'group', 'node'],
  data: () => ({
    form: {
      name: '',
      slug: null,
      apiUrl: '',
      apiUsername: '',
      apiPassword: '',
      archive: false,
      group: null,
    },
    showPassword: false,
    loading: { initial: true, submit: false },
    nodeGroups: [],
  }),
  created: function() {
    if (this.node) {
      this.form = {
        name: this.node.name,
        slug: this.node.slug,
        api_url: this.node.api_url,
        api_username: this.node.api_username,
        api_password: this.node.api_password,
        archive: this.node.archive,
      }
    }
    this.fetchNodeGroups();
    this.form.group = this.group.slug;
  },
  methods: {
    fetchNodeGroups: async function() {
      this.loading.initial = true
      try {
        const data = await nodeGroupAPI.fetchNodeGroups();
        this.nodeGroups = data.results;
      } catch(error) {
        this.$toasted.error('Failed to fetch node groups');
      }
      this.loading.initial = false
    },
    onSubmit: function() {
      this.loading.submit = true
      if (this.node) {
        nodeAPI.editNode(this.node.slug, this.form)
          .then(() => {
            this.$toasted.success('Node modified');
            this.$emit('modified');
          })
          .catch(() => {
            this.$toasted.error('Invalid data');
          })
          .finally(() => {
            this.loading.submit = false
          });
      } else {
        nodeAPI.addNode(this.form)
          .then(() => {
            this.$toasted.success('Node created');
            this.$emit('created');
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
