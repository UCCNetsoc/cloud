<template>
  <v-container fill-height fluid>
    <password-set-dialog :visible="true" @successful="$router.push('/')" @cancelled="$router.push('/')"/>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import PasswordSetDialog from '@/components/PasswordSetDialog.vue'

export default Vue.extend({
  name: 'PasswordSet',
  components: {
    PasswordSetDialog
  }
})
</script>
