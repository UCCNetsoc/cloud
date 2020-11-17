<template>
  <card-dialog
    :visible="visible"
    :width="width"
    :loading="loading"
  >
    <v-card-title class="justify-center text-center white--text font-weight-light">
      {{ title }}
    </v-card-title>
    <v-divider/>
    <v-card-text>
      <slot></slot>
    </v-card-text>
    <v-divider/>
    <v-card-actions class="justify-center ma-3">
      <v-btn :disabled="loading" v-on:click="$emit('confirmed')" color="green">Confirm</v-btn>
      <v-btn v-on:click="$emit('cancelled')" color="red">Cancel</v-btn>
    </v-card-actions>
  </card-dialog>
</template>

<script lang="ts">
import Vue from 'vue'
import CardDialog from '@/components/CardDialog.vue'

export default Vue.extend({
  name: 'CancelConfirmDialog',
  components: {
    CardDialog
  },

  props: {
    visible: {
      type: Boolean,
      default: true
    },

    width: {
      type: String,
      default: '460'
    },

    title: {
      type: String,
      default: 'confirm'
    },

    loading: {
      type: Boolean,
      default: false
    }
  }
})
</script>
