"use strict";

/* =============================================================
   Banco ENEM — Service Worker
   Estratégia (docs/skills/pwa-offline.md):
   - App shell (HTML/CSS/JS/ícone/manifest): cache-first com cache
     versionado; caches velhos são removidos no activate.
   - questions.json (2,48 MB) e taxonomy.json: stale-while-revalidate —
     serve o cache imediatamente e revalida em background.
   - Imagens das questões: entram no cache do shell sob demanda.
   - Nunca cacheia respostas com erro (status >= 500) nem não-GET.
   ============================================================= */

const VERSION = "v22"; // v22: transição em quadrados pretos; corrige "null" no tópico
const SHELL = "banco-enem-shell-" + VERSION;
const DATA = "banco-enem-data-" + VERSION;

const SHELL_ASSETS = [
  "./",
  "index.html",
  "styles.css",
  "js/base.js",
  "js/inicio.js",
  "js/topico.js",
  "js/simulado.js",
  "js/respostas.js",
  "js/resultado.js",
  "icon.svg",
  "manifest.json",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches
      .open(SHELL)
      .then((c) => c.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== SHELL && k !== DATA)
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // Só same-origin. Fontes (Google Fonts) ficam com o cache HTTP do navegador.
  if (url.origin !== self.location.origin) return;

  if (url.pathname.endsWith("questions.json") || url.pathname.endsWith("taxonomy.json")) {
    e.respondWith(staleWhileRevalidate(req));
  } else {
    e.respondWith(cacheFirst(req));
  }
});

async function cacheFirst(req) {
  const cached = await caches.match(req, { ignoreSearch: true });
  if (cached) return cached;
  try {
    const res = await fetch(req);
    if (res && res.ok && res.status < 500) {
      const c = await caches.open(SHELL);
      c.put(req, res.clone());
    }
    return res;
  } catch (err) {
    // Navegação offline: cai no shell, que é um app de página única.
    if (req.mode === "navigate") {
      const shell = await caches.match("index.html");
      if (shell) return shell;
    }
    throw err;
  }
}

async function staleWhileRevalidate(req) {
  const c = await caches.open(DATA);
  const cached = await c.match(req);
  const refresh = fetch(req)
    .then((res) => {
      if (res && res.ok && res.status < 500) c.put(req, res.clone());
      return res;
    })
    .catch(() => undefined);
  if (cached) return cached;
  const res = await refresh;
  if (res) return res;
  throw new Error("offline e sem cache de questões");
}
