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
        <v-btn @click="popConfirmCancel(ConfirmCancelMode.RequestInstance, { })" flat>
          <v-icon>
            mdi-plus
          </v-icon>
          Request
        </v-btn>
        <v-btn @click="uiReload()" icon>
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
      width="1280"
    >
      <v-container
        v-if="confirmCancel.mode == ConfirmCancelMode.RequestInstance"
        style="margin-bottom: -1em"
      >
        <v-row>
          <v-col cols="12" md="6" style="max-height: 300px; overflow-y: scroll">
            <v-list
              three-line
            >
              <v-list-item-group v-model="templateIdx">
                <template v-for="(item) in templates">
                  <!-- <v-subheader
                    v-if="item.header"
                    :key="item.header"
                    v-text="item.header"
                  ></v-subheader> -->
                  <v-list-item
                    :key="item.title"
                  >
                    <v-list-item-avatar>
                      <v-img :src="item.logo_url"></v-img>
                    </v-list-item-avatar>

                    <v-list-item-content>
                      <v-list-item-title v-html="item.title"></v-list-item-title>
                      <v-list-item-subtitle v-html="'<span class=\'text--primary\'>' + item.subtitle + '</span><br/>' + item.specs.cores + ' CPU, ' + item.specs.memory + 'MB RAM, ' + item.specs.disk_space +'GB disk space, ' + item.specs.swap +'MB swap '"></v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                </template>
              </v-list-item-group>
            </v-list>
          </v-col>
          <v-col cols="12" md="6" style="max-height: 600px; overflow-y: scroll">
            <v-card flat v-if="templateIdx === undefined">
              <v-card-text>
                <v-row no-gutters justify="start" align="center">
                  <v-col>
                    <v-avatar
                      size="64"
                      tile
                    >
                      <v-icon large>mdi-server</v-icon>
                    </v-avatar>
                  </v-col>
                  <v-col sm="10">
                    <h3>
                      Select a template to continue
                    </h3>
                    <span>
                      A template represents the base installation your instance will have
                    </span>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
            <v-form
              v-else
              lazy-validation
              ref="form"
              @submit="confirm()"
            >
              <v-card flat>
                <v-card-text>
                  <v-row no-gutters justify="start" align="center">
                    <v-col>
                      <v-avatar
                        size="64"
                        tile
                      >
                        <img
                          :src="Object.values(templates)[templateIdx].logo_url"
                          alt="John"
                        >
                      </v-avatar>
                    </v-col>
                    <v-col sm="10">
                      <h3>
                        {{ Object.values(templates)[templateIdx].title }}
                      </h3>
                      <span>
                        {{ Object.values(templates)[templateIdx].subtitle }}
                      </span>
                      <span>
                        {{ Object.values(templates)[templateIdx].description }}
                      </span>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
              <v-divider/>
              <v-card-text>
                <v-card flat>
                  <v-container>
                    <v-row no-gutters justify="start" align="center">
                      <v-col>
                        <v-avatar
                          size="48"
                          tile
                        >
                          <v-icon large>mdi-briefcase-remove</v-icon>
                        </v-avatar>
                      </v-col>
                      <v-col sm="10">
                        <h3>
                          No commercial use
                        </h3>
                        <span>
                          Netsoc Cloud is only for educational and learning purposes
                        </span>
                      </v-col>
                    </v-row>
                  </v-container>
                </v-card>
                <v-card flat>
                  <v-card-text>
                    <v-row no-gutters justify="start" align="center">
                      <v-col>
                        <v-avatar
                          size="48"
                          tile
                        >
                          <v-icon large>mdi-server-off</v-icon>
                        </v-avatar>
                      </v-col>
                      <v-col sm="10">
                        <h3>
                          No 'spammy'/resource-intensive services
                        </h3>
                        <span>
                          No cryptocurrency mining, DNS resolvers, email servers, file-sharing software, IRC servers or VPN usage
                        </span>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
                <v-card flat>
                  <v-card-text>
                    <v-row no-gutters justify="start" align="center">
                      <v-col>
                        <v-avatar
                          size="48"
                          tile
                        >
                          <v-icon large>mdi-voice-off</v-icon>
                        </v-avatar>
                      </v-col>
                      <v-col sm="10">
                        <h3>
                          No inappropiate / adult content
                        </h3>
                        <span>
                          Don't host anything your lecturers wouldn't be comfortable seeing
                        </span>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
                <v-card flat>
                  <v-container>
                    <v-row no-gutters justify="start" align="center">
                      <v-col>
                        <v-avatar
                          size="48"
                          tile
                        >
                          <v-icon large>mdi-chart-line</v-icon>
                        </v-avatar>
                      </v-col>
                      <v-col sm="10">
                        <h3>
                          No support, uptime, or data integrity guarantees
                        </h3>
                        <span>
                          You are responsible for arranging alternative hosting, security and backup procedures for your own instances
                        </span>
                      </v-col>
                    </v-row>
                  </v-container>
                  <v-card-actions>
                    <span class="grey--text">
                      Not an exhaustive list. Consult the <a class="grey--text" target="_blank" href="https://wiki.netsoc.co/services/terms-of-service">Terms of Service</a> for more information
                    </span>
                  </v-card-actions>
                </v-card>
              </v-card-text>
              <v-divider/>
              <v-text-field
                label='Hostname'
                outlined
                style="margin-bottom: -1em"
                v-model='confirmCancel.action.host'
                :rules="requiredRules"
              ></v-text-field>
              <v-textarea
                label='Why do you need this instance?'
                outlined
                :rules="requiredRules"
                v-model='confirmCancel.action.reason'
              ></v-textarea>
            </v-form>
          </v-col>
        </v-row>
      </v-container>
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

