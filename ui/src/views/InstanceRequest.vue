<template>
  <v-container fill-height fluid>
    <instance-request-dialog :visible="true" @successful="$router.push('/')" @cancelled="$router.push('/')"/>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import InstanceRequestDialog from '@/components/InstanceRequestDialog.vue'

export default Vue.extend({
  components: {
    InstanceRequestDialog
  }
})
</script>
