<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-data-table
          :loading="loading"
          :headers="headers"
          :items="Object.entries(instances).sort()"
          :items-per-page="50"
          style="margin-top: -1rem"
        >
          <template slot="no-data">
            {{ empty }}
          </template>

          <template v-slot:item="row">
            <tr
              :style="row.item[1].active === true ? (row.item[1].status == Status.Running ? 'background-color: rgba(0,255,0,0.04)' : 'background-color: rgba(255,0,0,0.04)') :  'filter: grayscale(0.2); background-color: rgba(127,127,127,0.04)' "
            >
              <td>
                <v-container class="pa-0 ma-0">
                  <v-row justify="start">
                    <v-col sm="12" md="3" align="center" justify="center">
                      <v-avatar
                        size="36"
                        tile
                        class="my-2"
                      >
                        <v-icon v-if="getTemplate(row.item[1].metadata.request_detail.template_id).logo_url===''">
                          mdi-help
                        </v-icon>
                        <img
                          v-else
                          :src="getTemplate(row.item[1].metadata.request_detail.template_id).logo_url"
                        >
                      </v-avatar>
                    </v-col>
                    <v-col sm="12" md="9">
                      <h2 class="pa-0 ma-0">{{row.item[1].hostname}}</h2>
                      <h4 class="mb-2">{{ getTemplate(row.item[1].metadata.request_detail.template_id).title }}</h4>
                      <div class="caption" v-for="spec in getSpecList(row.item[1].specs)" :key="spec">
                        {{ spec }}
                      </div>
                      <v-btn
                        x-small
                        class="mr-1 my-2 blue"
                        @click="msg = marked(getTemplate(row.item[1].metadata.request_detail.template_id).description)"
                        :disabled="row.item[1].metadata.tos.suspended === true"
                      >
                        <v-icon>
                          mdi-information
                        </v-icon>
                        info
                      </v-btn>
                      <v-btn
                        x-small
                        class="ma-1 my-2 blue"
                        @click="openConfirmCancel(ConfirmCancelMode.RequestRespec, { hostname: row.item[0] })"
                        :disabled="row.item[1].metadata.tos.suspended === true"
                      >
                        <v-icon>
                          mdi-server-plus
                        </v-icon>
                        upgrade
                      </v-btn>
                    </v-col>
                  </v-row>
                </v-container>
              </td>
              <td class="py-4">
                <v-container class="ma-0 pa-0">
                  <v-row no-gutters justify="start" align="center">
                    <p class="caption">
                      Internal IP:<br/>
                      <b>{{row.item[1].metadata.network.nic_allocation.addresses[0].split('/')[0] }}</b>
                      <br/>
                      <br/>
                      Forwarded ports available on external domain:<br/>
                      <b>{{row.item[1].fqdn}}</b>
                    </p>
                  </v-row>
                  <v-container v-for="(internal, external) in row.item[1].metadata.network.ports" :key="external" class="pa-0 ma-0">
                    <v-row no-gutters justify="start" align="center">
                      <v-col sm="12" md="10">
                        <code>:{{external}}</code>
                        <v-icon x-small class="ma-1">
                          mdi-arrow-expand-right
                        </v-icon>
                        <code>{{internal}}</code>
                      </v-col>
                      <v-col sm="12" md="2">
                        <v-btn
                          x-small
                          icon
                          @click="openConfirmCancel(ConfirmCancelMode.RemovePort, { hostname: row.item[0], portMapExternal: external })"
                          :disabled="row.item[1].metadata.tos.suspended === true"
                        >
                          <v-icon>
                            mdi-delete
                          </v-icon>
                        </v-btn>
                      </v-col>
                    </v-row>
                  </v-container>
                  <v-btn
                    x-small
                    @click="openConfirmCancel(ConfirmCancelMode.AddPort, { hostname: row.item[0] })"
                    class="purple ma-1 my-4"
                    :disabled="row.item[1].active === false"
                  >
                    <v-icon>
                      mdi-plus
                    </v-icon>
                    port
                  </v-btn>
                </v-container>
              </td>
              <td class="py-4">
                <v-container v-for="(opts, vhost) in row.item[1].metadata.network.vhosts" :key="vhost" class="pa-0 ma-0 my-3">
                  <v-row no-gutters justify="start" align="center">
                    <v-col sm="12" md="12">
                      <a class="white--text" target="_blank" :href="'https://'+vhost">https://{{vhost}}</a>
                    </v-col>
                  </v-row>
                  <v-row no-gutters justify="start" align="center">
                    <v-col sm="12" md="10">
                      <span style="font-size: 12px">({{opts.port}}, {{opts.https === true ? "HTTPS" : "HTTP"}})</span>
                    </v-col>
                    <v-col sm="12" md="2">
                      <v-btn
                        x-small
                        icon
                        @click="openConfirmCancel(ConfirmCancelMode.RemoveVirtualHost, { hostname: row.item[0], vHostDomain: vhost })"
                        :disabled="row.item[1].metadata.tos.suspended === true"
                      >
                        <v-icon>
                          mdi-delete
                        </v-icon>
                      </v-btn>
                    </v-col>
                  </v-row>
                </v-container>
                <v-btn
                  x-small
                  @click="openConfirmCancel(ConfirmCancelMode.AddVirtualHost, { hostname: row.item[0] })"
                  class="purple ma-1"
                  :disabled="row.item[1].active == false"
                >
                  <v-icon>
                    mdi-plus
                  </v-icon>
                  vhost
                </v-btn>
              </td>
              <td class="py-4">
                <p class="my-1" style="max-width: 220px;" v-for="remark in row.item[1].remarks" :key="remark">{{ remark }}</p>
              </td>
              <td>
                <v-container class="ma-0 pa-0">
                  <v-row no-gutters justify="start" align="center">
                    <v-col sm="12" md="2">
                      <v-avatar
                        size="24"
                        tile
                      >
                        <v-icon size="24" :class="row.item[1].active ? 'green--text' : 'red--text'">
                          {{row.item[1].active ? 'mdi-check-circle' : 'mdi-close-circle'}}
                        </v-icon>
                      </v-avatar>
                    </v-col>
                    <v-col sm="12" md="10">
                      <div v-if="row.item[1].metadata.tos.suspended == true" class="red--text">
                        <b>Suspended ({{ row.item[1].metadata.tos.reason }})</b>
                      </div>
                      <div v-else-if="row.item[1].metadata.permanent == true" class="green--text">
                        <b>Permanent</b>
                      </div>
                      <div v-else-if="row.item[1].active == true" class="green--text">
                        Active until <b>{{ row.item[1].inactivity_shutdown_date }}</b>
                      </div>
                      <div v-else-if="row.item[1].active == false" class="red--text">
                        Deletion on <b>{{ row.item[1].inactivity_deletion_date }}</b>
                      </div>
                      <v-btn
                        v-if="row.item[1].metadata.tos.suspended == false && row.item[1].metadata.permanent == false"
                        :ripple="false"
                        x-small
                        :class="row.item[1].active ? 'green ma-1' : 'red ma-1'"
                        inline
                        @click="openConfirmCancel(ConfirmCancelMode.RenewActivation, { hostname: row.item[0] })"
                      >
                        <v-icon>
                          mdi-timer
                        </v-icon>
                        renew
                      </v-btn>
                    </v-col>
                  </v-row>
                </v-container>
              </td>
              <td>
                <v-avatar
                  size="32"
                  tile
                >
                  <v-icon size="32" :class="row.item[1].status == Status.Running ? 'green--text' : 'red--text'">
                    {{row.item[1].status == Status.Running ? 'mdi-play' : 'mdi-stop'}}
                  </v-icon>
                </v-avatar>
                <span :class="row.item[1].status == Status.Running ? 'green--text' : 'red--text'">
                  <b>{{row.item[1].status}}</b>
                </span>
              </td>
              <td class="pa-2">
                <v-btn
                  x-small
                  class="ma-1 blue"
                  :disabled="row.item[1].status != Status.Running || row.item[1].active == false"
                  @click="openConfirmCancel(ConfirmCancelMode.OpenTerminal, { hostname: row.item[0] })"
                >
                  <v-icon>
                    mdi-console-line
                  </v-icon>
                  terminal
                </v-btn>
                <v-btn
                  x-small
                  class="ma-1 blue"
                  :disabled="row.item[1].status != Status.Running || row.item[1].active == false"
                  @click="openConfirmCancel(ConfirmCancelMode.OpenFilesystem, { hostname: row.item[0] })"
                >
                  <v-icon>
                    mdi-file-multiple
                  </v-icon>
                  filesystem
                </v-btn>
                <v-btn
                  x-small
                  class="ma-1 red"
                  @click="openConfirmCancel(ConfirmCancelMode.ResetRootUser, { hostname: row.item[0] })"
                  :disabled="row.item[1].status == Status.Stopped || row.item[1].active == false"
                >
                  <v-icon>
                    mdi-account
                  </v-icon>
                  reset root
                </v-btn>
                <br/>
                <v-btn
                  x-small
                  class="ma-1 green"
                  :disabled="row.item[1].status == Status.Running || row.item[1].active == false"
                  @click="openConfirmCancel(ConfirmCancelMode.StartInstance, { hostname: row.item[0] })"
                >
                  <v-icon>
                    mdi-play
                  </v-icon>
                  start
                </v-btn>
                <v-btn
                  x-small
                  class="ma-1 warning"
                  :disabled="row.item[1].status != Status.Running || row.item[1].active == false"
                  @click="openConfirmCancel(ConfirmCancelMode.ShutdownInstance, { hostname: row.item[0] })"
                >
                  <v-icon>
                    mdi-power
                  </v-icon>
                  shutdown
                </v-btn>
                <v-btn
                  x-small
                  class="ma-1 red"
                  :disabled="row.item[1].status != Status.Running || row.item[1].active == false"
                  @click="openConfirmCancel(ConfirmCancelMode.StopInstance, { hostname: row.item[0] })"
                >
                  <v-icon>
                    mdi-stop
                  </v-icon>
                  stop
                </v-btn>
                <v-btn
                  x-small
                  class="ma-1 black"
                  @click="openConfirmCancel(ConfirmCancelMode.DeleteInstance, { hostname: row.item[0] })"
                  :disabled="row.item[1].active == false"
                >
                  <v-icon>
                    mdi-delete
                  </v-icon>
                  delete
                </v-btn>
              </td>
            </tr>
          </template>
        </v-data-table>
      </v-col>
    </v-row>
    <v-row class="center ml-1" style="margin-top: -1em">
      <v-col class="d-flex  justify-end" cols="12" sm="12">
        <v-btn class="primary" @click="openConfirmCancel(ConfirmCancelMode.RequestInstance, { })" flat>
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
      <span v-html="msg"></span>
    </message-dialog>
    <confirm-cancel-dialog
      :title="confirmCancel.mode"
      :visible="confirmCancel.mode !== ConfirmCancelMode.Hidden"
      :loading="confirmCancel.loading"
      @confirmed="confirm()"
      @cancelled="cancel()"
      :width="confirmCancel.mode == ConfirmCancelMode.RequestInstance ? '1280' : '560'"
    >
      <v-container
        v-if="confirmCancel.mode == ConfirmCancelMode.RequestInstance"
        style="margin-bottom: -1em"
      >
        <v-row>
          <v-col cols="12" md="6" style="max-height: 480px; overflow-y: scroll">
            <v-list
              three-line
            >
              <v-list-item-group @change="idx => setConfirmCancelTemplate(idx)">
                <template v-for="(item) in templates">
                  <v-list-item
                    :key="item.title"
                  >
                    <v-list-item-avatar>
                      <v-img :src="item.logo_url"></v-img>
                    </v-list-item-avatar>

                    <v-list-item-content>
                      <v-list-item-title v-html="item.title"></v-list-item-title>
                      <v-list-item-subtitle v-html="'<span class=\'text--primary\'>' + item.subtitle + '</span><br/>' + getSpecString(item.specs)"></v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                </template>
              </v-list-item-group>
            </v-list>
          </v-col>
          <v-col cols="12" md="6" style="max-height: 480px; overflow-y: scroll">
            <v-card flat v-if="confirmCancel.action.templateId === undefined">
              <v-card-text>
                <v-row no-gutters justify="start" align="center">
                  <v-col>
                    <v-avatar
                      size="64"
                      tile
                    >
                      <v-icon size="64" large>mdi-map-outline</v-icon>
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
                          :src="confirmCancel.action.template.logo_url"
                        >
                      </v-avatar>
                    </v-col>
                    <v-col sm="10">
                      <h3 class="white--text">
                        {{ confirmCancel.action.template.title + ' ' + typeName }}
                      </h3>
                      <span class="grey--text text--lighten-2">
                        {{ confirmCancel.action.template.subtitle }}<br/>
                      </span>
                      <p v-html="marked(confirmCancel.action.template.description)"></p>
                      <h4 class="white--text">
                        {{ getSpecString(confirmCancel.action.template.specs) }}
                      </h4>
                    </v-col>
                  </v-row>
                  <v-row class="mt-4 mb-0">
                    <v-text-field
                      label='Hostname'
                      class="mx-4"
                      outlined
                      v-model='confirmCancel.action.host'
                      :rules="requiredRules"
                    ></v-text-field>
                  </v-row>
                  <v-row class="mt-0">
                    <v-textarea
                      label='Why do you need this instance?'
                      class="mx-4"
                      height=96
                      outlined
                      :rules="requiredRules"
                      v-model='confirmCancel.action.reason'
                    ></v-textarea>
                  </v-row>
                  <v-divider/>
                  <v-row class="my-6 grey--text text--darken-1 text-center">
                    <p style="margin: 0 auto" class="grey--text text--darken-1 text-center">
                      <b>IMPORTANT:</b>
                      Some disallowed uses found below, not an exhaustive list.<br/>
                      Consult latest <a class="grey--text" target="_blank" href="https://wiki.netsoc.co/services/terms-of-service">Terms of Service</a> for more information.
                    </p>
                  </v-row>
                  <v-row class="my-4" no-gutters justify="start" align="center">
                    <v-col>
                      <v-avatar
                        size="48"
                        tile
                      >
                        <v-icon large>mdi-briefcase-remove</v-icon>
                      </v-avatar>
                    </v-col>
                    <v-col sm="10">
                      <h3 class="white--text">
                        No commercial use
                      </h3>
                      <span class="grey--text text--lighten-1">
                        Netsoc Cloud is only for educational, entertainment and learning purposes
                      </span>
                    </v-col>
                  </v-row>
                  <v-row class="my-4" no-gutters justify="start" align="center">
                    <v-col>
                      <v-avatar
                        size="48"
                        tile
                      >
                        <v-icon large>mdi-server-off</v-icon>
                      </v-avatar>
                    </v-col>
                    <v-col sm="10">
                      <h3 class="white--text">
                        No resource-intensive or "spammy" services
                      </h3>
                      <span class="grey--text text--lighten-1">
                        No cryptocurrency mining, DNS resolvers, email servers, file-sharing software, IRC servers or VPN usage
                      </span>
                    </v-col>
                  </v-row>
                  <v-row class="my-4" no-gutters justify="start" align="center">
                    <v-col>
                      <v-avatar
                        size="48"
                        tile
                      >
                        <v-icon large>mdi-voice-off</v-icon>
                      </v-avatar>
                    </v-col>
                    <v-col sm="10">
                      <h3 class="white--text">
                        No inappropiate or adult content
                      </h3>
                      <span class="grey--text text--lighten-1">
                        Don't host anything your lecturers wouldn't be comfortable seeing or hearing about
                      </span>
                    </v-col>
                  </v-row>
                  <v-row class="my-4" no-gutters justify="start" align="center">
                    <v-col>
                      <v-avatar
                        size="48"
                        tile
                      >
                        <v-icon large>mdi-chart-line</v-icon>
                      </v-avatar>
                    </v-col>
                    <v-col sm="10">
                      <h3 class="white--text">
                        No data integrity, support or uptime guarantees
                      </h3>
                      <span class="grey--text text--lighten-1">
                        You are responsible for arranging alternative hosting during downtime, security and backup procedures for your own instances.
                        We cannot guarantee a response or resolution to a request for support
                      </span>
                    </v-col>
                  </v-row>
                  <v-row class="my-4" no-gutters justify="start" align="center">
                    <v-col>
                      <v-avatar
                        size="48"
                        tile
                      >
                        <v-icon large>mdi-message</v-icon>
                      </v-avatar>
                    </v-col>
                    <v-col sm="10">
                      <h3 class="white--text">
                        You must monitor the <code>#servers</code> channel in the <a class="white--text" target="_blank" href="https://discord.netsoc.co">UCC Netsoc Discord</a>
                      </h3>
                      <span class="grey--text text--lighten-1">
                        Important announcements and discussions will be posted there from time to time
                      </span>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-form>
          </v-col>
        </v-row>
      </v-container>
      <v-form
        v-else-if="confirmCancel.mode == ConfirmCancelMode.RequestRespec"
        lazy-validation
        ref="form"
        @submit="confirm()"
      >
        <p>
          You are allowed to request new specifications for your instance.<br/>
          Your request needs to be reasonable or it may be denied!<br/><br/>
          Simply outline what specifications you need below and why:<br/><br/>
          <span class="blue--text">
            Make sure to leave your Discord name so you can be contacted in our <code>#servers</code> channel
          </span>
          <br/>
        </p>
        <v-textarea
          label='What specifications do you need and why?'
          outlined
          :rules="requiredRules"
          v-model='confirmCancel.action.respecReason'
        ></v-textarea>
      </v-form>
      <v-form
        v-else-if="confirmCancel.mode == ConfirmCancelMode.AddPort"
        lazy-validation
        ref="form"
        @submit="confirm()"
      >
        <p>
          You can add a port forwardng rule to map traffic from the external internet to your instance<br/><br/>

          A port mapping of<br/>
          <code>42069</code>
          <v-icon x-small class="ma-1">
            mdi-arrow-expand-right
          </v-icon>
          <code>8080</code><br/>
          would cause any traffic sent to<br/>
          <code>{{ instances[confirmCancel.action.hostname].fqdn }}:42069</code><br/>
          to be sent to port <code>8080</code> inside your instance<br/><br/>

          <b class="warning--text">You should not create mappings to the following internal ports:</b>
          <ul>
            <li>21 (FTP, use SFTP)</li>
            <li>23 (Telnet, use SSH)</li>
            <li>25 (SMTP, we forbid hosting mail servers)</li>
            <li>53 (DNS, we forbid hosting DNS servers)</li>
            <li>143 (IMAP, we forbid hosting mail servers)</li>
          </ul>
        </p>
        <v-container class="ma-0 pa-0">
          <v-row no-gutters justify="start" align="center">
            <v-col sm="5">
              <v-text-field
                disabled
                label='External port'
                v-model='confirmCancel.action.portMapExternal'
              ></v-text-field>
            </v-col>
            <v-col sm="2">
              <v-icon class="pa-4" large>
                  mdi-arrow-expand-right
              </v-icon>
            </v-col>
            <v-col sm="5">
              <v-text-field
                label='Internal port'
                v-model='confirmCancel.action.portMapInternal'
              ></v-text-field>
            </v-col>
          </v-row>
        </v-container>
        <v-btn small @click="confirmCancelRandomizeExternalPort()">
          <v-icon>
            mdi-dice-multiple
          </v-icon>
          random external port
        </v-btn>
      </v-form>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.RemovePort">
        Are you sure you want to remove the port mapping?
      </p>
      <v-form
        v-else-if="confirmCancel.mode == ConfirmCancelMode.AddVirtualHost"
        lazy-validation
        ref="form"
        @submit="confirm()"
      >
        <h3>
          Using your free Netsoc Cloud domain
        </h3>
        <p>
          You can use any domain that match the following forms:
          <ul>
            <li>{{ $store.state.auth.user.profile.preferred_username }}.{{ vhostRequirements.base_domain }}</li>
            <li>
              *.{{ $store.state.auth.user.profile.preferred_username }}.{{ vhostRequirements.base_domain }}
              <ul>
                <li>e.g. blog.{{ $store.state.auth.user.profile.preferred_username }}.{{ vhostRequirements.base_domain }}</li>
              </ul>
            </li>
            <li>{{ instances[confirmCancel.action.hostname].fqdn }}</li>
          </ul>
        </p>
        <h3>
          Using your own domain
        </h3>
        <p>
          You must visit the website for your domain registrar and add the following records to your domain:
          <ul>
            <li>
              <code>TXT</code>
              record of key
              <code>{{ vhostRequirements.user_supplied.verification_txt_name }}</code>
              with value
              <code>{{ $store.state.auth.user.profile.preferred_username }}</code>
            </li>
            <li v-for="record in vhostRequirements.user_supplied.allowed_a_aaaa" :key="record">
              <code>A</code>
              record of value
              <code>{{ record }}</code>
            </li>
          </ul><br/>
          <b class="warning--text">These values may be subject to change.<br/>We will make an announcement in the <code>#servers</code> channel on our Discord if this is the case</b>
        </p>
        <v-text-field
          label='Virtual Host'
          v-model='confirmCancel.action.vHostDomain'
          :rules='websiteHostRules'
          :placeholder='$store.state.auth.user.profile.preferred_username+"."+vhostRequirements.base_domain'
        ></v-text-field>
        <v-text-field
          label='HTTP(S) port to reverse proxy'
          v-model='confirmCancel.action.vHostPort'
          :rules='websiteHostRules'
          :placeholder='"80"'
        ></v-text-field>
        <v-switch
          v-model='confirmCancel.action.vHostHttps'
          class="ma-0 pa-0"
          label="Is the internal service using HTTPS (typically not)?"
        ></v-switch>
      </v-form>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.RemoveVirtualHost">
        Are you sure you want to remove the host?<br/>
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.RenewActivation">
        Are you sure you want to renew the instance activation?<br>
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.StartInstance">
        Are you sure you want to start the instance?<br>
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.StopInstance">
        Are you sure you want to stop the instance?<br>
        The instance will be terminated immediately, this may lead to corrupted data. Try a shutdown instead!
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.ShutdownInstance">
        Are you sure you want to shut down the instance?<br>
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.DeleteInstance">
        Are you sure you want to delete the instance?<br><br>
        <b class="error--text">
          This action is irreversible and will permanently delete any data associated with the instance!
        </b>
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.ResetRootUser">
        Are you sure you want to reset the root user?<br>
        A new SSH password and private key will be sent to the email associated with your account.<br><br>
        <b class="warning--text">
          This action is irreversible and will possibly change the root password, rotate the host keys and re-enable root SSH access
        </b>
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.OpenTerminal">
        You are about to open an SSH terminal for this instance<br><br>
        You wll be prompted for:
        <ul>
          <li>Username of an account on this instance</li>
          <li>Password of the account</li>
        </ul><br>
        <b class="warning--text">If you have not already reset the <code>root</code> user password, you will need to do so before you can make use of this feature</b>
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.OpenFilesystem">
        You are about to open an SFTP browser for this instance.<br><br>

        You wll be prompted for:
        <ul>
          <li>
            Host
            <ul>
              <li>You will need to enter <code>{{ instances[confirmCancel.action.hostname].metadata.network.nic_allocation.addresses[0].split('/')[0] }}</code> and port <code>22</code></li>
            </ul>
          </li>
          <li>Username of an account on this instance</li>
          <li>Password of the account</li>
          <li>Remember to select <b>Password Authentication</b></li>
          <li>All other fields can be left blank</li>
        </ul>
        <br/>
        <b class="warning--text">If you have not already reset the <code>root</code> user password, you will need to do so before you can make use of this feature</b>
      </p>
    </confirm-cancel-dialog>
  </v-container>
