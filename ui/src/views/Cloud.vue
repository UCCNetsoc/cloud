<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-card>
          <v-container fluid class="d-flex flex-xs-wrap flex-sm-wrap flex-md-nowrap py-2">
            <v-card flat>
              <v-card-title>
                Cloud
              </v-card-title>
              <v-card-subtitle>
                Provision instances on demand
              </v-card-subtitle>
              <v-card-text>
                <p>
                  An instance is a <b>Container</b> or <b>Virtual Private Server (VPS)</b> which is the running form of one of our pre-configured templates<br/><br/>
                </p>
                <p>
                  <a>Need help?</a><br>
                  Follow the <a v-on:click="$router.push('/tutorial')">Tutorial</a> page to setup your first website using Netsoc Cloud
                </p>
              </v-card-text>
            </v-card>
            <v-divider vertical class="hidden-sm-and-down"/>
            <v-card flat>
              <v-card-title>
                <b>Keeping your instance running</b>
              </v-card-title>
              <v-card-text>
                <h3>Containers</h3>
                <p>
                  <b class="warning--text">Shutdown if you don't mark them active at least every 90 days.</b><br/>
                  <b class="red--text">Removed if you don't mark them active at least every 150 days</b><br/>
                </p>

                <br/><br/>
                <h3>Virtual Private Servers</h3>
                <p>
                  <b class="warning--text">Shutdown if you don't mark them active at least every 30 days.</b><br/>
                  <b class="red--text">Removed if you don't mark them active at least every 120 days</b><br/>
                </p>
              </v-card-text>
            </v-card>
            <v-divider vertical class="hidden-sm-and-down"/>
            <v-card flat>
              <v-card-title>
                <b>Using your own custom domain</b>
              </v-card-title>
              <v-card-text>
                <p>
                  If you have purchased your own custom domain, there are extra steps you must perform.<br/><br/>
                  You must add the records shown below to the DNS zone of the domain you wish to use,<br/>replace <code>mydomain.com</code> with the domain/subdomain you are using
                </p>
                <p>
                  <code>mydomain.com</code><code>A</code> <code>84.39.234.51</code> <br>
                  <code>mydomain.com</code><code>A</code> <code>84.39.234.50</code> <br>
                  <code>_netsoc</code><code>TXT</code> <code>{{ $store.state.auth.user.profile.preferred_username }}</code>
                </p>
                <p>
                  Once these records have been added, we can verify that you possess the domain.
                  It may take up to 24hrs for any changes in DNS records you make to be updated.
                </p>
                <p>
                  Your domain registrar will have tutorials for adding these records.<br/>
                  If you are having trouble with this and want help, please contact us on our Discord
                </p>
              </v-card-text>
            </v-card>
            <v-divider vertical class="hidden-sm-and-down"/>
            <!-- <v-card flat>
              <v-card-title>
                <b>Installing Software</b>
              </v-card-title>
              <v-card-text>
                <p>
                  We can automate the installation of some software such as WordPress.<br/><br />
                  To first install software your website directory must be empty except for the config file <code>netsoc.json</code> (dont delete this!).<br/>
                  If you have just created your website, you will able to install software right away<br/>
                </p>
                <p>
                  The <a v-on:click="$router.push('/tutorial')">Tutorial</a> page covers a WordPress installation
                </p>
              </v-card-text>
            </v-card> -->
          </v-container>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="12" align="stretch">
        <v-card>
          <v-card-title>
            Containers
          </v-card-title>
          <v-card-subtitle>
            A container is a lightweight instance that can run almost all software and web services
          </v-card-subtitle>
          <cloud-instances-list type="lxc" typeName="container" />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="12" align="stretch">
       <v-card>
          <v-card-title>
            Virtual Private Server (VPS)
          </v-card-title>
          <v-card-subtitle>
            A virtual private server instance is a complete emulation of a server. A VPS is required if you need to use Docker / LXD or Linux kernel tools
          </v-card-subtitle>
          <cloud-instances-list type="vps" typeName="vps" />
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import CloudInstancesList from '@/components/CloudInstancesList.vue'

export default Vue.extend({
  name: 'Websites',
  components: {
    CloudInstancesList
  },

  data: () => ({
  })
})
</script>
