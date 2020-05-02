<template>
  <v-container fill-height fluid v-bind:style="{ maxHeight: this.maxHeight, backgroundColor: 'black' }" >
    <bg-video/>
    <v-dialog
      v-model="visible"
      width="420"
      persistent
      :fullscreen="$vuetify.breakpoint.mdAndDown"
      class="ma-4"
      scrollable
      overlay-opacity="0.65"
    >
      <v-card>
        <dialog-logo/>
        <v-divider/>
        <v-card-text>
          <what-is-nsa />
        </v-card-text>
      </v-card>
    </v-dialog>
    <v-row v-if="!visible" class="my-4 justify-center text-center text-no-wrap">
      <v-col cols="12" sm="12">
        <v-img height="24rem" src="@/assets/netsoc-logo.svg" contain></v-img>
      </v-col>
    </v-row>
    <v-row v-if="!visible" class="justify-center text-center text-no-wrap">
      <v-col cols="12" sm="12">
        <h1 class="font-weight-light display-5" style="position: relative; z-index: 2">New to Linux or Netsoc? Try out our <a>Tutorial</a> to get started</h1>
      </v-col>
    </v-row>
    <v-row v-if="!visible" class="justify-center ma-0 pa-0" fill-height style="width: 100%">
      <v-col cols="12" xl="1" md="2" sm="2" xs="12" class="ma-0 pa-0" v-for="item in menu" v-bind:key="item.name" @click="$router.push(item.route)">
        <v-card class="text-center service" flat>
          <v-card-text class="justify-center" style="padding-left: 0; padding-right: 0">
            <v-icon class="align-center" size="48">{{ item.icon }}</v-icon>
          </v-card-text>
          <v-card-title style="padding-left: 0; padding-right: 0" class="justify-center subtitle-1">
            <p class="nowrap" style="min-width: 999%">{{ item.name }}</p>
          </v-card-title>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.service {
  top: 0;
  transition: 0.4s all;
  cursor: pointer;
  background-color: rgba(0,0,0,0);
  width: 100%;
}

.service:hover {
  top: -24px;
}

</style>

<script lang="ts">
import Vue from 'vue'
import DialogLogo from '../components/DialogLogo.vue'
import WhatIsNsa from '../components/WhatIsNsa.vue'
import BgVideo from '../components/BgVideo.vue'

export default Vue.extend({
  name: 'Landing',
  components: {
    WhatIsNsa,
    DialogLogo,
    BgVideo
  },

  computed: {
    maxHeight (): string {
      switch (this.$vuetify.breakpoint.name) {
        case 'xs': return 'auto'
        case 'sm': return 'calc(100vh - 64px)'
        case 'md': return 'calc(100vh - 64px)'
        case 'lg': return 'calc(100vh - 64px)'
        case 'xl': return 'calc(100vh - 64px)'
      }

      return 'auto'
    },

    visible (): boolean {
      return this.$store.state.auth.user === null
    }
  },

  data: () => ({
    selectedMenu: 0,
    menu: [
      { icon: 'mdi-account-circle', name: 'Account', route: '/account' },
      { icon: 'mdi-lifebuoy', name: 'Tutorial', route: '/tutorial', divider: true },
      { icon: 'mdi-backup-restore', name: 'Backups', route: '/backups' },
      { icon: 'mdi-cloud', name: 'Cloud', route: '/cloud' },
      { icon: 'mdi-database', name: 'Databases', route: '/databases' },
      { icon: 'mdi-gamepad-square', name: 'Games', route: '/games' },
      { icon: 'mdi-web', name: 'Websites', route: '/websites', divider: true },
      { icon: 'mdi-help-circle', name: 'Help', route: '/help' },
      { icon: 'mdi-alert', name: 'Status', route: '/status' },
      { icon: 'mdi-information', name: 'About', route: '/about' }
    ]
  })

})
</script>
