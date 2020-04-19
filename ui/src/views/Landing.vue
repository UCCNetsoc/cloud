<template>
  <v-container>
    <v-dialog
      v-model="visible"
      width="420"
      persistent
      :fullscreen="$vuetify.breakpoint.mdAndDown"
      class="ma-4"
      scrollable
    >
      <v-card>
        <dialog-logo/>
        <v-divider/>
        <v-card-text>
          <what-is-nsa />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import DialogLogo from '../components/DialogLogo.vue'
import WhatIsNsa from '../components/WhatIsNsa.vue'

export default Vue.extend({
  name: 'Landing',
  components: {
    WhatIsNsa,
    DialogLogo
  },

  data: () => ({
    visible: true,
    tabs: undefined
  })

})
</script>
