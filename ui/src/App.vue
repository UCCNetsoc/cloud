<template>
  <v-app id="inspire">
    <bg-video :playbackRate="bgRate" :additionalStyle="bgStyle" />
    <v-navigation-drawer
      v-model="drawer"
      hide-overlay
      app
      clipped
      style="background-color: rgba(37,37,37,0.8);"
      mini-variant
      v-if="this.$store.state.auth.user !== null"
    >
      <v-list dense>
        <v-list-item-group v-model="selectedMenu">
          <v-list-item
            link
            v-for="item in menu"
            v-bind:key="item.name"
            @click="$router.push(item.route)"
            v-bind:title="item.name"
          >
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

    <v-app-bar app color="primary" dark clipped-left v-if="this.$store.state.auth.user !== null">
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" v-if="drawer == true">
        <v-icon>mdi-close</v-icon>
      </v-app-bar-nav-icon>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" v-else>
        <v-icon>mdi-menu</v-icon>
      </v-app-bar-nav-icon>
      <v-toolbar-title class="ma-0">
        <div>
          <v-img
            alt="logo"
            class="shrink"
            contain
            :src="require('@/assets/cloud-logo.svg')"
            transition="scale-transition"
            aspect-ratio="1"
            width="120"
            height="42"
            @click="gotoLanding()"
            style="cursor: pointer;"
          />
        </div>
      </v-toolbar-title>

      <v-spacer></v-spacer>
      <span style="cursor: pointer; margin-right: 0.125em" v-on:click="$router.push('/account')" class="font-weight-bold">
        <v-icon class="align-center" size="24">
          mdi-account-circle
        </v-icon>
        {{ this.$store.state.auth.user.profile.preferred_username }}
      </span>
      <v-btn text v-on:click="$router.push('/accounts/logout', () => {})">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>
    <v-content>
      <v-slide-y-transition leave-absolute>
        <router-view style="margin-top: -0.5em"></router-view>
      </v-slide-y-transition>
      <v-footer
        app
        style="background-color: rgba(22,22,22,0.80)"
        v-if="this.$store.state.auth.user !== null"
      >
        <small>
          &copy; 2020 UCC Networking Society
          <span> &bull; </span>
          <a
            target="_blank"
            href="https://github.com/UCCNetsoc/cloud"
          >Open Source Software</a>
          <span> &bull; </span>
          <a
            target="_blank"
            href="https://github.com/UCCNetsoc/wiki/blob/master/services/terms-of-service.md"
          >Terms of Service</a>
        </small>
        <v-spacer></v-spacer>
        <a href="https://discord.netsoc.co" class="ml-1">
          <v-icon>mdi-discord</v-icon>
        </a>
        <!-- mdi-github is broken :( gotta workaround -->
        <a
          href="https://github.com/UCCNetsoc"
          class="ml-1"
          style="padding-bottom: 7px; display:block; border-bottom: 2px solid white"
        >
          <v-img
            width="24"
            height="24"
            src="@/assets/github.svg"
            style="margin-bottom: -4px; margin-top: 4px;"
          />
        </a>
        <a href="https://twitter.com/UCCNetsoc" class="ml-1">
          <v-icon>mdi-twitter</v-icon>
        </a>
        <a href="https://www.instagram.com/uccnetsoc/" class="ml-1">
          <v-icon>mdi-instagram</v-icon>
        </a>
        <a href="https://www.facebook.com/NetsocUCC/" class="ml-1">
          <v-icon>mdi-facebook</v-icon>
        </a>
      </v-footer>
    </v-content>
    <message-dialog :visible="msg.length > 0" @okay="msg = ''">
      {{ msg }}
    </message-dialog>
  </v-app>
</template>

<style scoped>
footer a {
  color: white;
}
</style>

<script lang="ts">
import Vue from 'vue'
import BgVideo from '@/components/BgVideo.vue'
import MessageDialog from '@/components/MessageDialog.vue'

interface BgStyle {
  filter: string;
}

export default Vue.extend({
  name: 'App',
  components: {
    BgVideo,
    MessageDialog
  },

  data: () => ({
    msg: '',
    drawer: false,
    selectedMenu: 0,
    menu: [
      { icon: 'mdi-home', name: 'Home', route: '/' },
      { icon: 'mdi-information', name: 'About', route: '/about' },
      { icon: 'mdi-account-circle', name: 'Account', route: '/account' },
      { icon: 'mdi-server', name: 'Instances', route: '/instances' },
      // { icon: 'mdi-console-line', name: 'Terminal', route: '/terminal' },
      { icon: 'mdi-lifebuoy', name: 'Tutorial', route: '/tutorial' },
      { icon: 'mdi-book', name: 'Wiki', route: '/wiki' }
    ]
  }),

  methods: {
    gotoLanding () {
      this.drawer = false
      if (this.$route.path !== '/') {
        this.$router.push('/')
      }
    }
  },

  computed: {
    bgStyle (): BgStyle {
      if (this.$route.path === '/') {
        return { filter: '' }
      } else {
        return {
          filter: 'brightness(0.4)'
        }
      }
    },

    bgRate (): number {
      if (this.$route.path === '/') {
        return 1
      } else {
        return 0
      }
    }
  },

  created () {
    this.$vuetify.theme.dark = true
  },

  updated () {
    let i = 0
    for (const item of this.menu) {
      if (this.$route.path === item.route) {
        this.selectedMenu = i
      }

      i++
    }

    if (this.selectedMenu !== 0) {
      this.drawer = true
    } else {
      // Hide drawer if we're on a non-menu page
      this.drawer = false
    }
  }
})
</script>
