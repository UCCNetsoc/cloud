<template>
  <v-container>
    <card-dialog
      :visible="visible"
      width="430"
      overlay-opacity="0.1"
    >
      <v-card-title class="justify-center text-center white--text font-weight-light">
        our services
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

      { icon: 'mdi-book', title: 'Blogs', description: 'Launch and host your own blog in minutes' },
      // { icon: 'mdi-cloud', title: 'Cloud', description: 'Launch and deploy your own VPS\' and servers on demand' },
      { icon: 'mdi-database', title: 'Databases', description: 'MySQL on demand' },
      { icon: 'mdi-controller-classic', title: 'Gameservers', description: 'Host Minecraft, Garry\'s Mod, CS:GO, Terraria, FiveM servers and more' },
      { icon: 'mdi-teach', title: 'Mentorships', description: 'Sign up to our mentorships and learn stuff you won\'t see in college' },
      { icon: 'mdi-console', title: 'User Server', description: 'Gain access to portal.netsoc.co, our Linux server offered to all of our members' },
      { icon: 'mdi-web', title: 'Websites', description: 'Host your own website at username.netsoc.co or use your own custom domain' }
    ]
  })
})
</script>
