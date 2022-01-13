<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-card>
          <v-container fluid :class=" this.$vuetify.breakpoint.smAndDown ? '' : 'd-flex flex-xs-wrap flex-sm-wrap flex-md-nowrap py-2'">
            <v-card flat>
              <v-card-title>
                Instances
              </v-card-title>
              <v-card-subtitle>
                An instance is a remote virtualized machine built from a base template
              </v-card-subtitle>
              <v-card-text>
                <h3>Help!</h3>
                <a target="_blank" href="https://tutorial.netsoc.co">Consult the tutorial</a>
                <br/>
              </v-card-text>
            </v-card>
            <v-divider vertical class="hidden-sm-and-down"/>
            <v-card flat>
              <v-card-title>
                <b>Important information about backups, inactivity, resource usage, reliability and uptime</b>
              </v-card-title>
              <v-card-text>
                <p>
                  If your instance goes inactive, it may be <b class="warning--text">shutdown</b> or <b class="error--text">deleted!</b><br/>
                  Remember to take note of the date it goes inactive and remember to renew its activation.
                </p>
                <p>
                  In the interests of server stability, we may change the resource limits on your instance at <b>any</b> time<br/>
                  This could you mean your allocated resources being raised or lowered depending on your use of available resources<br/>
                  In extreme cases, your instance could be <b>shutdown</b> (with longest running instances being the priority in that case)
                </p>
                <p>
                  Instances come by default with a minimal set of resources, you can request more resources via the <b>Upgrade</b> button
                </p>
                <p>
                  <b class="warning--text">
                    We do not typically take backups of instance data nor provide any guarantees of instance uptime, user data integrity or system reliablity
                  </b>
                  <br/>
                  Users should be aware that keeping off-site backups of their data on a personal storage device or making use of an alternative backup solution is recommended
                </p>
                <p>
                  For more information refer to the <a target="_blank" href="https://github.com/UCCNetsoc/wiki/blob/master/services/terms-of-service.md">Terms of Service</a>
                </p>
              </v-card-text>
            </v-card>
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
          <instances-list type="lxc" typeName="Container" />
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
            A virtual private server (VPS) instance is a complete emulation of a server.<br/>A VPS is required if you need to use Linux kernel tools
            <p>
              <b class="warning--text">If you request a VPS, there is a very high likelihood of your request being declined<br/>if the request reason can be suitably ran inside a container-based workflow.</b>
            </p>
          </v-card-subtitle>
          <instances-list type="vps" typeName="VPS" />
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import InstancesList from '@/components/InstancesList.vue'

export default Vue.extend({
  name: 'Websites',
  components: {
    InstancesList
  },

  data: () => ({
  })
})
</script>
