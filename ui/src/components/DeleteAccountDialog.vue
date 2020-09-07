<template>
  <v-container>
    <card-dialog
      :visible="visible"
      width="460"
      overlay-opacity="0.4"
    >
      <v-card-text class="justify-center text-center">
        To request account deletion, contact netsoc@uccsocieties.ie using the email associated with this account
      </v-card-text>
      <v-card-actions class="justify-center mb-4">
        <v-btn v-on:click="closeResultDialog()" color="green">Okay</v-btn>
      </v-card-actions>
    </card-dialog>
  </v-container>
</template>

<script lang='ts'>
import Vue from 'vue'
import CardDialog from '@/components/CardDialog.vue'

export default Vue.extend({
  name: 'DeleteAccountDialog',
  components: {
    CardDialog
  },

  props: {
    visible: {
      type: Boolean,
      default: true
    }
  },

  methods: {
    closeResultDialog () {
      this.$emit('successful')
    }
  },

  data: () => ({

  })
})

</script>
