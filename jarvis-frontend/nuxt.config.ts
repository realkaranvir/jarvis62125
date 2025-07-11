// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@nuxt/ui',
    '@nuxt/eslint',
    '@nuxt/fonts',
    '@nuxt/icon'
  ],

  css: ['~/assets/css/main.css'],

  future: {
    compatibilityVersion: 4
  },

  app: {
    baseURL: '/jarvis62125/',
    buildAssetsDir: 'assets',
  },

  compatibilityDate: '2024-11-27'
})