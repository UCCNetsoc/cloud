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
                Provision services and servers on demand
              </v-card-subtitle>
              <v-card-text>
                <p>
                  You can host either a service or Virtual Private Server that's been spawned from a template such as
                  WordPress, Ghost CMS, static hosting and more.
                </p>
                <p>
                  <a>Need help?</a><br>
                  Follow the <a v-on:click="$router.push('/tutorial')">Tutorial</a> page to setup your first website
                </p>
              </v-card-text>
            </v-card>
            <v-divider vertical class="hidden-sm-and-down"/>
            <v-card flat>
              <v-card-title>
                <b>Keeping your service/VPS running</b>
              </v-card-title>
              <v-card-text>
                <h3>Services</h3>
                <p>
                  Your service will expire if you don't mark it active at least every 90 days.
                  We will warn you by email if you have forgotten to do this<br/>
                  <br/>
                  If your service is not marked active after 90 days, we will shut it down
                  If your service is not marked active after 150 days we will remove it from our servers and your data will be lost<br/>
                </p>
                <br/><br/>
                <h3>Virtual Private Servers</h3>
                <p>
                  Your VPS will expire if you don't mark it active at least every 60 days
                  We will warn you by email if you have forgotten to do this<br/>
                  <br/>
                  If your VPS is not marked active after 60 days, we will shut it down
                  If your VPS is not marked active after 120 days, we will remove it from our servers and your data will be lost<br/>
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
            Services
          </v-card-title>
          <v-card-subtitle>
            A service is a lightweight container that can run most software and web services
          </v-card-subtitle>
          <cloud-services-list type="lxc" typeName="service" />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="12" align="stretch">
       <v-card>
          <v-card-title>
            Virtual Private Server
          </v-card-title>
          <v-card-subtitle>
            A virtual private server is a complete emulation of a server. This is required if you need to use Docker / LXD or Linux kernel tools
          </v-card-subtitle>
          <cloud-services-list type="vps" typeName="vps" />
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import CloudServicesList from '@/components/CloudServicesList.vue'

export default Vue.extend({
  name: 'Websites',
  components: {
    CloudServicesList
  },

  data: () => ({
  })
})
</script>
