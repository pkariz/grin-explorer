<template>
  <v-row justify="center">
    <v-dialog
      v-model="dialog"
      persistent
      max-width="600px"
    >
      <v-card>
        <v-card-title class="error" style="border-bottom: 4px double rgba(255, 255, 255, 0.22)">
          Confirm deletion
        </v-card-title>
        <v-card-text class="pt-5">
          {{ text }}
          <v-row justify="center" align="center" class="pt-5">
            <v-spacer></v-spacer>
            <v-col>
              <v-btn
                color="error"
                block
                :loading="loading"
                @click="callSubmitFn()"
                >Confirm</v-btn
              >
            </v-col>
            <v-spacer></v-spacer>
          </v-row>
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

export default {
  name: 'ConfirmDialog',
  props: ['dialog', 'text', 'loading', 'onsubmit'],
  data: () => ({}),
  methods: {
    callSubmitFn: async function() {
      await this.onsubmit()
      this.$emit('done')
    }
  },
}
</script>
