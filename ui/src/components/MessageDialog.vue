<template>
  <card-dialog
    :visible="visible"
    width="420"
  >
    <v-card-text class="my-2 text-center">
      <slot></slot>
    </v-card-text>
    <v-card-actions class="justify-center ma-3">
      <v-btn v-on:click="$emit('okay')" color="green">Okay</v-btn>
    </v-card-actions>
  </card-dialog>
</template>

<script lang="ts">
import Vue from 'vue'
import CardDialog from '@/components/CardDialog.vue'

export default Vue.extend({
  name: 'MessageDialog',
  components: {
    CardDialog
  },

  props: {
    visible: {
      type: Boolean,
      default: true
    }
  }
})
</script>
