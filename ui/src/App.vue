<template>
  <v-app id="inspire">
    <v-navigation-drawer
      v-model="drawer"
      app
      clipped
    >
      <v-list dense>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-account-circle</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Account</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-lifebuoy</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Getting Started</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-backup-restore</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Backups</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-cloud</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Cloud</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-database</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Databases</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-web</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Deploy</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-gamepad-square</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Games</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-help-circle</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Help</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-alert</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Status</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-information</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>About &amp; Contributors</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar
      app
      color="primary"
      dark
      clipped-left
    >
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" v-if="drawer == true">
        <v-icon>
          mdi-close
        </v-icon>
      </v-app-bar-nav-icon>
       <v-app-bar-nav-icon @click.stop="drawer = !drawer" v-else>
        <v-icon>
          mdi-menu
        </v-icon>
      </v-app-bar-nav-icon>
      <v-toolbar-title>
        <div class="d-flex align-center">
          <v-img
            alt="Vuetify Logo"
            class="shrink mr-2"
            contain
            src="img/logo/nsa-white.svg"
            transition="scale-transition"
            width="90"
          />
        </div>
      </v-toolbar-title>

      <v-spacer></v-spacer>
      <v-btn text>
        <v-icon>mdi-exit-to-app</v-icon>
      </v-btn>
    </v-app-bar>

    <v-content>
      <router-view></router-view>
      <v-footer app>
        <span>&copy; 2020 UCC Networking Society</span>
        <v-spacer></v-spacer>
          <a href="https://www.facebook.com/NetsocUCC/">
            <v-icon>
              mdi-facebook
            </v-icon>
          </a>
          <a href="https://twitter.com/UCCNetsoc">
            <v-icon>
              mdi-twitter
            </v-icon>
          </a>
          <a href="https://github.com/UCCNetsoc">
            <v-icon>
              mdi-github
            </v-icon>
          </a>
          <a href="https://www.instagram.com/uccnetsoc/">
            <v-icon>
              mdi-instagram
            </v-icon>
          </a>
      </v-footer>
    </v-content>
  </v-app>
</template>

<script lang="ts">
import Vue from 'vue'

import HelloWorld from './components/HelloWorld.vue'

export default Vue.extend({
  name: 'App',

  components: { },

  data: () => ({
    drawer: true
  }),

  created () {
    this.$vuetify.theme.dark = true
  }
})
</script>
