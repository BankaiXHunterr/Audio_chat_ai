// import { defineConfig } from "vite";
// import react from "@vitejs/plugin-react-swc";
// import path from "path";
// import { componentTagger } from "lovable-tagger";

// // https://vitejs.dev/config/
// export default defineConfig(({ mode }) => ({
//   server: {
//     host: "::",
//     port: 8080,
//   },
//   plugins: [
//     react(),
//     mode === 'development' &&
//     componentTagger(),
//   ].filter(Boolean),
//   resolve: {
//     alias: {
//       "@": path.resolve(__dirname, "./src"),
//     },
//   },
// }));




// vite.config.ts

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";
import { VitePWA } from 'vite-plugin-pwa'; // 1. Import the PWA plugin

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [
    react(),

    // 2. Add the VitePWA plugin configuration here
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      workbox: {
        // THIS IS THE CRITICAL FIX for the OAuth redirect issue.
        // It tells the service worker NOT to handle navigation for the root URL,
        // allowing Supabase to process the authentication tokens.
        navigateFallbackDenylist: [/^\/$/],
      },
      // 3. Add a basic manifest for PWA "Add to Homescreen" functionality
      manifest: {
        name: 'AudioChat AI',
        short_name: 'AudioChatAI',
        description: 'An AI-powered meeting summarization tool.',
        theme_color: '#ffffff',
        icons: [
          {
            src: 'icon-192x192.png', // You will need to create these icon files
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'icon-512x512.png', // in your public directory
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    }),

    // Your existing conditional plugin
    mode === 'development' &&
    componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));