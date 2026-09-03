/* BloodLink PWA service worker. Live medical API data is never cached. */
const CACHE_NAME = "bloodlink-shell-v1";
const OFFLINE_URL = "/static/pwa/offline.html";
const APP_SHELL = [OFFLINE_URL, "/static/pwa/icon-192.png", "/static/pwa/icon-512.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;

  // Always try the deployed server first. Cached files are an offline fallback
  // only, preventing a prior deployment from looking like current data.
  event.respondWith(fetch(new Request(request, { cache: "no-store" })).then((response) => {
    if (response.ok && (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest")) {
      const copy = response.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
    }
    return response;
  }).catch(async () => {
    if (request.mode === "navigate") return (await caches.match(OFFLINE_URL)) || Response.error();
    return (await caches.match(request)) || Response.error();
  }));
});

self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) { data = {}; }
  event.waitUntil(self.registration.showNotification(data.title || "BloodLink blood request", {
    body: data.body || "A new blood request needs your attention.",
    icon: "/static/pwa/icon-192.png",
    badge: "/static/pwa/icon-192.png",
    tag: data.tag || "bloodlink-request",
    renotify: true,
    data: { url: data.url || "/donor-dashboard" },
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = new URL(event.notification.data?.url || "/donor-dashboard", self.location.origin).href;
  event.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
    const existing = clients.find((client) => client.url.startsWith(self.location.origin));
    if (existing) return existing.navigate(target).then(() => existing.focus());
    return self.clients.openWindow(target);
  }));
});