<script lang='ts'>
import ConfirmCancelDialog from '@/components/ConfirmCancelDialog.vue'
import MessageDialog from '@/components/MessageDialog.vue'

import { config } from '@/config'
import { fetchRest } from '@/api/rest'
// import { openApiGetSchemaProperty, openApiPropertyValidator } from '@/api/openapi'

import Vue from 'vue'

interface Specs {
  cores: number;
  disk_space: number;
  memory: number;
  swap: number;
}

interface Template {
  id?: string;
  title: string;
  subtitle: string;
  description: string;
  logo_url: string;
  disk_url: string;
  disk_sha256sum: string;
  disk_format: string;
  specs: Specs;
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

interface VHostOptions {
  port: number;
  https: boolean;
}

interface Network {
  ports: { [external: number]: number };
  vhosts: { [vhost: string]: VHostOptions};
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

interface Metadata {
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

enum Type {
  VPS = 'vps',
  LXC = 'lxc'
}

interface Instance {
  node: string;
  type: Type;
  id: number;
  hostname: string;
  fqdn: string;
  specs: Specs;
  active: boolean;
  metadata: Metadata;
  remarks: string[];
  status: Status;
}

enum ConfirmCancelMode {
  Hidden = '-',
  RequestInstance = 'request instance'
}

interface ConfirmCancelAction {
  host?: string;
  template_idx?: number;
  reason?: string;
}

// const HostValidation = new RegExp('^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\\.(xn--)?([a-z0-9\\-]{1,61}|[a-z0-9-]{1,30}\\.[a-z]{2,})$')

export default Vue.extend({
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
          case ConfirmCancelMode.RequestInstance: {
            // console.log(username)
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}-request/${host}`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ template_id, reason })
              })

            this.msg = `${this.typeName} request successfully sent! we will review your request and get back to you soon.`
            break
          }
        }
      } catch (e) {
        this.msg = e.message
      } finally {
        this.confirmCancel.loading = false
        this.confirmCancel.mode = ConfirmCancelMode.Hidden
        this.uiReload()
      }
    },

    async cancel () {
      this.confirmCancel.loading = false
      this.confirmCancel.mode = ConfirmCancelMode.Hidden
    },

    async uiReload () {
      this.loading = true
      this.instances = []

      try {
        // console.log(config)
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/${this.$store.state.auth.user.profile.preferred_username}/${this.type}`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.instances = await res.json()
        this.loading = false

        if (Object.keys(this.instances).length === 0) {
          this.empty = 'You have no instances of this type, try requesting one!'
        }
      } catch (e) {
        this.loading = false
        this.instances = []
        this.empty = e.message
      }
    },

    async popConfirmCancel (mode: ConfirmCancelMode, action: ConfirmCancelAction) {
      this.confirmCancel.action = action
      this.confirmCancel.mode = mode
    },

    async uiReloadTemplates () {
      this.templates = []

      try {
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/${this.$store.state.auth.user.profile.preferred_username}/${this.type}-templates`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.templates = await res.json()
      } catch (e) {
        console.error(e)
      }
    }
  },

  props: {
    type: String,
    typeName: String
  },

  data () {
    const instances: { [hostname: string]: Instance} = {}
    const action: ConfirmCancelAction = {}
    const templates: { [template_id: string]: Template} = {}
    const templateIdx: number | undefined = undefined

    return {
      ConfirmCancelMode, // Needed to use the enum in the rendered template
      empty: '',
      msg: '',
      instances,
      loading: true,
      templates,

      templateIdx,

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
    this.uiReload()
    this.uiReloadTemplates()
  }
})
</script>
