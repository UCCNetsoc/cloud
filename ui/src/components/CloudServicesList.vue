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
        <v-btn @click="popConfirmCancel(ConfirmCancelMode.RequestService, { })" icon>
          <v-icon>
            mdi-plus
          </v-icon>
        </v-btn>
        <v-btn @click="uiReloadLxc()" icon>
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
        v-if="confirmCancel.mode == ConfirmCancelMode.RequestService"
        lazy-validation
        ref="form"
        @submit="confirm()"
      >
        <!-- :suffix="'.'+$store.state.auth.user.profile.preferred_username+'.lxc.cloud.netsoc.co'" -->
        <v-text-field
          label='Hostname'
          outlined
          style="margin-bottom: -1em"
          v-model='confirmCancel.action.host'
          :rules="requiredRules"
        ></v-text-field>
        <v-select
          :items='lxcTemplates'
          label='Template'
          outlined
          :rules="requiredRules"
          v-model='confirmCancel.action.template_id'
          class="mt-4"
          item-text="title"
          item-value="id"
        >
          <template v-slot:item="{ item }">
            <img style="width: 2em; margin-right: 1em;" :src="item.logo_url" />
            <span>{{ item.title }}</span>
          </template>
        </v-select>
        <v-card-text style="margin-top: -2.5em; margin-bottom: -0.5em">
          <v-card flat>
            <v-container>
              <v-row no-gutters justify="start" align="center">
                <v-col>
                  <v-avatar
                    size="32"
                    tile
                  >
                    <v-icon large>mdi-web</v-icon>
                  </v-avatar>
                </v-col>
                <v-col sm="10">
                  <h3>
                    No commerical use
                  </h3>
                  <span>
                    Don't host facebook or listen.moe, etc
                  </span>
                </v-col>
              </v-row>
            </v-container>
          </v-card>
          <v-card flat>
            <v-container>
              <v-row no-gutters justify="start" align="center">
                <v-col>
                  <v-avatar
                    size="32"
                    tile
                  >
                    <v-icon large>mdi-briefcase-account-outline</v-icon>
                  </v-avatar>
                </v-col>
                <v-col sm="10">
                  <h3>
                    No adult material
                  </h3>
                  <span>
                    Find somewhere else
                  </span>
                </v-col>
              </v-row>
            </v-container>
          </v-card>
        </v-card-text>
        <span style="margin: auto;">Check the Terms of service for an exhaustive list of acceptable usages.</span>
        <v-textarea
          label='Reason'
          outlined
          style="margin-top: 1em"
          :rules="requiredRules"
          v-model='confirmCancel.action.reason'
        ></v-textarea>
      </v-form>
      <v-form
        v-else-if="confirmCancel.mode == ConfirmCancelMode.AddWebsite"
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
// import { openApiGetSchemaProperty, openApiPropertyValidator } from '@/api/openapi'

import Vue from 'vue'

interface Template {
  id?: string;
  title: string;
  description: string;
  logo_url: string;
  disk_url: string;
  disk_sha256sum: string;
  disk_format: string;
}

interface Specs {
  cores: number;
  disk_space: number;
  memory: number;
  swap: number;
}

interface ToS {
  suspended: boolean;
  reason: string;
}

interface NICAllocation {
  addresses: string[];
  gateway4: string;
  macaddress: string;
}

interface Network {
  ports: { [external: number]: number };
  vhosts: string[];
  nic_allocation: NICAllocation;
}

interface RootUser {
  password_hash: string;
  ssh_public_key: string;
  mgmt_ssh_public_key: string;
  mgmt_ssh_private_key: string;
}

interface RequestDetail {
  template_id: string;
  reason: string;
}

interface LXCMetadata {
  groups: string[];
  host_vars: { [key: string]: string };
  owner: string;
  tos: ToS;
  network: Network;
  root_user: RootUser;
  request_detail: RequestDetail;
}

enum Status {
  NotApplicable = 'n/a',
  Stopped = 'stopped',
  Running = 'running'
}

