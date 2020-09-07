<template>
  <v-container>
    <card-dialog
      :visible="visible"
      width="430"
    >
      <v-card-title class="justify-center text-center white--text font-weight-light">
        sign up
      </v-card-title>
      <v-divider/>
      <v-card-text>
        <v-form
          lazy-validation
          ref="form"
          class=""
        >
          <v-select
            :items='Object.keys(categories)'
            label='I am a:'
            outlined
            v-model='category'
            class="mt-4"
            style="margin-bottom: -1.5em"
          ></v-select>
          <v-text-field
            :label='categories[category].emailLabel'
            :suffix='categories[category].emailSuffix'
            v-model='emailPrefix'
            :rules='emailPrefixRules'
          ></v-text-field>
          <v-text-field
            :label='categories[category].usernameLabel'
            v-model='username'
            :rules='usernameRules'
          ></v-text-field>
          <v-text-field
            label='Password'
            v-model='password'
            :rules='passwordRules'
            type='password'
          ></v-text-field>
          <v-text-field
            label='Confirm password'
            v-model='confirmPassword'
            :rules='confirmPasswordRules'
            type='password'
          ></v-text-field>
          <v-checkbox
            v-model='tosAccepted'
            @change='tosCheckChange'
          >
            <span slot='label'>
              I read and accept the <a @click='tosCheckChange'>Terms of Service</a>
            </span>
          </v-checkbox>
          <v-checkbox
            @change='privacyCheckChange'
            v-model='privacyAccepted'
          >
            <span slot='label'>
              I read and accept the <a @click='privacyCheckChange'>Privacy Policy</a>
            </span>
          </v-checkbox>
          <policy
            mdUrl='https://raw.githubusercontent.com/UCCNetsoc/wiki/master/services/privacy-policy.md'
            v-on:accept='privacyAccepted = true; privacyVisible = false'
            v-on:decline='privacyAccepted = false; privacyVisible = false'
            :visible='privacyVisible'
          />
          <policy
            mdUrl='https://raw.githubusercontent.com/UCCNetsoc/wiki/master/services/terms-of-service.md'
            v-on:accept='tosAccepted = true; tosVisible = false'
            v-on:decline='tosAccepted = false; tosVisible = false'
            :visible='tosVisible'
          />
        </v-form>
      </v-card-text>
      <v-divider/>
      <v-card-actions class="justify-center ma-3">
        <v-btn v-on:click="submit()" color="green">Sign Up</v-btn>
        <v-btn v-on:click="$emit('cancelled')" color="red">Cancel</v-btn>
      </v-card-actions>
    </card-dialog>
    <card-dialog
      :visible="resultDialog.visible"
      width="480"
    >
      <v-card-text class="justify-center text-center">
        {{ this.resultDialog.msg }}
      </v-card-text>
      <v-card-actions class="justify-center mb-4">
        <v-btn v-on:click="closeResultDialog()" color="green">Okay</v-btn>
      </v-card-actions>
    </card-dialog>
  </v-container>
</template>

<script lang='ts'>
import Vue from 'vue'
import CardDialog from '@/components/CardDialog.vue'

import Policy from '@/components/Policy.vue'
import { config } from '@/config'
import { fetchRest } from '@/api/rest'
import { openApiGetSchemaProperty, openApiPropertyValidator } from '@/api/openapi'

export default Vue.extend({
  components: {
    CardDialog,
    Policy
  },

  props: {
    visible: {
      type: Boolean,
      default: true
    }
  },

  computed: {
    email () {
      return `${this.emailPrefix}${this.categories[this.category].emailSuffix}`
    },

    usernameRules () {
      return [
        (v: string) => !!v || 'Username required',
        openApiPropertyValidator(openApiGetSchemaProperty(this.categories[this.category].model, 'username'))
      ]
    },

    passwordRules () {
      return [
        (v: string) => !!v || 'Password required',
        openApiPropertyValidator(openApiGetSchemaProperty(this.categories[this.category].model, 'password'))
      ]
    },

    confirmPasswordRules () {
      return [
        () => (this.password === this.confirmPassword) || 'Passwords do not match'
      ]
    },

    emailPrefixRules () {
      return [
        (v: string) => !!v || 'Email required',
        (v: string) => openApiPropertyValidator(openApiGetSchemaProperty(this.categories[this.category].model, 'email'))(v + this.categories[this.category].emailSuffix)
      ]
    }
  },

  methods: {
    privacyCheckChange () {
      this.privacyVisible = true
    },

    tosCheckChange () {
      this.tosVisible = true
    },

    closeResultDialog () {
      this.resultDialog.visible = false

      console.log(this.successful)
      if (this.successful) {
        this.$emit('successful')
      }
    },

    async submit () {
      this.$refs.form.validate()

      if (!this.privacyAccepted) {
        this.resultDialog = {
          visible: true,
          msg: 'You must agree to the Privacy Policy to create an account'
        }
        return
      }

      if (!this.tosAccepted) {
        this.resultDialog = {
          visible: true,
          msg: 'You must agree to the Terms of Service to create an account'
        }
        return
      }

      if (!this.$refs.form.validate()) return

      try {
        await fetchRest(`${config.apiBaseUrl}/v1/signups/${this.categories[this.category].endpoint}`, {
          method: 'POST',
          body: JSON.stringify({
            email: this.email,
            username: this.username,
            password: this.password
          })
        })

        try {
          const verify = await fetchRest(`${config.apiBaseUrl}/v1/accounts/${this.email}/verification-email`, {
            method: 'POST'
          })

          const { detail } = await verify.json()

          this.resultDialog = {
            visible: true,
            msg: detail.msg
          }

          this.successful = (verify.status === 201)
        } catch (e) {
          this.resultDialog = {
            visible: true,
            msg: `Created your account but could not send verification email: (${e.message})`
          }
        }
      } catch (e) {
        this.resultDialog = {
          visible: true,
          msg: `Could not create your account: ${e.message}`
        }
      }
    }
  },

  mounted () {
    // openApiGetSpec(`${config.apiBaseUrl}/openapi.json`).then(
    //   (spec) => {
    //     this.openApiSpec = spec
    //   })
  },

  data: () => ({
    openApiSpec: undefined,

    tosVisible: false,
    privacyVisible: false,

    successful: false,

    resultDialog: {
      visible: false,
      text: ''
    },

    category: 'UCC student',

    username: '',
    emailPrefix: '',
    password: '',
    confirmPassword: '',
    signupReason: '',
    tosAccepted: false,
    privacyAccepted: false,

    categories: {
      'UCC student': {
        usernameLabel: 'Username',
        emailLabel: 'Student email address',
        emailSuffix: '@umail.ucc.ie',
        requiresReason: false,
        requiresApproval: false,
        model: 'UCCStudent',
        endpoint: 'ucc-student'
      }

      // 'UCC society': {
      //   usernameLabel: 'Society username',
      //   emailLabel: 'Society email address',
      //   emailSuffix: '@uccsocieties.ie',
      //   requiresReason: false,
      //   requiresApproval: false,
      //   model: 'UccSociety'
      // },

      // 'UCC staff member': {
      //   usernameLabel: 'Username',
      //   emailLabel: 'Staff email address',
      //   emailSuffix: '@ucc.ie',
      //   requiresReason: false,
      //   requiresApproval: false,
      //   model: 'UccStaff'
      // }
    }
  })

})
</script>
