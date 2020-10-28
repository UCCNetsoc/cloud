<template>
  <v-container fill-height fluid>
    <cloud-instance-request-dialog :visible="true" @successful="$router.push('/')" @cancelled="$router.push('/')"/>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import CloudInstanceRequestDialog from '@/components/CloudInstanceRequestDialog.vue'

export default Vue.extend({
  components: {
    CloudInstanceRequestDialog
  }
})
</script>
