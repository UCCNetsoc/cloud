<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-data-table
            :loading="loading"
            :headers="headers"
            :items="websites"
            :items-per-page="20"
            style="margin-top: -1rem"
          >
            <template slot="no-data">
              {{ empty }}
            </template>

            <template v-slot:item="row">
              <tr>
                <td>
                  {{row.item.name}}
                </td>
                <td>
                  <p v-for="host in row.item.config.hosts" :key="host" class="ma-0">
                    {{host}}
                    <v-btn
                      icon
                      style="line-height: 16px;"
                      @click="popConfirmCancel(ConfirmCancelMode.RemoveHost, { name: row.item.name, host })"
                    >
                      <v-icon>
                        mdi-delete
                      </v-icon>
                    </v-btn>
                  </p>
                  <v-btn icon @click="popConfirmCancel(ConfirmCancelMode.AddHost, { name: row.item.name })">
                    <v-icon>
                      mdi-plus
                    </v-icon>
                  </v-btn>
                </td>
                <td>
                  {{row.item.root}}
                </td>
                <td :style="{ color: row.item.valid ? 'green' : 'red', fontWeight: 'bold' }">
                  {{row.item.valid ? "Valid" : "Invalid"}}
                </td>
                <td>
                  <div v-for="remark in row.item.remarks" :key="remark">
                    {{ remark }}
                  </div>
                </td>
                <td>
                  <p v-if="row.item.software != 'not-installed'">
                    {{row.item.software}}
                    <v-btn
                      v-if="!(['unknown', 'not-installed'].includes(row.item.software))"
                      icon
                      @click="popConfirmCancel(ConfirmCancelMode.UninstallSoftware, { name: row.item.name })"
                    >
                      <v-icon>
                        mdi-delete
                      </v-icon>
                    </v-btn>
                  </p>
                  <v-btn
                    v-else
                    icon
                    @click="popConfirmCancel(ConfirmCancelMode.InstallSoftware, { name: row.item.name })"

                  >
                    <v-icon>
                      mdi-plus
                    </v-icon>
                  </v-btn>
                </td>
                <td style="text-align: right">
                  <v-btn
                    icon
                    @click="popConfirmCancel(ConfirmCancelMode.RemoveWebsite, { name: row.item.name })"
                  >
                    <v-icon>
                      mdi-delete
                    </v-icon>
                  </v-btn>
                </td>
              </tr>
            </template>

          </v-data-table>
      </v-col>
    </v-row>
    <v-row class="center ml-1" style="margin-top: -1em">
      <v-col class="d-flex  justify-end" cols="12" sm="12">
        <v-btn @click="popConfirmCancel(ConfirmCancelMode.AddWebsite, { })" icon>
          <v-icon>
            mdi-plus
          </v-icon>
        </v-btn>
        <v-btn @click="uiReloadWebsites()" icon>
          <v-icon>
            mdi-refresh
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
    <message-dialog :visible="msg.length > 0" @okay="msg = ''">
      {{ msg }}
    </message-dialog>
    <confirm-cancel-dialog
      :title="confirmCancel.mode"
      :visible="confirmCancel.mode !== ConfirmCancelMode.Hidden"
      :loading="confirmCancel.loading"
      @confirmed="confirm()"
      @cancelled="cancel()"
      class="confirmCancel"
    >
      <v-form
        v-if="confirmCancel.mode == ConfirmCancelMode.AddWebsite"
        lazy-validation
        ref="form"
        @submit="confirm()"
      >
        <v-text-field
          label='Name'
          :rules='websiteNameRules'
          v-model='confirmCancel.action.name'
        ></v-text-field>
      </v-form>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.RemoveWebsite">
        Are you sure you want to remove the website?<br>
        This action is unrecoverable and will remove ALL data associated with the website including it's software!
      </p>
      <v-form
        v-else-if="confirmCancel.mode == ConfirmCancelMode.AddHost"
        lazy-validation
        ref="form"
        @submit="confirm()"
      >
        <v-text-field
          label='Host'
          v-model='confirmCancel.action.host'
          :rules='websiteHostRules'
          :placeholder='$store.state.auth.user.profile.preferred_username+".netsoc.co"'
        ></v-text-field>
      </v-form>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.RemoveHost">
        Are you sure you want to remove the host?
      </p>
      <v-form
        v-else-if="confirmCancel.mode == ConfirmCancelMode.InstallSoftware"
        lazy-validation
        ref="form"
        @submit="confirm()"
      >
        <v-select
          :items='softwareList'
          label='Software'
          outlined
          v-model='confirmCancel.action.software'
          class="mt-4"
          style="margin-bottom: -1.5em"
        ></v-select>
      </v-form>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.UninstallSoftware">
        Are you sure you want to uninstall the software?<br>
        This action is unrecoverable and will remove ALL data associated with the software!
      </p>
    </confirm-cancel-dialog>
  </v-container>
</template>

<style scoped>
.confirmCancel p {
  text-align: center !important;
}
</style>

<script lang='ts'>
import ConfirmCancelDialog from '@/components/ConfirmCancelDialog.vue'
import MessageDialog from '@/components/MessageDialog.vue'

