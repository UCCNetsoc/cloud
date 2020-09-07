<template>
  <v-container fill-height fluid>
    <sign-up-dialog @successful="$router.push('/')" @cancelled="$router.push('/')" :visible="true"/>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import SignUpDialog from '@/components/SignUpDialog.vue'

export default Vue.extend({
  name: 'SignUp',
  components: {
    SignUpDialog
  },

  data: () => ({
    visible: true,
    tabs: undefined
  })

})
</script>