</template>

<style scoped>
/* prevent highlight on scroll */
.v-data-table
  tbody
  tr:hover:not(.v-data-table__expanded__content) {
  background: inherit;
}
</style>

<script lang='ts'>
import marked from 'marked'

import ConfirmCancelDialog from '@/components/ConfirmCancelDialog.vue'
import MessageDialog from '@/components/MessageDialog.vue'

import { config } from '@/config'
import { fetchRest } from '@/api/rest'
// import { openApiGetSchemaProperty, openApiPropertyValidator } from '@/api/openapi'

import { Instance, Template, Status, Specs, VHostRequirements } from '@/api/cloud'

import Vue from 'vue'

enum ConfirmCancelMode {
  Hidden = '-',
  RequestInstance = 'request instance',
  RequestRespec = 'request new specifications',
  RenewActivation = 'renew activation',
  AddVirtualHost = 'add virtual host',
  RemoveVirtualHost = 'remove virtual host',
  AddPort = 'add port mapping',
  RemovePort = 'remove port mapping',
  StartInstance = 'start instance',
  ShutdownInstance = 'shutdown instance',
  StopInstance = 'stop instance',
  DeleteInstance = 'delete instance',
  ResetRootUser = 'reset root user',
  OpenTerminal = 'open terminal',
  OpenFilesystem = 'open filesystem'
}

