<template>
  <v-container fluid class="d-flex justify-space-around">
    <v-dialog
      v-model="visible"
      width="460"
      persistent
      :fullscreen="$vuetify.breakpoint.mdAndDown"
      class="ma-4"
      scrollable
    >
      <v-card>
        <dialog-logo/>
        <v-card-text class="my-2">
          <p class="my-2 text-center">
            {{ text }}
          </p>
          <v-card-actions class="justify-center">
            <v-btn v-on:click="visible = false" color="green">Okay</v-btn>
          </v-card-actions>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import Config from '../config'

export default Vue.extend({
  name: 'SignUpVerify',
  components: {},

  mounted: () => {
    fetch(`${Config.accountApiBaseUrl}/accounts/signup/verify/${this.$route.params.verify_jew}`, {
      method: 'POST'
    }).then((res: Response) => {
      switch (res.status) {
        case 201: {
          this.visible = true
          this.text = 'Successfully verified account, you can now login'
        }
      }
    })
      .catch((reason) => {
        this.visible = true
        this.text = 'Could not verify your account. An unexpected error happened'
      })
  },

  data: () => ({
    visible: false,
    text: ''
  })
})
</script>
