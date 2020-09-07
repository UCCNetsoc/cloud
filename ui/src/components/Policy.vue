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
          alt="admin logo"
          class="shrink mr-12"
          contain
          src="@/assets/netsoc-horizontal.svg"
          transition="scale-transition"
          width="600"
          height="32"
        />
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <div class="markdown my-3" v-html="html"></div>
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
  name: 'Policy',
  components: {},

  data: () => ({
    html: 'Loading...'
  }),

  async mounted () {
    try {
      const req = await fetch(this.mdUrl)
      let text = await req.text()

      // Trim preamble if it's present
      if (text.indexOf('---') === 0) {
        const index = text.indexOf('---', 3)

        if (index > 0) {
          text = text.substring(index + 3, text.length)
        }
      }

      this.html = marked(text)
    } catch (err) {
      this.html = `Could not fetch policy! ${err}`
    }
  },

  props: {
    visible: Boolean,
    mdUrl: String
  }
})
</script>
