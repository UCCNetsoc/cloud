<template>
  <v-container>
    <v-card class="ma-2" flat>
      <h1 class="text-center white--text font-weight-light pt-1">netsocadmin</h1>
      <h2 class="text-center subtitle-1">our services</h2>
    </v-card>
    <v-divider class="ma-2"/>
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
    <v-divider class="ma-2"/>
    <v-card-actions class="justify-center">
      <v-btn v-on:click="$router.push('/login')" color="primary">Login</v-btn>
      <v-btn v-on:click="$router.push('/signup')" color="green">Sign Up</v-btn>
    </v-card-actions>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'WhatIsNsa',

  data: () => ({
    features: [
      { icon: 'mdi-book', title: 'Blogs', description: 'Launch and host your own blog in seconds' },
      { icon: 'mdi-cloud', title: 'Cloud', description: 'Launch and deploy your own VPS\' and servers on demand' },
      { icon: 'mdi-database', title: 'Database', description: 'MySQL & PostgresSQL on demand' },
      { icon: 'mdi-controller-classic', title: 'Gameservers', description: 'Host Minecraft, Garry\'s Mod, CS:GO, Terraria, FiveM and more' },
      { icon: 'mdi-web', title: 'Websites', description: 'Host your own website at yourname.netsoc.co or use your own custom domain' },
      { icon: 'mdi-speedometer', title: 'Reasonable Quotas', description: 'We won\'t delete your data every year and offer 25-50GB of storage space' }
    ]
  })
})
</script>
