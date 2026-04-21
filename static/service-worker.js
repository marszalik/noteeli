/*
 * Noteeli service worker.
 *
 * Goals:
 *  - make the app installable as a PWA
 *  - cache static assets + CDN libs so the UI shell keeps loading if the
 *    network is flaky or uvicorn is briefly down
 *
 * Explicit non-goals:
 *  - caching file content, API responses, OAuth, or anything non-GET —
 *    those must always go to the network so that saves, renames, uploads,
 *    and auth stay correct
 */

const VERSION = "noteeli-pwa-v3";
const APP_SHELL = [
  "/",
  "/static/app.js",
  "/static/app.css",
  "/static/favicon.svg",
  "/static/icon.svg",
  "/static/icon-192.png",
  "/static/icon-512.png",
  "/static/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(VERSION).then((cache) =>
      // addAll is atomic — if any asset 404s the install fails, which is what we want
      cache.addAll(APP_SHELL),
    ),
  );
  // new SW takes over as soon as install completes
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)),
      );
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("message", (event) => {
  if (event.data === "skipWaiting") self.skipWaiting();
});

// --- fetch strategies ---

const isSameOrigin = (url) => url.origin === self.location.origin;
const isStaticAsset = (url) =>
  isSameOrigin(url) && url.pathname.startsWith("/static/");

async function staleWhileRevalidate(request) {
  const cache = await caches.open(VERSION);
  const cached = await cache.match(request);
  const networkFetch = fetch(request)
    .then((response) => {
      if (response && response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached);
  return cached || networkFetch;
}

async function networkFirstNavigation(request) {
  const cache = await caches.open(VERSION);
  try {
    const response = await fetch(request);
    if (response && response.ok) cache.put("/", response.clone());
    return response;
  } catch (err) {
    const cached = await cache.match("/");
    if (cached) return cached;
    throw err;
  }
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // only intercept GET — anything else (POST/PUT/DELETE) goes straight to net
  if (request.method !== "GET") return;

  // ignore OAuth + auth flows — must always hit server
  if (isSameOrigin(url) && url.pathname.startsWith("/auth/")) return;

  // navigations: network-first, fall back to cached shell if offline
  if (request.mode === "navigate") {
    event.respondWith(networkFirstNavigation(request));
    return;
  }

  // same-origin static assets: stale-while-revalidate
  if (isStaticAsset(url)) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // cross-origin GET (CDN libs, fonts): stale-while-revalidate
  if (!isSameOrigin(url)) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // everything else same-origin (API, file content, tree, previews) — let it
  // go to the network untouched. Don't cache it.
});
