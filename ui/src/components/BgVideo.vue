<template>
  <!-- <div></div> -->
  <video v-if="enabled" ref="video" autoplay="autoplay" muted loop :style="{ height: maxHeight, ...additionalStyle }" class="bg">
    <source src="@/assets/bgvideo-orig.mp4" type="video/mp4">
  </video>
</template>

<style scoped>
.bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;

  z-index: 0;
  overflow: hidden;
  opacity: 1;
  object-fit: cover;
  transform: scale(1.4);
  margin: 0;
  padding: 0;
  transition: 0.2s filter;
}
</style>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'BgVideo',
  components: { },
  computed: {
    maxHeight (): string {
      switch (this.$vuetify.breakpoint.name) {
        case 'xs': return 'auto'
        case 'sm': return 'calc(100vh - 140px)'
        case 'md': return 'calc(100vh - 140px)'
        case 'lg': return 'calc(100vh - 140px)'
        case 'xl': return 'calc(100vh - 140px)'
      }

      return 'auto'
    },

    enabled (): boolean {
      switch (this.$vuetify.breakpoint.name) {
        case 'xs': return false
        case 'sm': return true
        case 'md': return true
        case 'lg': return true
        case 'xl': return true
      }

      return true
    }
  },

  props: {
    height: String,
    playbackRate: {
      type: Number,
      default: 0
    },
    additionalStyle: {
      type: Object
    }
  },

  watch: {
    playbackRate: function (newVal: number) {
      (this.$refs.video as HTMLVideoElement).playbackRate = newVal
    }
  }
})
</script>
