<template>
  <div>
    <video autoplay="autoplay" muted loop class="meme">
      <source src="@/assets/bgvideo-orig.mp4" type="video/mp4">
    </video>
    <!-- <video autoplay="autoplay" muted loop class="meme2">
      <source src="@/assets/bgvideo-blue.webm" type="video/webm">
    </video> -->
  </div>
</template>

<style scoped>
.meme {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  overflow: hidden;
  opacity: 1;
  object-fit: cover;
  transform: scale(1.2);
  margin: 0;
  padding: 0;
}
</style>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'BgVideo',
  components: { }
})
</script>
