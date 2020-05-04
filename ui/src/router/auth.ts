
import { VueConstructor } from 'vue'
import Router, { Route } from 'vue-router'

import Landing from '@/views/Landing.vue'
import store from '@/store'
import userManager from '../userManager'

/**
 * Return a component with a beforeRouteEnter hook which will redirect to the homepage if the auth module user is null (i.e not signed in)
 * @param component The component
 */
export function requireAuth (component: VueConstructor) {
  return component.extend({
    beforeRouteEnter (to: Route, from: Route, next: Function) {
      // Render the component
      next((component: Landing) => {
        // If they're not authenticated send them to the homepage
        if (component.$store.state.auth.user === null) {
          component.$router.replace('/')
        }
      })
    }
  })
}

export function useAuthRoutes (router: Router) {
  // Setup auth routes
  const loginRedirectUrl = new URL(userManager.settings.redirect_uri as string)
  const silentRedirectUrl = new URL(userManager.settings.silent_redirect_uri as string)
  const logoutRedirectUrl = new URL(userManager.settings.post_logout_redirect_uri as string)

  // Before every route hook (this is before any beforeRouteEnter hook on the component to be rendered)
  router.beforeEach((to: Route, _from: Route, next: Function) => {
    // Don't let auth routes hit the silent sign in, prevents a loop
    if ([
      '/login',
      '/logout',
      loginRedirectUrl.pathname,
      silentRedirectUrl.pathname,
      logoutRedirectUrl.pathname
    ].includes(to.path)) {
      next()
      return
    }

    // If user is unauthenticated
    if (store.state.auth.user === null) {
      // Try to silently sign them in (doesn't open a window or prompt)
      // We need to do this sometimes because the user might have a cookie on the SSO domain (keycloak)
      // i.e they're signed on the keycloak page but not on our page
      userManager.signinSilent()
        // User authenticated, send them on their way
        .then(() => next())
        // Authentication failed, however we don't know if the page they're going to requires auth or not
        // so send them there anyway. The beforeRouteEnter hook on the component they're going to
        // will handle it by forcing them to auth then (assuming it requires auth)
        .catch(() => next())
    } else {
      // User already authenticated
      next()
    }
  })

  // Redirect user home if silent renew fails
  // i.e they logged out in another tab
  userManager.events.addSilentRenewError(() => {
    if (router.currentRoute.path !== '/') {
      router.replace('/')
    }
  })

  router.addRoutes([
    {
      path: '/login',
      component: Landing.extend({
        beforeRouteEnter (_to: Route, _from: Route, next: Function) {
          userManager.signinPopup()
            .then(() => {
              next(false)
            })
            .catch(() => {
              next(false)
            })
        }
      })
    },
    {
      path: loginRedirectUrl.pathname,
      component: Landing,
      beforeEnter (_to: Route, _from: Route, next: Function) {
        userManager.signoutPopupCallback(window.location.href.split('?')[1])
        next(false)
      }
    },
    {
      path: silentRedirectUrl.pathname,
      component: Landing,
      beforeEnter (_to: Route, _from: Route, next: Function) {
        userManager.signinSilentCallback(window.location.href.split('?')[1])
        // Don't bother rendering the page because it's not visible
        next(false)
      }
    },
    {
      path: '/logout',
      component: Landing.extend({
        beforeRouteEnter (_to: Route, from: Route, next: Function) {
          userManager.signoutPopup()
            .then(() => {
              if (from.path !== '/') {
                next((landing: Landing) => {
                  landing.$router.replace('/')
                })
              } else {
                next(false)
              }
            })
            .catch(() => {
              next((landing: Landing) => {
                landing.$router.replace('/')
              })
            })
        }
      })
    },
    {
      path: logoutRedirectUrl.pathname,
      component: Landing,
      beforeEnter (_to: Route, _from: Route, next: Function) {
        userManager.signoutPopupCallback(window.location.href.split('?')[1])
        next(false)
      }
    }
  ])

  // router.addRoutes([

  // ])

  // Because the first time the user hits / vue-router isn't initialized yet
  // and no route is hit, we need to check silent sign in manually
  // The .catch() prevents an exception from happening if the user doesn't have a cookie on SSO (i.e not signed in on Keycloak)
  // userManager.signinSilent()
  //   .catch(() => {}) // eslint-disable-line @typescript-eslint/no-empty-function

  //   router.addRoutes([
  //     {
  //       path: '/login',
  //       component: Landing.extend({
  //         beforeRouteEnter (to: Route, from: Route, next: Function) {
  //           // Open the sign in popup, which when the user signs in will go to /<redirectUrl>
  //           // oidc-client will resolve this promise when signinPopupCallback is ran in the route handler for /<redirectUrl>
  //           userManager.signinPopup()
  //             .then(() => {
  //               // Render the component
  //               next((landing: Landing) => {
  //                 // Send the user back to where they came from
  //                 landing.$router.back()
  //               })
  //             })
  //             .catch((reason: Error) => {
  //               console.log(`Could not authenticate user: ${reason}`)

//               // Send them back to the homepage
//               next('/')
//             })
//         }
//       })
//     },
//     {
//       path: redirectUrl.pathname,
//       component: Landing,
//       beforeEnter: (to: Route, from: Route, next: Function) => {
//         // BUG:
//         // https://github.com/IdentityModel/oidc-client-js/issues/937
//         // Currently need to split the href string due to a bug when
//         // passing it into signin*
//         userManager.signinPopupCallback(window.location.href.split('?')[1])
//           .catch((reason) => {
//             console.log(`Could not handle the redirect for regular sign in: ${reason}`)
//             next()
//           })
//       }
//     },
//     {
//       path: silentRedirectUrl.pathname,
//       component: Landing,
//       beforeEnter: (to: Route, from: Route, next: Function) => {
//         // BUG:
//         // https://github.com/IdentityModel/oidc-client-js/issues/937
//         // Currently need to split the href string due to a bug when
//         // passing it into signin*
//         userManager.signinSilentCallback(window.location.href.split('?')[1])
//           .then(() => {
//             next(false)
//           })
//           .catch((reason) => {
//             console.log(`Could not handle the redirect for silent sign in: ${reason}`)
//             next(false)
//           })
//       }
//     },
//     {
//       path: '/logout',
//       component: Landing.extend({
//         beforeRouteEnter (to: Route, from: Route, next: Function) {
//           // Open the sign out popup, which when the user signs out will go to /<loggedOutUrl>
//           userManager.signoutPopup()
//             .then(() => {
//               if (from.path !== '/') {
//                 next('/')
//               } else {
//                 next(false)
//               }
//             })
//             .catch((reason: Error) => {
//               console.log(`Could not sign out user: ${reason}`)
//               next(false)
//             })
//         }
//       })
//     },
//     {
//       path: loggedOutUrl.pathname,
//       component: Landing,
//       beforeEnter: (_: Route, __: Route, next: Function) => {
//       // BUG:
//       // https://github.com/IdentityModel/oidc-client-js/issues/937
//       // Currently need to split the href string due to a bug when
//       // passing it into signin*
//         userManager.signoutPopupCallback(window.location.href.split('?')[1]).then(() => {
//           next(false)
//         })
//       }
//     }
//   ])
// })
}
