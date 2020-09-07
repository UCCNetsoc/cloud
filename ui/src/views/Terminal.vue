<template>
  <v-container fluid style="background-color: rgba(0,0,0,0); overflow: hidden; margin: 0; height: calc(100vh - 102px)">
    <!--
      welcome to canty's spastic way of applying the linux compositor (i.e. transparent terminal) look to an iframe on a different origin
      here is my story:

      opacity: 0.5 - can't see the text for shit, it looks like shit
      inject css and js into the iframe (lol) - violates same origin policy
      fork wetty - easy solution but imagine forking stuff
      try filter() - doesn't have the features
      try background-blend-mode - only works on multiple background-modes
      try mask-composite - only firefox support (https://developer.mozilla.org/en-US/docs/Web/CSS/mask-composite)
      try some weird shit with canvas and make a "green screen" - security sandbox wont let us

      ding ding we have a solution... i lied about filter(), you can make it use the effects inside svg files

      welcome to the arcane technology of svg compositor filters
      these bastards support a full fucking filter pipeline, it's basically xml photoshop
      they're also supported by literally every browser ever

      https://en.wikipedia.org/wiki/SVG_filter_effects

      https://alistapart.com/article/finessing-fecolormatrix/

    -->
    <!-- <svg height="0">
      <defs>
        <filter id="color-replace" color-interpolation-filters="sRGB">
          <feComponentTransfer >
            <feFuncR type="discrete" tableValues="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"/>
            <feFuncG type="discrete" tableValues="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"/>
            <feFuncB type="discrete" tableValues="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"/>
          </feComponentTransfer>

          <feColorMatrix
            type="matrix"
            values="1 0 0 0 0
                    0 1 0 0 0
                    0 0 1 0 0
                    1 1 1 1 -3" result="selectedColor"/>

          <feComposite operator="out" in="SourceGraphic" result="notSelectedColor"/>
          <feFlood flood-color="black" flood-opacity="0"/>
          <feComposite operator="in" in2="selectedColor"/>
          <feComposite operator="over" in2="notSelectedColor"/>
        </filter>
      </defs>
    </svg> -->
    <div class="black"></div>
    <iframe class="frame" :src="url"/>
  </v-container>
</template>

<style scoped>

.black {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  padding: 1000vw;
  background-color: black;
  z-index: 1;
}

.frame {
  position: relative;
  z-index: 2;
  width: 100%;
  height: calc(100vh - 148px);
  margin-top: 20px;
  margin-right: 20px;
  border: none;
  opacity: 1;
  /* filter: url(#color-replace); */
  background-color: rgba(0,0,0,0);
}
</style>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'Terminal',
  components: {
  },

  computed: {
    url (): string {
      return `http://portal.netsoc.co/wetty/ssh/${this.$store.state.auth.user.profile.preferred_username}`
    }
  },

  data: () => ({
  })
})
</script>
