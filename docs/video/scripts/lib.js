// Utilidades compartidas para grabar el video de demostración con Playwright.
// Cursor visible, subtítulos (caption), movimientos suaves y grabación por escena.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.BASE_URL || "http://localhost:3000";
const API = process.env.API_URL || "http://localhost:8000";
const CLAVE = process.env.DEMO_PASS || "Demo12345"; // contraseña de las cuentas de demostración (datos ficticios)
const OUT = path.resolve(process.env.VIDEO_OUT || path.join(__dirname, "salida"));
const CLIPS = path.join(OUT, "clips");
const AUTH = path.join(OUT, "auth");
for (const d of [OUT, CLIPS, AUTH]) fs.mkdirSync(d, { recursive: true });

const AZUL = "#0B468A", AZUL_OSCURO = "#172741", NARANJA = "#E88A37";

// Script inyectado en cada página: punto de cursor + barra de subtítulo que sobreviven a la navegación.
const OVERLAY = `(() => {
  const AZ = "${AZUL_OSCURO}", NA = "${NARANJA}";
  const iniciar = () => {
    if (document.getElementById("__demo_cursor")) return;
    const st = document.createElement("style");
    st.textContent = \`
      #__demo_cursor{position:fixed;left:0;top:0;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;background:\${NA};
        border:3px solid #fff;box-shadow:0 2px 10px rgba(0,0,0,.45);z-index:2147483647;pointer-events:none;opacity:0;transition:opacity .3s, transform .08s linear}
      #__demo_cursor.on{opacity:.95}
      #__demo_cursor.down{transform:scale(.75)}
      .__demo_ripple{position:fixed;width:20px;height:20px;margin:-10px 0 0 -10px;border-radius:50%;border:4px solid \${NA};z-index:2147483646;
        pointer-events:none;animation:__rip .6s ease-out forwards}
      @keyframes __rip{to{transform:scale(4);opacity:0}}
      #__demo_cap{position:fixed;left:50%;transform:translateX(-50%);width:max-content;max-width:min(1500px,90vw);z-index:2147483645;pointer-events:none;
        background:rgba(23,39,65,.93);color:#fff;border-left:8px solid \${NA};border-radius:10px;
        padding:.55em 1.1em;font-family:Montserrat,"Segoe UI",system-ui,sans-serif;font-weight:600;line-height:1.3;
        text-align:left;box-shadow:0 6px 24px rgba(0,0,0,.35);opacity:0;transition:opacity .45s}
      #__demo_cap.on{opacity:1}\`;
    document.head.appendChild(st);
    const c = document.createElement("div"); c.id = "__demo_cursor"; document.body.appendChild(c);
    const cap = document.createElement("div"); cap.id = "__demo_cap"; document.body.appendChild(cap);
    const mover = (x, y) => { c.style.left = x + "px"; c.style.top = y + "px"; c.classList.add("on"); try { sessionStorage.setItem("__cur", x + "," + y); } catch (e) {} };
    try { const p = sessionStorage.getItem("__cur"); if (p) { const [x, y] = p.split(",").map(Number); mover(x, y); } } catch (e) {}
    addEventListener("mousemove", (e) => mover(e.clientX, e.clientY), true);
    addEventListener("pointermove", (e) => mover(e.clientX, e.clientY), true);
    const ripple = (e) => { mover(e.clientX, e.clientY); c.classList.add("down");
      const r = document.createElement("div"); r.className = "__demo_ripple"; r.style.left = e.clientX + "px"; r.style.top = e.clientY + "px";
      document.body.appendChild(r); setTimeout(() => r.remove(), 700); };
    addEventListener("pointerdown", ripple, true);
    addEventListener("pointerup", () => c.classList.remove("down"), true);
    window.__setCap = (t, bottom) => {
      const fs = Math.max(15, Math.round(innerWidth * 0.0167));
      cap.style.fontSize = fs + "px";
      cap.style.bottom = (bottom != null ? bottom : (innerWidth < 600 ? 90 : 56)) + "px";
      try { sessionStorage.setItem("__cap", JSON.stringify([t, bottom == null ? null : bottom])); } catch (e) {}
      if (!t) { cap.classList.remove("on"); return; }
      cap.textContent = t; cap.classList.add("on");
    };
    try { const s = JSON.parse(sessionStorage.getItem("__cap") || "null"); if (s && s[0]) window.__setCap(s[0], s[1]); } catch (e) {}
  };
  if (document.body) iniciar(); else addEventListener("DOMContentLoaded", iniciar);
})();`;

