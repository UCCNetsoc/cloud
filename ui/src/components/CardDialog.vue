<template>
  <v-dialog
    v-model="visible"
    :width="width"
    persistent
    :fullscreen="$vuetify.breakpoint.mdAndDown"
    class="ma-4"
    scrollable
    :overlay-opacity="0.1"
  >
    <v-card :loading="loading">
      <dialog-logo/>
      <section class="mx-12">
        <slot></slot>
      </section>
    </v-card>
  </v-dialog>
</template>

<script lang='ts'>
import Vue from 'vue'
import DialogLogo from '@/components/DialogLogo.vue'

export default Vue.extend({
  name: 'CardDialog',
  components: {
    DialogLogo
  },

  props: {
    width: String,
    visible: Boolean,
    overlayOpacity: {
      type: String,
      default: '0.5'
    },
    loading: {
      type: Boolean,
      default: false
    }
  }

})
</script>
