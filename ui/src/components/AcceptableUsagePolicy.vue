<template>
  <v-dialog
    v-model="visible"
    width="600"
    persistent
    :fullscreen="$vuetify.breakpoint.mdAndDown"
    scrollable
  >
    <v-card flat>
      <v-card-title
        class="headline dark lighten-2 justify-center ma-2"
        primary-title
      >
        <v-img
          alt="netsocadmin3 logo"
          class="shrink mr-12"
          contain
          src="img/logo/netsoc-white.svg"
          transition="scale-transition"
          width="240"
          height="32"
        />
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <div class="my-3" v-html="aupHtml"></div>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions class="justify-center">
        <v-btn
          @click="$emit('accept')"
        >
          Accept
        </v-btn>
        <v-btn
          @click="$emit('decline')"
        >
          Decline
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import Vue from 'vue'
import marked from 'marked'

export default Vue.extend({
  name: 'AcceptableUsagePolicy',
  components: {},

  data: () => ({
    aupHtml: 'Loading...'
  }),

  async created () {
    try {
      const req = await fetch('https://raw.githubusercontent.com/UCCNetsoc/acceptable-usage-policy/master/README.md')
      this.aupHtml = marked(await req.text())
    } catch (err) {
      this.aupHtml = 'Could not fetch Acceptable Usage Policy!'
    }
  },

  props: {
    visible: Boolean
  }
})
</script>
