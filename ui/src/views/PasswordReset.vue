<template>
  <v-container fill-height fluid>
    <password-reset-dialog :visible="true" @successful="$router.push('/')" @cancelled="$router.push('/')"/>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import PasswordResetDialog from '@/components/PasswordResetDialog.vue'

export default Vue.extend({
  name: 'PasswordReset',
  components: {
    PasswordResetDialog
  }
})
</script>
