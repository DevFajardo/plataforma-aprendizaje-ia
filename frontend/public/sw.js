/* Service worker de Aprendizaje Activo CUL (PWA).
 *
 * Qué cachea:
 *  - El «shell»: la página sin conexión y los iconos (al instalar).
 *  - Recursos estáticos de Next (/_next/static/*, con nombre de archivo único por versión): primero caché.
 *  - Páginas de navegación: primero la red; si no hay conexión, la última copia o la página «Sin conexión».
 * Qué NO hace nunca:
 *  - No toca /api ni ninguna petición a otro origen (el backend suele estar en otro origen).
 *  - No intercepta WebSockets (la clase en vivo): el navegador no los pasa por el service worker.
 *  - Solo atiende peticiones GET.
 */
const VERSION = "aa-cul-v1";
const CACHE_SHELL = `${VERSION}-shell`;
const CACHE_PAGINAS = `${VERSION}-paginas`;
const CACHE_ESTATICOS = `${VERSION}-estaticos`;
const PAGINA_OFFLINE = "/offline.html";
const PRECACHE = [PAGINA_OFFLINE, "/icons/icono-192.png", "/icons/icono-512.png", "/manifest.webmanifest"];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(CACHE_SHELL).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((nombres) => Promise.all(nombres.filter((n) => !n.startsWith(VERSION)).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

function esApi(url) {
  return url.pathname === "/api" || url.pathname.startsWith("/api/");
}

self.addEventListener("fetch", (evento) => {
  const peticion = evento.request;
  if (peticion.method !== "GET") return;
  const url = new URL(peticion.url);
  if (url.origin !== self.location.origin || esApi(url)) return; // otro origen, API: directo a la red

  // Páginas: red primero, con copia y página «Sin conexión» de respaldo
  if (peticion.mode === "navigate") {
    evento.respondWith(
      fetch(peticion)
        .then((respuesta) => {
          if (respuesta.ok) {
            const copia = respuesta.clone();
            caches.open(CACHE_PAGINAS).then((c) => c.put(peticion, copia));
          }
          return respuesta;
        })
        .catch(async () => (await caches.match(peticion)) || (await caches.match(PAGINA_OFFLINE)) || Response.error()),
    );
    return;
  }

  // Estáticos de Next e iconos: caché primero
  if (url.pathname.startsWith("/_next/static/") || url.pathname.startsWith("/icons/")) {
    evento.respondWith(
      caches.match(peticion).then(
        (guardada) =>
          guardada ||
          fetch(peticion).then((respuesta) => {
            if (respuesta.ok) {
              const copia = respuesta.clone();
              caches.open(CACHE_ESTATICOS).then((c) => c.put(peticion, copia));
            }
            return respuesta;
          }),
      ),
    );
  }
});