export interface ConfirmCancelAction {
  template?: Template;
  templateId?: string;
  hostname?: string;
  reason?: string;
  host?: string;

  respecReason?: string;
  portMapExternal?: number;
  portMapInternal?: number;
  vHostDomain?: string;
  vHostHttps?: boolean;
  vHostPort?: number;
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
    marked (str: string) {
      return marked(str)
    },

    open (url: string) {
      window.open(url, '_blank', '')
    },

    getTemplate (templateId: string): Template {
      if (templateId in this.templates) {
        return this.templates[templateId]
      }

      return {
        title: 'Unknown Template',
        subtitle: 'This template has been renamed or moved',
        description: 'This template has been renamed or moved, contact a SysAdmin on the UCC Netsoc Discord if you are having any issues',
        logo_url: '',
        disk_url: '',
        disk_sha256sum: '',
        disk_format: '',
        specs: {
          cores: 0,
          disk_space: 0,
          memory: 0,
          swap: 0
        }
      }
    },

    async openConfirmCancel (mode: ConfirmCancelMode, action: ConfirmCancelAction = {}) {
      this.confirmCancel.action = action
      this.confirmCancel.mode = mode

      if (mode === ConfirmCancelMode.AddPort) {
        await this.confirmCancelRandomizeExternalPort()
      }
    },

