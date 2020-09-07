<template>
  <v-container fill-height fluid>
    <sign-up-verify-dialog @successful="$router.push('/')" @cancelled="$router.push('/')" :visible="true"/>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import SignUpVerifyDialog from '@/components/SignUpVerifyDialog.vue'

export default Vue.extend({
  name: 'SignUpVerify',
  components: {
    SignUpVerifyDialog
  }
})
</script>
