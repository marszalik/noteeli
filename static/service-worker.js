/*
 * Noteeli kill-switch service worker.
 *
 * Noteeli no longer ships a PWA / service worker — it only ever cached
 * static assets and that caused stale versions to linger in browsers.
 *
 * This file is intentionally a self-destruct: browsers re-check the SW
 * script byte-for-byte on navigation (independent of any cached app.js),
 * so a browser still running an old Noteeli SW will fetch THIS script,
 * install it, wipe every cache, unregister itself, and reload open tabs.
 * After that the page is served straight from the network. Keep serving
 * this file indefinitely so every lingering client eventually clears.
 */
self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      try {
        const keys = await caches.keys();
        await Promise.all(keys.map((k) => caches.delete(k)));
      } catch (_e) {}
      try {
        await self.registration.unregister();
      } catch (_e) {}
      // Reload any open tabs once so they re-fetch fresh assets without
      // the (now-removed) cache in the way.
      try {
        const clients = await self.clients.matchAll({ type: "window" });
        for (const client of clients) {
          client.navigate(client.url);
        }
      } catch (_e) {}
    })(),
  );
});

// No fetch handler: every request goes straight to the network.
