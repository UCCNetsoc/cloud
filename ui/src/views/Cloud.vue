<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-card>
          <v-container fluid class="d-flex flex-xs-wrap flex-sm-wrap flex-md-nowrap py-2">
            <v-card flat>
              <v-card-title>
                Instances
              </v-card-title>
              <v-card-subtitle>
                An instance is a remote virtualized machine that you can run whatever software you want on
              </v-card-subtitle>
              <v-card-text>
                <h3>How To Guides</h3>
                <a target="_blank" href="https://tutorial.netsoc.co">Tutorial (for Beginners!)</a>
                <br/>
                <a target="_blank" href="https://wiki.netsoc.co">Setup a blog using WordPress / Ghost CMS</a>
                <br/>
                <a target="_blank" href="https://wiki.netsoc.co">Connect to your instance over SSH</a>
                <br/>
                <a target="_blank" href="https://wiki.netsoc.co">Setup a static website</a>
                <br/>
                <a target="_blank" href="https://wiki.netsoc.co">Get started using Docker</a>
                <br/>
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
                  <b class="warning--text">Shutdown if you don't keep them marked active at least once every 90 days.</b><br/>
                  <b class="red--text">Removed if you don't mark them active at least once every 180 days</b><br/>
                </p>
                <br/>
                <h3>Virtual Private Servers</h3>
                <p>
                  <b class="warning--text">Shutdown if you don't mark them active at least once every 30 days.</b><br/>
                  <b class="red--text">Removed if you don't mark them active at least once every 120 days</b><br/>
                </p>
              </v-card-text>
            </v-card>
            <!--
            <v-divider vertical class="hidden-sm-and-down"/>
            <v-card flat>
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
          <cloud-instances-list type="lxc" typeName="Container" />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="12" align="stretch">
       <v-card>
          <v-card-title>
            Virtual Private Servers
          </v-card-title>
          <v-card-subtitle>
            A virtual private server (VPS) instance is a complete emulation of a server. A VPS is required if you need to use Docker / LXD or Linux kernel tools
            <p>
              <b class="warning--text">If you request a VPS, there is a very high likelihood of your request being declined if the request reason can be suitably ran inside a container-based workflow.</b>
            </p>
          </v-card-subtitle>
          <cloud-instances-list type="vps" typeName="VPS" />
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
