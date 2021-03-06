import Vue from 'vue'
import VueRouter, { Route } from 'vue-router'
import Landing from '@/views/Landing.vue'
import SignUp from '@/views/SignUp.vue'
import SignUpVerify from '@/views/SignUpVerify.vue'
import SignUpResendVerify from '@/views/SignUpResendVerify.vue'
import PasswordReset from '@/views/PasswordReset.vue'
import PasswordSet from '@/views/PasswordSet.vue'

import Account from '@/views/Account.vue'
import About from '@/views/About.vue'
import Instances from '@/views/Instances.vue'
import InstanceRequest from '@/views/InstanceRequest.vue'
import InstanceFileManager from '@/views/InstanceFileManager.vue'

import Terminal from '@/views/Terminal.vue'
import { useAuthRoutes, requireAuth } from './auth'
import { compile } from 'vue/types/umd'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: '',
    component: Landing
  },
  {
    path: '/accounts/sign-up',
    name: 'Sign Up',
    component: SignUp
  },
  {
    path: '/accounts/verification-email',
    name: 'Resend Verification',
    component: SignUpResendVerify
  },
  {
    path: '/account/:emailOrUsername/verification-email',
    name: 'Reend Verification',
    component: SignUpResendVerify
  },
  {
    path: '/account/:emailOrUsername/verification/:token',
    name: 'Account Verification',
    component: SignUpVerify
  },
  {
    path: '/accounts/verification',
    name: 'Account Verification',
    component: SignUpVerify
  },
  {
    path: '/accounts/password-reset',
    name: 'Password Reset',
    component: PasswordReset
  },
  {
    path: '/account/:emailOrUsername/password-reset',
    name: 'Password Reset',
    component: PasswordReset
  },
  {
    path: '/account/:emailOrUsername/password/:token',
    name: 'Password Set',
    component: PasswordSet
  },
  {
    path: '/account',
    name: 'Account',
    component: requireAuth(Account)
  },
  {
    path: '/instances',
    name: 'Instances',
    component: requireAuth(Instances)
  },
  {
    path: '/instance-request/:emailOrUsername/:instanceRequestType/:hostname/:token',
    name: 'Instance Request',
    component: requireAuth(InstanceRequest)
  },
  {
    path: '/tutorial',
    name: 'Tutorial',
    beforeEnter (_to: Route, _from: Route, next: Function) {
      const popupWindowFeatures: { [k: string]: string | number } = {
        status: 'no',
        location: 'no',
        toolbar: 'no',
        menubar: 'no',
        resizable: 'no',
        width: 500,
        height: 620,
        left: (window.screen.width / 2) - (500 / 2),
        top: (window.screen.height / 2) - (600 / 2)
      }

      const featureStr = Object.keys(popupWindowFeatures).reduce(
        (prev: string, cur: string, _: number, __: string[]) => {
          return `${prev},${cur}=${popupWindowFeatures[cur]}`
        }, '')

      window.open('https://wiki.netsoc.co/en/services/tutorial', '_blank', featureStr)
      next(false)
    }
  },
  {
    path: '/terminal',
    name: 'Terminal',
    component: requireAuth(Terminal)
  },
  {
    path: '/wiki',
    name: 'wiki',
    beforeEnter (_to: Route, _from: Route, next: Function) {
      window.open('https://wiki.netsoc.co')
      next(false)
    }
  },
  {
    path: '/about',
    name: 'About',
    component: requireAuth(About)
  },
  {
    path: '*',
    name: '404',
    component: Landing.extend({
      beforeRouteEnter (_, __, next: Function) {
        next('/')
      }
    })
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

useAuthRoutes(router)

router.afterEach((to: Route) => {
  Vue.nextTick(() => {
    if (to?.name) {
      document.title = `${to?.name} | Netsoc Cloud`
    } else {
      document.title = 'Netsoc Cloud | UCC Netsoc'
    }
  })
})

export default router
