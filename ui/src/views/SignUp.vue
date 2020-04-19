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
          <sign-up-form />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import DialogLogo from '../components/DialogLogo.vue'
import SignUpForm from '../components/SignUpForm.vue'

export default Vue.extend({
  name: 'SignUp',
  components: {
    SignUpForm,
    DialogLogo
  },

  data: () => ({
    visible: true,
    tabs: undefined
  })

})
</script>