const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
const esperar = (p, ms) => p.waitForTimeout(ms);

async function caption(p, texto, bottom) {
  await p.evaluate(([t, b]) => window.__setCap && window.__setCap(t, b), [texto, bottom ?? null]).catch(() => {});
}

const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

async function posicion(p) {
  return p.evaluate(() => {
    try { const s = sessionStorage.getItem("__cur"); if (s) return s.split(",").map(Number); } catch (e) {}
    return [innerWidth / 2, innerHeight / 2];
  }).catch(() => [0, 0]);
}

/** Mueve el cursor de forma visible y suave hasta (x, y). */
async function moverA(p, x, y) {
  const [x0, y0] = await posicion(p);
  const d = Math.hypot(x - x0, y - y0);
  const n = Math.max(14, Math.min(70, Math.round(d / 14)));
  for (let i = 1; i <= n; i++) {
    const t = ease(i / n);
    await p.mouse.move(x0 + (x - x0) * t, y0 + (y - y0) * t);
    await p.waitForTimeout(13);
  }
}

/** Desplaza suavemente la página `dy` píxeles en pasos pequeños. */
async function scrollSuave(p, dy, pasoMs = 1200) {
  await p.evaluate((d) => window.scrollBy({ top: d, behavior: "smooth" }), dy);
  await p.waitForTimeout(pasoMs);
}

/** Recorre la página de arriba abajo en pasos con pausa. */
async function recorrer(p, { paso = 520, pausa = 1800, max = 99 } = {}) {
  for (let i = 0; i < max; i++) {
    const fin = await p.evaluate(() => innerHeight + scrollY >= document.documentElement.scrollHeight - 4);
    if (fin) break;
    await scrollSuave(p, paso, 900);
    await esperar(p, pausa);
  }
}

async function arriba(p, ms = 1500) {
  await p.evaluate(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  await p.waitForTimeout(ms);
}

/** Lleva el elemento al centro vertical (suave). */
async function centrar(p, loc, offset = 0) {
  const el = loc.first();
  await el.waitFor({ state: "visible", timeout: 20000 });
  const dy = await el.evaluate((e, off) => {
    const r = e.getBoundingClientRect();
    return r.top + r.height / 2 - innerHeight / 2 + off;
  }, offset);
  if (Math.abs(dy) > 40) await scrollSuave(p, dy, Math.min(1800, 600 + Math.abs(dy) * 0.6));
}

async function centroDe(loc) {
  const b = await loc.first().boundingBox();
  return [b.x + b.width / 2, b.y + b.height / 2];
}

/** Mueve el cursor hasta el elemento (sin hacer clic). */
async function apuntar(p, loc, { scroll = true, offset = 0 } = {}) {
  if (scroll) await centrar(p, loc, offset);
  const [x, y] = await centroDe(loc);
  await moverA(p, x, y);
}

/** Cursor visible hasta el elemento, pausa breve y clic. */
async function clic(p, loc, opts = {}) {
  await apuntar(p, loc, opts);
  await esperar(p, opts.antes ?? 350);
  const [x, y] = await centroDe(loc);
  await p.mouse.click(x, y);
  await esperar(p, opts.despues ?? 500);
}

/** Escribe como una persona (60 ms por carácter). */
async function escribir(p, loc, texto, { delay = 60 } = {}) {
  await clic(p, loc, { despues: 200 });
  await loc.first().pressSequentially(texto, { delay });
  await esperar(p, 400);
}

/** Contexto con sesión guardada (sin mostrar el login). */
async function guardarSesion(browser, rol) {
  const f = path.join(AUTH, rol + ".json");
  const c = await browser.newContext();
  const p = await c.newPage();
  await p.goto(BASE + "/login");
  await p.fill('input[type="email"]', rol + "@demo.com");
  await p.fill('input[type="password"]', CLAVE);
  await p.click('button[type="submit"]');
  await p.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 30000 });
  await p.waitForTimeout(1500);
  const omitir = p.getByRole("button", { name: "Omitir" });
  if (await omitir.count()) await omitir.click().catch(() => {});
  await p.waitForTimeout(600);
  await c.storageState({ path: f });
  await c.close();
  return f;
}

