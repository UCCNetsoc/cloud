<template>
  <v-container fill-height fluid>
    <sign-up-resend-verify-dialog @successful="$router.push('/')" @cancelled="$router.push('/')" :visible="true"/>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import SignUpResendVerifyDialog from '@/components/SignUpResendVerifyDialog.vue'

export default Vue.extend({
  name: 'SignUpResendVerify',
  components: {
    SignUpResendVerifyDialog
  }
})
</script>
