<template>
  <v-container>
    <card-dialog
      :visible="visible"
      width="430"
      overlay-opacity="0.1"
    >
      <v-card-title class="justify-center text-center white--text font-weight-light">
        what we offer
      </v-card-title>
      <v-divider/>
      <v-card-text style="margin-top: -0.5em; margin-bottom: -0.5em">
        <v-card flat v-for="feature in features" :key="feature.name">
          <v-container>
            <v-row no-gutters justify="start" align="center">
              <v-col>
                <v-avatar
                  size="32"
                  tile
                >
                  <v-icon large>{{ feature.icon }}</v-icon>
                </v-avatar>
              </v-col>
              <v-col sm="10">
                <h3>
                  {{ feature.title }}
                </h3>
                <span>
                  {{ feature.description }}
                </span>
              </v-col>
            </v-row>
          </v-container>
        </v-card>
      </v-card-text>
      <v-divider/>
      <v-card-actions class="justify-center ma-3">
      <v-btn v-on:click="$router.push('/accounts/login', () => {})" color="primary">Login</v-btn>
      <v-btn v-on:click="$router.push('/accounts/sign-up')" color="green">Sign Up</v-btn>
      </v-card-actions>
    </card-dialog>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import CardDialog from '@/components/CardDialog.vue'

export default Vue.extend({
  name: 'LandingDialog',
  components: {
    CardDialog
  },

  props: {
    visible: {
      type: Boolean,
      default: true
    }
  },

  data: () => ({
    features: [
      { icon: 'mdi-web', title: 'Web Services', description: 'Easily deploy a web service with a few clicks. Pre-configured templates include WordPress, Ghost CMS, static hosting and more' },
      { icon: 'mdi-controller-classic', title: 'Gameservers', description: 'Spin up a game server and play games like Minecraft with your friends in seconds' },
      { icon: 'mdi-console-network', title: 'Development Tools', description: 'Boot a container with support for any programming language you can think of' },
      { icon: 'mdi-server-network', title: 'Virtual Private Servers', description: 'Launch a Linux host like Debian / Ubuntu / Arch / CentOS and run tools like Docker, LXD and more' }
    ]
  })
})
</script>
