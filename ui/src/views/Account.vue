<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>
            Hi {{ $store.state.auth.user.profile.preferred_username }}!
          </v-card-title>
          <v-card-subtitle>
            UCC Netsoc welcomes you!
          </v-card-subtitle>
          <v-card-text>
            <p>
              We offer a user server that any of our members can connect to and make use of at any time.<br>
              By default you have a free account on this server, automatically made available when you signed up
            </p>
            <p>
              You can play around with Linux, store files, compile code... hat you do with it is all up to you!
            </p>
            <p>
              Please remember to keep the <b>Terms of Use</b> in mind, this server space is shared with our other users.
            </p>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card>
          <v-card-title>
            Account
          </v-card-title>
          <v-card-text class="ma-0 justify-center">
            Username: {{ $store.state.auth.user.profile.preferred_username }}<br/>
            Email: {{ $store.state.auth.user.profile.email }}
          </v-card-text>
          <v-card-actions>
            <v-container flex class="justify-center">
              <v-btn color="primary" class="mx-1" @click="gdprRequest.visible=true">
                Data Request
              </v-btn>
              <v-btn color="warning" class="mx-1" @click="passwordReset.visible=true">
                Reset Password
              </v-btn>
              <v-btn color="red" class="mx-1" @click="deleteAccount.visible=true">
                Delete Account
              </v-btn>
            </v-container>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>
            Connecting to the server
          </v-card-title>
          <v-card-text>
            <p>
              You can connect to the server via <code>ssh</code> to <code>portal.netsoc.co</code> or using our web based Terminal<br>
              Your username and password are the same ones as your account on this website
            </p>
            <h2 class="font-weight-regular pb-2">Troubleshooting:</h2>
            <ul>
              <li>
                <b>It was working previously and now I am recieving a message similar to <code>Connection refused</code>:</b>
                <p>
                  Every user gets 5 password attempts from their IP address until their account is temporarily blocked for 24hrs
                  <br><br>
                  This is an automated system to prevent security attacks on our network.
                  <br>
                  If you have gotten your password wrong too many times, you will need to wait these 24hrs or contact the SysAdmins on our Discord
                </p>
              </li>
              <li>
                <b>I am accessing the server from inside student accomodation / workplace WiFi</b>
                <p>
                  Some businesses block all outgoing SSH (port 22) traffic.
                  You will need to find an alternative internet connection or make use of a VPN.
                </p>
              </li>
              <li>
                <b>When I try to type my password into the terminal/PuTTY, the cursor doesn't move</b>
                <p>
                  This is standard security practice to hide the length of your password<br />
                  Your keystrokes are still being registered, they just won't appear on the screen.<br />
                  Enter and Backspace will still work
                </p>
              </li>
            </ul>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <password-reset-dialog :visible="passwordReset.visible" @successful="passwordReset.visible=false" @cancelled="passwordReset.visible=false"/>
    <g-d-p-r-dialog :visible="gdprRequest.visible" @successful="gdprRequest.visible=false" @cancelled="gdprRequest.visible=false"/>
    <delete-account-dialog :visible="deleteAccount.visible" @successful="deleteAccount.visible=false"/>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import PasswordResetDialog from '@/components/PasswordResetDialog.vue'
import GDPRDialog from '@/components/GDPRDialog.vue'
import DeleteAccountDialog from '@/components/DeleteAccountDialog.vue'

export default Vue.extend({
  name: 'Account',
  components: {
    PasswordResetDialog,
    GDPRDialog,
    DeleteAccountDialog
  },

  data: () => ({
    passwordReset: {
      visible: false
    },

    gdprRequest: {
      visible: false
    },

    deleteAccount: {
      visible: false
    }
  })
})
</script>
