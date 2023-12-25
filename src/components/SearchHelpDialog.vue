<template>
  <v-row justify="center">
    <v-dialog
      v-model="dialogWrapper"
      max-width="900px"
      @click:outside="$emit('close')"
    >
      <v-card>
        <v-card-title style="border-bottom: 4px double rgba(255, 255, 255, 0.22)">
          <span class="text-h5 primary-color">Search explanation</span>
        </v-card-title>
        <v-card-text class="pt-5">
        The following types of search are supported:
        <ul class="py-3">
            <li class="mb-2"><strong>block hash</strong>
              <p class="mb-0">can also search for reorged block hashes.</p>
            </li>
            <li class="mb-2"><strong>height</strong>
              <p class="mb-0">searches on the current main chain.</p>
            </li>
            <li class="mb-2"><strong>kernel</strong>
              <p class="mb-0">can also search for reorged kernels, if multiple exists the block on the main chain will be shown.</p>
            </li>
            <li class="mb-2"><strong>output</strong>
              <p class="mb-0">can also search for reorged outputs, if multiple exists the block on the main chain will be shown.</p>
            </li>
            <li class="mb-2"><strong>computation</strong>
              <p class="mb-0">computation is a search which starts with one of keywords <strong>'inputs'</strong>,
                <strong>'outputs'</strong> or <strong>'kernels'</strong>, followed by one of operators <strong>'=', '&lt;', '&gt;', '&lt;=', '&gt;='</strong>,
                followed by a value. Between each of these there must be a single space (eg. <strong>'inputs > 2'</strong>).
                A computation can also be multiple such computations separated by a comma and whitespace (eg. <strong>'inputs > 2, kernels = 3'</strong>)
                in which case an AND is made between them.
              </p>
            </li>
            <li class="mb-2"><strong>reorgs</strong>
              <p class="mb-0">searching for keyword <strong>'reorgs'</strong> will return only blocks where reorgs were spotted.</p>
            </li>
        </ul>
        <p>
          You cannot combine different types of search (eg. 'inputs > 5, reorgs').
        </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            text
            @click="$emit('close')"
            ref="closeBtn"
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
  name: 'SearchHelpDialog',
  props: ['dialog'],
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
        // for some reason close btn is focused so we unfocus it
        if (this.dialogWrapper) {
          setTimeout(() => {
            this.$refs.closeBtn.$el.blur()
          }, 0)
        }
      },
    },
  },
}
</script>
<style scoped>
.primary-color {
  color: #e5dd00;
}
</style>