import { config } from '@/config'
import { fetchRest } from '@/api/rest'
import { openApiGetSchemaProperty, openApiPropertyValidator } from '@/api/openapi'

import Vue from 'vue'

interface Websiteconfig {
  Hosts: { [host: string]: {} };
  Runtime: string;
}

interface Website {
  name: string;
  root: string;
  owner: string;
  config: Websiteconfig;
  valid: boolean;
  remarks: string[];
  software: string;
}

enum ConfirmCancelMode {
  Hidden = '-',
  InstallSoftware = 'install software',
  UninstallSoftware = 'uninstall software',
  AddWebsite = 'add website',
  RemoveWebsite = 'remove website',
  AddHost = 'add host',
  RemoveHost = 'remove host'
}

interface ConfirmCancelAction {
  name?: string;
  host?: string;
  software?: string;
}

export default Vue.extend({
  name: 'WebsitesList',
  components: {
    ConfirmCancelDialog,
    MessageDialog
  },

  computed: {
    required () {
      return [
        (v: string) => !!v || 'Required'
      ]
    },

    websiteNameRules () {
      return [
        (v: string) => !!v || 'Website name required',
        openApiPropertyValidator(openApiGetSchemaProperty('Website', 'name'))
      ]
    },

    websiteHostRules () {
      return [
        (v: string) => !!v || 'Website host required'
      ]
    }
  },

  methods: {
    async confirm () {
      // Extract username from profile
      const username = this.$store.state.auth.user.profile.preferred_username
      const headers = {
        Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
      }

      // Extract action
      const { name, host, software } = this.confirmCancel.action

      this.confirmCancel.loading = true
      try {
        switch (this.confirmCancel.mode) {
          case ConfirmCancelMode.AddWebsite: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/websites/${username}/${name}`, {
                method: 'POST',
                headers
              })

            this.msg = 'Website created successfully!'
            break
          }

          case ConfirmCancelMode.RemoveWebsite: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/websites/${username}/${name}`, {
                method: 'DELETE',
                headers
              })

            this.msg = 'Website deleted successfully!'
            break
          }

          case ConfirmCancelMode.AddHost: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/websites/${username}/${name}/host/${host}`, {
                method: 'POST',
                headers
              })

            this.msg = 'Added host successfully!'
            break
          }

          case ConfirmCancelMode.RemoveHost: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/websites/${username}/${name}/host/${host}`, {
                method: 'DELETE',
                headers
              })

            this.msg = 'Removed host successfully!'
            break
          }

          case ConfirmCancelMode.InstallSoftware: {
            console.log(username)
            await fetchRest(
              `${config.apiBaseUrl}/v1/websites/${username}/${name}/software/${software}`, {
                method: 'POST',
                headers,
                body: JSON.stringify({})
              })

            this.msg = 'Software installed successfully!'
            break
          }

          case ConfirmCancelMode.UninstallSoftware: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/websites/${username}/${name}/software`, {
                method: 'DELETE',
                headers
              })

            this.msg = 'Software uninstalled successfully!'
            break
          }
        }
      } catch (e) {
        this.msg = e.message
      } finally {
        this.confirmCancel.loading = false
        this.confirmCancel.mode = ConfirmCancelMode.Hidden
        this.uiReloadWebsites()
      }
    },

    async cancel () {
      this.confirmCancel.loading = false
      this.confirmCancel.mode = ConfirmCancelMode.Hidden
    },

    async uiReloadWebsites () {
      this.loading = true
      this.websites = []

      try {
        console.log(config)
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/websites/${this.$store.state.auth.user.profile.preferred_username}`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.loading = false
        const websites: { [name: string]: Website } = await res.json()
        this.websites = Object.values(websites)

        if (this.websites.length === 0) {
          this.empty = 'You have no websites, try adding one!'
        }
      } catch (e) {
        this.loading = false
        this.websites = []
        this.empty = e.message
      }
    },

    async popConfirmCancel (mode: ConfirmCancelMode, action: ConfirmCancelAction) {
      this.confirmCancel.action = action
      this.confirmCancel.mode = mode
    }
  },

  data () {
    const websites: Website[] = []
    const action: ConfirmCancelAction = {}

    return {
      ConfirmCancelMode, // Needed to use the enum in the rendered template
      loading: true,
      empty: '',
      msg: '',
      websites: websites,

      confirmCancel: {
        mode: ConfirmCancelMode.Hidden,
        loading: false,
        action
      },

      softwareList: [
        'wordpress',
        'php-info'
      ],

      headers: [
        { text: 'Name', value: 'name' },
        { text: 'Hosts', value: 'hosts' },
        { text: 'Root', sortable: false, value: 'root' },
        { text: 'Status', sortable: false, value: 'valid ' },
        { text: 'Remarks', sortable: false, value: 'remarks' },
        { text: 'Software', sortable: false, value: 'software' },
        { text: 'Actions' }
      ]
    }
  },

  mounted () {
    this.uiReloadWebsites()
  }
})
</script>
