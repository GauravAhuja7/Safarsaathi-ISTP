import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/*.png", "audio/*.mp3"],
      manifest: {
        name: "SafarSathi — Mountain Travel Safety",
        short_name: "SafarSathi",
        description: "Mountain travel safety information for Mandi region, Himachal Pradesh",
        start_url: "/",
        display: "standalone",
        theme_color: "#1a6b3c",
        background_color: "#ffffff",
        lang: "hi",
        icons: [
          { src: "icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any maskable" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,mp3,woff2}"],
        runtimeCaching: [
          {
            urlPattern: ({ url }) =>
              url.pathname.startsWith("/routes") ||
              url.pathname.startsWith("/weather") ||
              url.pathname.startsWith("/emergency"),
            handler: "NetworkFirst",
            options: {
              cacheName: "api-cache",
              expiration: { maxEntries: 50, maxAgeSeconds: 60 * 60 * 8 },
              networkTimeoutSeconds: 5,
            },
          },
        ],
      },
    }),
  ],
  server: {
    host: "0.0.0.0",
    proxy: {
      "/routes": "http://localhost:8000",
      "/weather": "http://localhost:8000",
      "/emergency": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/reports": "http://localhost:8000",
      "/reporters": "http://localhost:8000",
      "/telegram": "http://localhost:8000",
      "/webhook": "http://localhost:8000",
    },
  },
});
