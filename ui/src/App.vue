<template>
  <v-app id="inspire">
    <v-navigation-drawer
      v-model="drawer"
      app
      clipped
      style="background-color: rgba(37,37,37,0.8);"
    >
      <v-list dense>
        <v-list-item-group v-model="selectedMenu">
          <v-list-item link v-for="item in menu" v-bind:key="item.name" @click="$router.push(item.route)">
            <v-list-item-action>
              <v-icon>{{ item.icon }}</v-icon>
            </v-list-item-action>
            <v-list-item-content>
              <v-list-item-title>{{ item.name }}</v-list-item-title>
              <v-list-item-subtitle v-if="item.hasOwnProperty('subtitle')">{{ item.subtitle }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
        </v-list-item-group>
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
            alt="netsocadmin3 logo"
            class="shrink mr-2"
            contain
            src="img/logo/nsa-white.svg"
            transition="scale-transition"
            width="90"
            height="42"
            @click="$router.push('/')"
            style="cursor: pointer"
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
        <a href="https://www.facebook.com/NetsocUCC/" class="ml-1">
          <v-icon>
            mdi-facebook
          </v-icon>
        </a>
        <a href="https://twitter.com/UCCNetsoc" class="ml-1">
          <v-icon>
            mdi-twitter
          </v-icon>
        </a>
        <a href="https://github.com/UCCNetsoc" class="ml-1">
          <v-icon>
            mdi-microsoft-github
          </v-icon>
        </a>
        <a href="https://www.instagram.com/uccnetsoc/" class="ml-1">
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

export default Vue.extend({
  name: 'App',
  components: { },

  data: () => ({
    drawer: true,
    selectedMenu: 0,
    menu: [
      { icon: 'mdi-account-circle', name: 'Account', route: '/account' },
      { icon: 'mdi-lifebuoy', name: 'Getting Started', route: '/getting-started' },
      { icon: 'mdi-backup-restore', name: 'Backups', route: '/backups' },
      { icon: 'mdi-cloud', name: 'Cloud', route: '/cloud' },
      { icon: 'mdi-database', name: 'Databases', route: '/databases' },
      { icon: 'mdi-gamepad-square', name: 'Games', route: '/games' },
      { icon: 'mdi-web', name: 'Websites', route: '/websites' },
      { icon: 'mdi-help-circle', name: 'Help', route: '/help' },
      { icon: 'mdi-alert', name: 'Status', route: '/status' },
      { icon: 'mdi-information', name: 'About & Contributors', route: '/about' }
    ]
  }),

  created () {
    this.$vuetify.theme.dark = true

    // TODO: fixed

    let i = 0
    for (const item of this.menu) {
      console.log(this.$router.currentRoute, item.route)
      // if (this.$router.currentRoute === item.route) {
      //   this.selectedMenu = i
      //   break
      // }

      i++
    }
  }
})
</script>