    async closeConfirmCancel () {
      this.confirmCancel.action = {}
      this.confirmCancel.mode = ConfirmCancelMode.Hidden
      this.confirmCancel.loading = false
    },

    setConfirmCancelTemplate (templateIdx: number | undefined) {
      if (templateIdx === undefined) {
        this.confirmCancel.action = {
          templateId: undefined,
          template: undefined
        }
        return
      }

      this.confirmCancel.action = {
        templateId: Object.keys(this.templates)[templateIdx],
        template: this.templates[Object.keys(this.templates)[templateIdx]]
      }
    },

    getSpecString (specs: Specs): string {
      return `${specs.cores} CPU, ${specs.memory}MB RAM, ${specs.disk_space}GB disk space, ${specs.swap}MB swap`
    },

    getSpecList (specs: Specs): string[] {
      return this.getSpecString(specs).split(',')
    },

    async confirmCancelRandomizeExternalPort () {
      const username = this.$store.state.auth.user.profile.preferred_username
      const headers = {
        Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
      }

      const action = this.confirmCancel.action
      this.confirmCancel.loading = true

      try {
        const req = await fetchRest(
        `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${action.hostname}/free-external-port`, {
          method: 'GET',
          headers
        })

        this.confirmCancel.action.portMapExternal = parseInt(await req.text())
      } catch (e) {
        this.msg = e.message
        this.closeConfirmCancel()
        this.uiReload()
      } finally {
        this.confirmCancel.loading = false
      }
    },

