import type { RouteRecordRaw } from 'vue-router'

/**
 * The signed-out surface (ADR-0027). Every route names its view directly and
 * the view is loaded on first visit, so the sign-in screen does not pull in the
 * conversation UI.
 */
export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/auth/sign-in',
    name: 'sign-in',
    component: () => import('@/features/auth/views/SignInView.vue'),
    meta: { title: 'Sign In', requiresAuth: false },
  },
  {
    path: '/auth/sign-up',
    name: 'sign-up',
    component: () => import('@/features/auth/views/SignupView.vue'),
    meta: { title: 'Sign Up', requiresAuth: false },
  },
  {
    // SuperTokens' backend handles the provider callback, then forwards the
    // browser here. The provider never sees this route.
    path: '/auth/callback',
    name: 'auth-callback',
    component: () => import('@/features/auth/views/AuthCallbackView.vue'),
    meta: { title: 'Sign In', requiresAuth: false },
  },
  {
    path: '/auth/forgot-password',
    name: 'forgot-password',
    component: () => import('@/features/auth/views/ForgotPasswordView.vue'),
    // Public, like the rest of `/auth`; stated explicitly rather than
    // left to inheritance (ADR-0027).
    meta: { title: 'Reset Password', requiresAuth: false },
  },
  {
    // The path is fixed by SuperTokens, which builds the emailed link as
    // `{website_base_path}/reset-password` with no trailing slash. Vue Router
    // matches the trailing-slash form to this route too.
    path: '/auth/reset-password',
    name: 'reset-password',
    component: () => import('@/features/auth/views/ResetPasswordView.vue'),
    meta: { title: 'Set a New Password', requiresAuth: false },
  },
  {
    // The path is fixed by the verification mail's template, which builds its
    // link as `{website_base_path}/verify-email` with the token in the query —
    // the same convention as reset-password above, and the same reason the
    // route is public.
    path: '/auth/verify-email',
    name: 'verify-email',
    component: () => import('@/features/auth/views/VerifyEmailView.vue'),
    meta: { title: 'Verify Email', requiresAuth: false },
  },
]
