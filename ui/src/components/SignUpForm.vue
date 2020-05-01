<template>
  <v-container>
    <v-card flat>
      <v-card-text>
        <v-form
          v-model='formValid'
          lazy-validation
          ref="form"
        >
          <v-select
            :items='Object.keys(categories)'
            label='I am a:'
            outlined
            v-model='category'
          ></v-select>
          <v-text-field
            :label='categories[category].nameLabel'
            v-model='displayname'
            :rules='displaynameRules'
          ></v-text-field>
          <v-text-field
            :label='categories[category].emailLabel'
            :suffix='categories[category].emailSuffix'
            v-model='emailPrefix'
            :rules='emailPrefixRules'
          ></v-text-field>
          <v-text-field
            label='Choose a username'
            v-model='username'
            :rules='usernameRules'
          ></v-text-field>
          <v-text-field
            label='Choose a password'
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
            v-model='aupAccepted'
            @change='aupCheckChange'
          >
            <span slot='label'>
              I read and accept the <a @click='aupCheckChange'>Acceptable Usage Policy</a>
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
          <privacy-policy
            v-on:accept='privacyAccepted = true; privacyVisible = false'
            v-on:decline='privacyAccepted = false; privacyVisible = false'
            :visible='privacyVisible'
          />
          <acceptable-usage-policy
            v-on:accept='aupAccepted = true; aupVisible = false'
            v-on:decline='aupAccepted = false; aupVisible = false'
            :visible='aupVisible'
          />
        </v-form>
      </v-card-text>
    </v-card>
    <v-divider class='ma-2'/>
    <v-card-actions class="justify-center">
      <v-btn v-on:click="$router.push('/login', () => {})" color="primary">Login</v-btn>
      <v-btn v-on:click="submit()" color="green">Sign Up</v-btn>
    </v-card-actions>
    <v-dialog
      v-model="dialog.visible"
      width="460"
      persistent
      :fullscreen="$vuetify.breakpoint.mdAndDown"
      class="ma-4"
      scrollable
    >
      <v-card>
        <dialog-logo/>
        <v-card-text class="my-2">
          <p class="my-2 text-center">
            {{ dialog.msg }}
          </p>
          <v-card-actions class="justify-center">
            <v-btn v-on:click="dialog.visible = false" color="green">Okay</v-btn>
          </v-card-actions>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang='ts'>
import Vue from 'vue'
import DialogLogo from '@/components/DialogLogo.vue'
import AcceptableUsagePolicy from '@/components/AcceptableUsagePolicy.vue'
import PrivacyPolicy from '@/components/PrivacyPolicy.vue'
import Config from '../config'
import { openApiPropertyValidateData, openApiGetSpec, openApiGetSchemaProperty } from '../api/'

function vuetifyRuleFromOpenApiSpec (spec, model: string, property: string, value: string) {
  if (spec !== undefined) {
    const prop = openApiGetSchemaProperty(spec, model, property)
    if (!openApiPropertyValidateData(prop, value)) {
      return prop.description || 'Invalid'
    }
  }

  return true
}

export default Vue.extend({
  name: 'SignUpForm',
  components: {
    AcceptableUsagePolicy,
    PrivacyPolicy,
    DialogLogo
  },
  computed: {
    email () {
      return `${this.emailPrefix}${this.categories[this.category].emailSuffix}`
    },

    displaynameRules () {
      return [
        (v: string) => !!v || 'Display name required',
        (v: string) => vuetifyRuleFromOpenApiSpec(this.openApiSpec, this.categories[this.category].model, 'displayname', v)
      ]
    },

    usernameRules () {
      return [
        (v: string) => !!v || 'Name required',
        (v: string) => vuetifyRuleFromOpenApiSpec(this.openApiSpec, this.categories[this.category].model, 'username', v)
      ]
    },

    passwordRules () {
      return [
        (v: string) => !!v || 'Password required',
        (v: string) => vuetifyRuleFromOpenApiSpec(this.openApiSpec, this.categories[this.category].model, 'password', v)
      ]
    },

    confirmPasswordRules () {
      return [
        () => (this.password === this.confirmPassword) || 'Passwords do not match'
      ]
    },

    emailPrefixRules () {
      return [
        (v: string) => !!v || 'Password required',
        (v: string) => vuetifyRuleFromOpenApiSpec(this.openApiSpec, this.categories[this.category].model, 'email', v + this.categories[this.category].emailSuffix)
      ]
    }
  },

  methods: {
    privacyCheckChange () {
      if (!this.privacyAccepted) {
        this.privacyVisible = true
      }
    },

    aupCheckChange () {
      if (!this.aupAccepted) {
        this.aupVisible = true
      }
    },

    async submit () {
      this.refs.$form.validate()

      if (!this.privacyAccepted) {
        this.dialog = {
          visible: true,
          msg: 'You must agree to the privacy policy to create an account'
        }
        return
      }

      if (this.formValid) {
        try {
          const res = await fetch(`${Config.accountApiBaseUrl}/accounts/signup/${this.categories[this.category].model}`, {
            method: 'POST',
            body: JSON.stringify({
              displayname: this.displayname,
              email: this.email,
              username: this.username,
              password: this.password
            })
          })

          switch (true) {
            case (res.status === 201): {
              this.dialog.visible = true
              const { detail } = await res.json()
              this.dialog = {
                visible: true,
                msg: detail.msg
              }
              break
            }

            case (res.status >= 400): {
              this.dialog.visible = true
              const { detail } = await res.json()
              this.dialog = {
                visible: true,
                msg: detail.msg
              }
              break
            }
          }
        } catch (e) {
          this.dialog = {
            visible: true,
            msg: `Could not create your account. An unexpected error happened.\nIf you're in contact with a SysAdmin give them this: ${e}`
          }
        }
      }
    }
  },

  mounted () {
    openApiGetSpec(`${Config.accountApiBaseUrl}/openapi.json`).then(
      (spec) => {
        this.openApiSpec = spec
      })
  },

  data: () => ({
    openApiSpec: undefined,

    formValid: false,

    aupVisible: false,
    privacyVisible: false,

    dialog: {
      visible: false,
      text: ''
    },

    category: 'UCC student',
    displayname: '',
    username: '',
    emailPrefix: '',
    password: '',
    confirmPassword: '',
    signupReason: '',
    aupAccepted: false,
    privacyAccepted: false,

    categories: {
      'UCC student': {
        nameLabel: 'Your name',
        emailLabel: 'Student email address',
        emailSuffix: '@umail.ucc.ie',
        requiresReason: false,
        requiresApproval: false,
        model: 'UccStudent'
      },

      'UCC society': {
        nameLabel: 'Society name',
        emailLabel: 'Society email address',
        emailSuffix: '@uccsocieties.ie',
        requiresReason: false,
        requiresApproval: false,
        model: 'UccSociety'
      },

      'UCC staff member': {
        nameLabel: 'Your name',
        emailLabel: 'Staff email address',
        emailSuffix: '@ucc.ie',
        requiresReason: false,
        requiresApproval: false,
        model: 'UccStaff'
      }
    },

    passwordForgotRememberCategories: ['Email address', 'Server username'],
    passwordForgotRememberCategory: 'Email address'
  })

})
</script>