let _browser;
async function navegador() {
  if (!_browser) _browser = await chromium.launch({ args: ["--force-device-scale-factor=1", "--hide-scrollbars"] });
  return _browser;
}
async function cerrarNavegador() { if (_browser) await _browser.close(); _browser = null; }

/**
 * Graba una escena. `fn({ page, ctx, browser, listo })`: llamar `await listo()` cuando ya hay contenido
 * (todo lo anterior se recorta del clip).
 */
async function escena(nombre, fn, { rol, movil = false, ancho = 1920, alto = 1080 } = {}) {
  const browser = await navegador();
  const vp = movil ? { width: 390, height: 844 } : { width: ancho, height: alto };
  const opts = {
    viewport: vp,
    recordVideo: { dir: path.join(OUT, "tmp_" + nombre), size: vp },
    locale: "es-CO",
    deviceScaleFactor: 1,
    ...(movil ? { isMobile: true, hasTouch: true } : {}),
  };
  if (rol) opts.storageState = fs.existsSync(path.join(AUTH, rol + ".json")) ? path.join(AUTH, rol + ".json") : await guardarSesion(browser, rol);
  const ctx = await browser.newContext(opts);
  await ctx.addInitScript(OVERLAY);
  const t0 = Date.now();
  const page = await ctx.newPage();
  let inicio = 0;
  const acelerar = [];
  const t = () => (Date.now() - t0) / 1000;
  const listo = async () => { inicio = t() + 0.35; };
  try {
    await fn({ page, ctx, browser, listo, t, acelerar });
    await esperar(page, 1200);
  } finally {
    const video = page.video();
    await ctx.close();
    if (video) {
      const dest = path.join(CLIPS, nombre + ".webm");
      fs.copyFileSync(await video.path(), dest);
      fs.writeFileSync(path.join(CLIPS, nombre + ".json"), JSON.stringify({ inicio, t0Epoch: t0, acelerar }));
      fs.rmSync(path.join(OUT, "tmp_" + nombre), { recursive: true, force: true });
    }
  }
  console.log("escena lista:", nombre, "inicio", inicio.toFixed(2));
}

/** Tarjeta de texto a pantalla completa (título / cierre) con la paleta CUL, sin logo. */
async function tarjeta(p, { titulo, subtitulo, pie }) {
  await p.evaluate(([t, s, f, az, azo, na]) => {
    const d = document.createElement("div");
    d.style.cssText = `position:fixed;inset:0;z-index:2147483640;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:0 140px;
      background:linear-gradient(135deg,${azo} 0%,${az} 100%);color:#fff;font-family:Montserrat,"Segoe UI",system-ui,sans-serif`;
    d.innerHTML = `<div style="width:120px;height:8px;background:${na};border-radius:4px;margin-bottom:44px"></div>
      <div style="font-size:${t.length > 30 ? 68 : 96}px;font-weight:800;line-height:1.15;max-width:1500px">${t}</div>
      ${s ? `<div style="font-size:34px;font-weight:500;margin-top:40px;max-width:1400px;line-height:1.4;opacity:.92">${s}</div>` : ""}
      ${f ? `<div style="font-size:26px;margin-top:56px;color:${na};font-weight:600">${f}</div>` : ""}`;
    document.body.appendChild(d);
  }, [titulo, subtitulo || "", pie || "", AZUL, AZUL_OSCURO, NARANJA]);
}

module.exports = {
  BASE, API, CLAVE, OUT, CLIPS, AUTH, AZUL, NARANJA, AZUL_OSCURO, OVERLAY,
  dormir, esperar, caption, moverA, scrollSuave, recorrer, arriba, centrar, apuntar, clic, escribir,
  escena, tarjeta, navegador, cerrarNavegador, guardarSesion, centroDe,
};
