// 50720f97afeb is replaced with the commit id on deploy, so every push is a new version
const CACHE = "seal-player-50720f97afeb";
const SHELL = ["./", "./manifest.json", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/apple-touch-icon.png", "./icons/icon-maskable-512.png"];

// Safari refuses to show a page from a response that went through a redirect
// (Cloudflare Pages 308s /index.html -> /), so store a clean copy instead.
async function clean(res) {
  if (!res.redirected) return res;
  const body = await res.blob();
  return new Response(body, { status: res.status, statusText: res.statusText, headers: res.headers });
}

async function store(cache, key, res) {
  if (res && res.ok && res.type === "basic") await cache.put(key, await clean(res.clone()));
}

self.addEventListener("install", (event) => {
  // cache each file separately so one missing file can't break the install
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => Promise.all(SHELL.map((u) =>
        fetch(u, { cache: "reload" }).then((res) => store(cache, u, res)).catch(() => {})
      )))
      // first install takes over straight away; later versions wait for the page to say "update"
      .then(() => { if (!self.registration.active) return self.skipWaiting(); })
  );
});

self.addEventListener("message", (event) => {
  if (event.data === "update") self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// The app always opens from this version's saved copy (instant, works offline).
// New versions arrive by installing a new worker, which the page offers as an update.
// Every page URL (/, /index.html, ?query) is served from the one saved app shell.
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  const key = req.mode === "navigate" ? "./" : req;
  event.respondWith(
    caches.open(CACHE).then((cache) =>
      cache.match(key, { ignoreSearch: req.mode === "navigate" }).then((hit) => hit ||
        fetch(req).then(async (res) => {
          const out = await clean(res);
          if (out.ok && out.type === "basic") cache.put(key, out.clone());
          return out;
        })
      )
    )
  );
});
