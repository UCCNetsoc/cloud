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
          <v-card-text class="ma-0 justify-center">
            Username: <span class="white--text text--lighten-1">{{ $store.state.auth.user.profile.preferred_username }}</span><br/>
            Email: <span class="white--text text--lighten-1">{{ $store.state.auth.user.profile.email }}</span><br/>
            <br/>
            <p>
              Your account is used for logging into UCC Netsoc web services and our portal server.<br/>
              The portal server is used to connect inside our network so that you can then connect to any of your Cloud instances
              <br/>
              <br/>
              Please remember to keep the <b>Terms of Use</b> and its <b>Acceptable Use Policy</b> in mind as you share server hardware with our other users.
            </p>
            <v-btn color="warning" class="mx-1" @click="passwordReset.visible=true">
              Reset Password
            </v-btn>
            <v-btn color="primary" class="mx-1" @click="gdprRequest.visible=true">
              Data Request
            </v-btn>
            <v-btn color="red" class="mx-1" @click="deleteAccount.visible=true">
              Delete Account
            </v-btn>
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
