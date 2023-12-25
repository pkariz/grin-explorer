<template>
  <v-row justify="center">
    <v-dialog
      v-model="dialog"
      persistent
      max-width="600px"
    >
      <v-card>
        <v-card-title style="border-bottom: 4px double rgba(255, 255, 255, 0.22)">
          <span class="text-h5">Add node group</span>
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
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="form.name"
                    :error-messages="errors"
                    prepend-icon="mdi-account"
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
                    prepend-icon="mdi-account"
                    label="Slug"
                    hint="Leave empty for automatic slug creation"
                  ></v-text-field>
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
                  >Add</v-btn
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

export default {
  name: 'AddNodeGroup',
  props: ['dialog'],
  data: () => ({
    form: {
      name: '',
      slug: null,
    },
    loading: { submit: false },
  }),
  methods: {
    addNodeGroup: async function() {
      this.loading.initial = true
      try {
        await nodeGroupAPI.addNodeGroup(this.form);
        this.$toasted.success('Node group created');
        this.$emit('created');
      } catch(error) {
        this.$toasted.error('Failed to fetch node groups');
      }
      this.loading.initial = false
    },
    onSubmit: function() {
      this.loading.submit = true;
      nodeGroupAPI.addNodeGroup(this.form)
        .then(() => {
          this.$toasted.success('Node group created');
          this.$emit('created');
        })
        .catch(() => {
          this.$toasted.error('Invalid data');
        })
        .finally(() => {
          this.loading.submit = false;
        });
    },
  },
}
</script>