    async confirm () {
      // Extract username from profile
      const username = this.$store.state.auth.user.profile.preferred_username
      const headers = {
        Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
      }

      // Extract action
      const { host, template, hostname, portMapExternal, portMapInternal, vHostDomain, vHostHttps, vHostPort, templateId, reason, respecReason } = this.confirmCancel.action
      this.confirmCancel.loading = true

      try {
        switch (this.confirmCancel.mode) {
          case ConfirmCancelMode.RequestInstance: {
            const req = await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}-request/${host}`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                  template_id: templateId,
                  reason
                })
              })

            const json = await req.json()
            this.msg = json.detail.msg

            break
          }

          case ConfirmCancelMode.RequestRespec: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/respec-request`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                  details: respecReason
                })
              })
            break
          }

          case ConfirmCancelMode.RenewActivation: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/active`, {
                method: 'POST',
                headers
              })
            break
          }

          case ConfirmCancelMode.AddVirtualHost: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/vhost/${vHostDomain}`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                  port: vHostPort,
                  https: vHostHttps
                })
              })
            break
          }

          case ConfirmCancelMode.RemoveVirtualHost: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/vhost/${vHostDomain}`, {
                method: 'DELETE',
                headers
              })
            break
          }

          case ConfirmCancelMode.AddPort: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/port/${portMapExternal}/${portMapInternal}`, {
                method: 'POST',
                headers
              })
            break
          }

          case ConfirmCancelMode.RemovePort: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/port/${portMapExternal}`, {
                method: 'DELETE',
                headers
              })

            break
          }

          case ConfirmCancelMode.ResetRootUser: {
            const req = await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/reset-root-user`, {
                method: 'POST',
                headers
              })

            const json = await req.json()
            this.msg = json.detail.msg

            break
          }

          case ConfirmCancelMode.StartInstance: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/start`, {
                method: 'POST',
                headers
              })
            break
          }

          case ConfirmCancelMode.ShutdownInstance: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/shutdown`, {
                method: 'POST',
                headers
              })
            break
          }

          case ConfirmCancelMode.StopInstance: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}/stop`, {
                method: 'POST',
                headers
              })
            break
          }

          case ConfirmCancelMode.DeleteInstance: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/proxmox/${username}/${this.type}/${hostname}`, {
                method: 'DELETE',
                headers
              })
            break
          }

          case ConfirmCancelMode.OpenTerminal: {
            const instance = this.instances[hostname as string]

            open(config.sshUrl + '/ssh/host/' + instance.metadata.network.nic_allocation.addresses[0].split('/')[0])
            break
          }

          case ConfirmCancelMode.OpenFilesystem: {
            const instance = this.instances[hostname as string]

            open(config.sftpUrl)
            break
          }
        }
      } catch (e) {
        this.confirmCancel.loading = false
        this.msg = e.message
      } finally {
        this.closeConfirmCancel()
        setTimeout(() => this.uiReload(), 10)
      }
    },

    async cancel () {
      this.confirmCancel.loading = false
      this.confirmCancel.mode = ConfirmCancelMode.Hidden
    },

    async uiSetInstances (instances: { [hostname: string]: Instance}) {
      if (Object.keys(instances).length === 0) {
        this.empty = 'You have no instances of this type, try requesting one!'
      }

      this.instances = instances
    },

    async uiReload () {
      this.loading = true

      try {
        const bdRes = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/vhost-requirements`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.vhostRequirements = await bdRes.json()

        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/${this.$store.state.auth.user.profile.preferred_username}/${this.type}`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.loading = false
        this.uiSetInstances(await res.json())
      } catch (e) {
        this.loading = false
        this.empty = e.message
        this.instances = {}
      }
    },

    async uiSilentReload () {
      if (this.loading === true) {
        return
      }

      // Silently reload without clearing the UI list
      try {
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/${this.$store.state.auth.user.profile.preferred_username}/${this.type}`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.uiSetInstances(await res.json())
      } catch (e) {
        this.loading = false
        this.empty = e.message
        this.instances = {}
      }
    },

    async uiSilentReloadLoop () {
      setTimeout(() => {
        // Only refresh list when they're looking at it
        // i.e confirmcancel dialog is hidden
        if (this.confirmCancel.mode === ConfirmCancelMode.Hidden) {
          this.uiSilentReload()
        }
        this.uiSilentReloadLoop()
      }, 30000 + (-7500 + (Math.random() * 7500)))
    },

    async uiReloadTemplates () {
      this.templates = {}

      try {
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/${this.$store.state.auth.user.profile.preferred_username}/${this.type}-templates`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.templates = await res.json()
      } catch (e) {
        this.msg = `Could not fetch templates: ${e.message}`
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
    const vhostRequirements: VHostRequirements | undefined = undefined

    return {
      Status,
      ConfirmCancelMode, // Needed to use the enum in the rendered template
      empty: '',
      msg: '',
      instances,
      loading: true,
      templates,

      templateIdx,
      vhostRequirements,

      confirmCancel: {
        mode: ConfirmCancelMode.Hidden,
        loading: false,
        action
      },

      headers: [
        { text: 'Instance' },
        { text: 'Port Forwarding' },
        { text: 'Virtual Hosts' },
        { text: 'Remarks' },
        { text: 'Activation' },
        { text: 'Status' },
        { text: 'Actions' }
      ]
    }
  },

  mounted () {
    this.uiReload()
    this.uiReloadTemplates()
    this.uiSilentReloadLoop()
  }
})
</script>