interface LXC {
  node: string;
  id: number;
  hostname: string;
  fqdn: string;
  specs: Specs;
  active: boolean;
  metadata: LXCMetadata;
  remarks: string[];
  status: Status;
}

enum ConfirmCancelMode {
  Hidden = '-',
  RequestService = 'request a service'
}

interface ConfirmCancelAction {
  host?: string;
  template_id?: string;
  reason?: string;
}

// const HostValidation = new RegExp('^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\\.(xn--)?([a-z0-9\\-]{1,61}|[a-z0-9-]{1,30}\\.[a-z]{2,})$')

export default Vue.extend({
  name: 'WebsitesList',
  components: {
    ConfirmCancelDialog,
    MessageDialog
  },

  computed: {
    required (): ((v: string) => (string | boolean))[] {
      return [
        (v: string) => !!v || 'Required'
      ]
    },

    // websiteNameRules () {
    //   return [
    //     (v: string) => !!v || 'Website name required',
    //     openApiPropertyValidator(openApiGetSchemaProperty('Website', 'name'))
    //   ]
    // },

    requiredRules () {
      return [
        (v: string) => !!v || 'This field is required'
      ]
    }
    // websiteHostRules () {
    //   return [
    //     (v: string) => !!v || 'Website host required',
    //     (v: string) => {
    //       return HostValidation.test(v) || 'Invalid Host'
    //     }
    //   ]
    // }
  },

  methods: {
    async confirm () {
      // Extract username from profile
      const username = this.$store.state.auth.user.profile.preferred_username
      const headers = {
        Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
      }

      // // Extract action
      const { host, template_id, reason } = this.confirmCancel.action

      this.confirmCancel.loading = true
      try {
        switch (this.confirmCancel.mode) {
          case ConfirmCancelMode.RequestService: {
            // console.log(username)
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/lxc-request/${username}/${host}`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ template_id, reason })
              })

            this.msg = 'Service request successfully sent! We will review your request and get back to you soon.'
            break
          }
        }
      } catch (e) {
        this.msg = e.message
      } finally {
        this.confirmCancel.loading = false
        this.confirmCancel.mode = ConfirmCancelMode.Hidden
        this.uiReloadLxc()
      }
    },

    async cancel () {
      this.confirmCancel.loading = false
      this.confirmCancel.mode = ConfirmCancelMode.Hidden
    },

    async uiReloadLxc () {
      this.lxcLoading = true
      this.lxcs = []

      try {
        // console.log(config)
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/lxc/${this.$store.state.auth.user.profile.preferred_username}`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.lxcLoading = false
        const lxcs: { [name: string]: LXC } = await res.json()
        this.lxcs = Object.values(lxcs)

        if (this.lxcs.length === 0) {
          this.empty = 'You have no services, try requesting one!'
        }
      } catch (e) {
        this.lxcLoading = false
        this.lxcs = []
        this.empty = e.message
      }
    },

    async popConfirmCancel (mode: ConfirmCancelMode, action: ConfirmCancelAction) {
      this.confirmCancel.action = action
      this.confirmCancel.mode = mode
    },

    async uiReloadLxcTemplates () {
      this.lxcTemplates = []

      try {
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/lxc-templates`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })
        const templates: {[name: string]: Template} = await res.json()
        for (const k of Object.keys(templates)) {
          this.lxcTemplates.push(Object.assign(templates[k], { id: k }))
        }
        this.lxcTemplates = Object.values(templates)
      } catch (e) {
        console.error(e)
      }
    }
  },

  data () {
    const lxcs: LXC[] = []
    const action: ConfirmCancelAction = {}
    const lxcTemplates: Template[] = []

    return {
      ConfirmCancelMode, // Needed to use the enum in the rendered template
      empty: '',
      msg: '',
      lxcs,
      lxcLoading: true,
      lxcTemplates,

      confirmCancel: {
        mode: ConfirmCancelMode.Hidden,
        loading: false,
        action
      },

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
    this.uiReloadLxc()
    this.uiReloadLxcTemplates()
  }
})
</script>
