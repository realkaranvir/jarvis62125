// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@nuxt/ui',
    '@nuxt/eslint',
    '@nuxt/fonts',
    '@nuxt/icon',
    '@vite-pwa/nuxt'
  ],

  pwa: {
    manifest: {
      name: "Jarvis",
      short_name: "Jarvis",
      theme_color: '#003399',
      description: "Jarvis",
      icons: [
        {
          src: "icons/icon-144.png",
          sizes: "144x144",
          type: "image/png"
        },
        {
          src: "icons/icon-192.png",
          sizes: "192x192",
          type: "image/png"
        },
        {
          src: "icons/icon-512.png",
          sizes: "512x512",
          type: "image/png"
        },
      ]
    },
    workbox: {
      navigateFallback: "/",

    },
    devOptions: {
      enabled: true,
      type: "module",
      suppressWarnings: true
    }
  },

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