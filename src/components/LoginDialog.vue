<template>
  <v-row justify="center">
    <v-dialog
      v-model="dialog"
      persistent
      max-width="600px"
    >
      <v-card>
        <v-card-title style="border-bottom: 4px double rgba(255, 255, 255, 0.22)">
          <span class="text-h5">Login</span>
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
                  name="username"
                  rules="required"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="username"
                    :error-messages="errors"
                    prepend-icon="mdi-account"
                    label="Username"
                    autofocus
                  ></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="password"
                  rules="required"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    type="password"
                    v-model="password"
                    :error-messages="errors"
                    prepend-icon="mdi-lock"
                    name="password"
                    label="Password"
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
                  >Login</v-btn
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
import { createNamespacedHelpers } from 'vuex'

const { mapActions } = createNamespacedHelpers('auth')

export default {
  name: 'Login',
  props: ['dialog'],
  data: () => ({
    username: '',
    password: '',
  }),
  methods: {
    onSubmit: function() {
      this.login({ username: this.username, password: this.password })
        .then(() => {
          this.$toasted.show('Welcome');
          this.$router.push({ name: 'settings' });
          this.$emit('success');
        })
        .catch(() => {
          this.$toasted.error('Invalid data');
        });
    },
    ...mapActions([
      'login',
    ]),
  },
}
</script>
