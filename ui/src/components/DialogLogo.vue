<template>
  <v-card
    flat
    class="binary-background"
  >
    <v-card-title
      class="headline dark lighten-2 justify-center "
      primary-title
    >
      <v-img
        class="shrink"
        contain
        :src="require('@/assets/cloud-logo.svg')"
        transition="none"
        width="160"
        height="64"
      />
    </v-card-title>
  </v-card>
</template>

<style scoped>

@keyframes swipe {
  0%{background-position:0% 50%; filter: invert(0)     }
  50%{background-position:100% 50%;  filter: invert(1) }
  100%{background-position:0% 51%;  filter: invert(0)  }
}

.binary-background {
  background: url("../assets/binary-repeat.png") rgba(22,22,22,1);
  background-size: 45%;

  animation: swipe 45s ease infinite;
  background-repeat: round no-repeat;
}

</style>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'DialogLogo'
})
</script>
