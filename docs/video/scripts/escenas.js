// Definición de las escenas del video. Cada escena genera un clip en salida/clips/<nombre>.webm
const L = require("./lib");
const { BASE, CLAVE, esperar, caption, clic, apuntar, escribir, scrollSuave, recorrer, arriba, centrar, escena, tarjeta, moverA } = L;

const QUIZ = process.env.QUIZ_ID || "2"; // cuestionario sembrado «Bases de datos relacionales»
const CODIGO = process.env.CODIGO || "BUR4JW"; // código de acceso de ese cuestionario (se verifica en la escena)

const ESCENAS = {};

ESCENAS.titulo = () =>
  escena("00_titulo", async ({ page, listo }) => {
    await page.goto(BASE + "/login");
    await tarjeta(page, {
      titulo: "Aprendizaje Activo CUL — Plataforma web de aprendizaje activo con IA",
      subtitulo: "Proyecto de grado · Ingeniería de Sistemas y Computación · Corporación Universitaria Latinoamericana",
    });
    await esperar(page, 600);
    await listo();
    await esperar(page, 4000);
  });

ESCENAS.landing = () =>
  escena("01_landing", async ({ page, listo }) => {
    await page.goto(BASE + "/");
    await page.waitForLoadState("networkidle").catch(() => {});
    await esperar(page, 800);
    await caption(page, "Aprendizaje Activo CUL convierte cualquier video en una experiencia de estudio interactiva.");
    await listo();
    await esperar(page, 3500);
    await moverA(page, 900, 560);
    await caption(page, "Tres pasos: pegas el video, la IA genera el cuestionario y el estudiante aprende respondiendo.");
    await scrollSuave(page, 700, 1500);
    await esperar(page, 3000);
    await caption(page, "Incluye tutor con IA, clases en vivo y resultados de aprendizaje fáciles de entender.");
    await scrollSuave(page, 800, 1600);
    await esperar(page, 3000);
    await scrollSuave(page, 800, 1600);
    await esperar(page, 2500);
    await caption(page, "Pensada para estudiantes, docentes y coordinación académica.");
    await scrollSuave(page, 800, 1600);
    await esperar(page, 3000);
    await scrollSuave(page, 900, 1600);
    await esperar(page, 2000);
    await arriba(page, 2000);
  });

ESCENAS.login_docente = () =>
  escena("02_docente_panel", async ({ page, listo }) => {
    await page.goto(BASE + "/login");
    await page.waitForLoadState("networkidle").catch(() => {});
    await caption(page, "El docente inicia sesión con su cuenta institucional.");
    await esperar(page, 600);
    await listo();
    await esperar(page, 1500);
    await escribir(page, page.locator('input[type="email"]'), "docente@demo.com");
    await escribir(page, page.locator('input[type="password"]'), CLAVE);
    await clic(page, page.locator('button[type="submit"]'));
    await page.waitForURL((u) => u.pathname === "/panel", { timeout: 30000 });
    await page.waitForLoadState("networkidle").catch(() => {});
    await esperar(page, 800);
    await caption(page, "Su panel resume cuestionarios publicados, resultados y temas que el curso debe reforzar.");
    await esperar(page, 3500);
    await recorrer(page, { paso: 480, pausa: 2200, max: 3 });
    await caption(page, "Incluso estima cuánto tiempo ahorra frente a preparar todo a mano.");
    await esperar(page, 2500);
    await arriba(page, 1200);
  });

ESCENAS.generar = () =>
  escena(
    "03_generar",
    async ({ page, listo }) => {
      await page.goto(BASE + "/panel");
      await page.waitForLoadState("networkidle").catch(() => {});
      const yt = await page.evaluate(async (id) => {
        const t = localStorage.getItem("token") || Object.values(localStorage).find((v) => typeof v === "string" && v.split(".").length === 3);
        const r = await fetch((window.__API || "http://localhost:8000") + "/api/cuestionarios/" + id, { headers: { Authorization: "Bearer " + t } });
        return (await r.json()).youtube_id;
      }, QUIZ);
      await caption(page, "Para crear un cuestionario, el docente entra a «Generar».");
      await listo();
      await esperar(page, 1800);
      await clic(page, page.getByRole("link", { name: "Generar", exact: true }).first());
      await page.waitForURL((u) => u.pathname === "/");
      await page.waitForLoadState("networkidle").catch(() => {});
      await esperar(page, 1500);
      await caption(page, "Solo pega el enlace de un video de YouTube o Vimeo, o sube un archivo.");
      await escribir(page, page.locator('input[type="url"], input[placeholder*="youtube"]').first(), "https://www.youtube.com/watch?v=" + yt, { delay: 55 });
      await esperar(page, 1500);
      await caption(page, "Elige cuántas preguntas quieres y pulsa «Generar»: la IA transcribe el video y redacta el cuestionario.");
      const sel = page.locator("select").first();
      if (await sel.count()) {
        await apuntar(page, sel);
        await esperar(page, 600);
        await sel.selectOption({ index: 1 }).catch(() => {});
      }
      await esperar(page, 1200);
      await apuntar(page, page.getByRole("button", { name: "Generar", exact: true }));
      await esperar(page, 3000);
    },
    { rol: "docente" },
  );

ESCENAS.quiz = () =>
  escena(
    "04_quiz_docente",
    async ({ page, listo }) => {
      await page.goto(BASE + "/cuestionarios/" + QUIZ);
      await page.waitForLoadState("networkidle").catch(() => {});
      const panel = page.locator('section[aria-label="Calidad de las preguntas"]');
      await panel.waitFor({ timeout: 30000 });
      await esperar(page, 800);
      await caption(page, "Así queda el cuestionario ya generado: el video, su resumen y las ideas clave.");
      await listo();
      await esperar(page, 2500);
      await scrollSuave(page, 520, 1500);
      await esperar(page, 3500);
      await caption(page, "En segundos la IA genera el resumen, las ideas clave y las preguntas.");
      await recorrer(page, { paso: 220, pausa: 900, max: 2 });
      await esperar(page, 2500);

      await centrar(page, panel.locator("h2, h3").first(), 250);
      await caption(page, "El panel «Calidad de las preguntas» contrasta cada pregunta con la transcripción del video.");
      await esperar(page, 3500);
      const insignia = panel.getByText("Verificada en el video").first();
      await apuntar(page, insignia, { offset: 100 });
      await caption(page, "La insignia «Verificada en el video» indica que la respuesta está respaldada por lo que se dice en el video.");
      await esperar(page, 4000);

      await caption(page, "La clave de respuestas resalta en verde la opción correcta, con su explicación.");
      const item = panel.locator("ul > li").first();
      await apuntar(page, item, { offset: 0 });
      await esperar(page, 3500);
      await scrollSuave(page, 420, 1400);
      await esperar(page, 3000);
      await scrollSuave(page, -420, 1400);
      await esperar(page, 800);

      await caption(page, "Si algo no convence, el docente corrige la respuesta con «Editar respuesta», sin salir de la página.");
      const btn = item.getByRole("button", { name: /respuesta$/ });
      await clic(page, btn, { despues: 1200 });
      await esperar(page, 3500);
      const cancelar = item.getByRole("button", { name: /Cancelar/ });
      if (await cancelar.count()) await clic(page, cancelar, { despues: 1200 });
      await esperar(page, 1500);

      await caption(page, "Las mejores preguntas se guardan en el banco institucional para reutilizarlas.");
      await clic(page, item.getByRole("button", { name: /Guardar en el banco/ }), { despues: 1800 });
      const gb = item.getByRole("button", { name: /^Guardar$/ });
      if (await gb.count()) await clic(page, gb, { despues: 1500 });
      await esperar(page, 3000);

      // Editor: nivel de Bloom y resultado de aprendizaje
      await arriba(page, 1800);
      await caption(page, "Cada pregunta tiene su resultado de aprendizaje y su nivel de Bloom, que se ajustan desde «Editar».");
      await clic(page, page.getByRole("button", { name: /^Editar$/ }).or(page.getByRole("link", { name: /^Editar$/ })), { despues: 2500 });
      await page.waitForLoadState("networkidle").catch(() => {});
      const bloom = page.getByLabel("Nivel de Bloom").first();
      if (await bloom.count()) {
        await centrar(page, bloom);
        await apuntar(page, bloom, { scroll: false });
        await esperar(page, 3500);
      }
      await esperar(page, 1000);
    },
    { rol: "docente" },
  );

ESCENAS.tutor = () =>
  escena(
    "05_tutor",
    async ({ page, listo, t, acelerar }) => {
      await page.goto(BASE + "/cuestionarios/" + QUIZ);
      await page.waitForLoadState("networkidle").catch(() => {});
      await esperar(page, 800);
      const pestanas = page.getByRole("tab");
      // Limpia conversaciones previas (esta parte se recorta del clip)
      await pestanas.nth(1).click();
      await esperar(page, 1200);
      const nueva = page.getByRole("button", { name: /Nueva conversaci/ });
      if (await nueva.count()) await nueva.click();
      await esperar(page, 800);
      await pestanas.nth(0).click();
      await scrollSuave(page, 420, 1200);
      await caption(page, "«Pregúntale al video»: un tutor con IA que responde solo con lo que dice el video.");
      await listo();
      await esperar(page, 2000);
      await clic(page, pestanas.nth(1), { despues: 1500 });
      const caja = page.getByPlaceholder(/Escribe tu pregunta sobre el video/);
      await caja.waitFor({ timeout: 20000 });
      await escribir(page, caja, "¿Qué es una clave primaria?", { delay: 60 });
      await esperar(page, 1000);
      await caption(page, "El tutor busca en la transcripción del video y arma la respuesta.");
      await clic(page, page.getByRole("button", { name: /Preguntar/ }), { despues: 800 });
      const espera0 = t();
      const cita = page.getByRole("button", { name: /Ir al minuto/ }).first();
      await cita.waitFor({ timeout: 180000 });
      // La IA externa puede tardar: ese tramo de espera se acelera en el montaje
      if (t() - espera0 > 8) acelerar.push([espera0 + 4, t() - 1.5]);
      await esperar(page, 1200);
      await caption(page, "La respuesta incluye la cita con el minuto exacto del video donde se explica.");
      await apuntar(page, cita, { offset: -40 });
      await esperar(page, 5000);
    },
    { rol: "docente" },
  );

ESCENAS.publicar = () =>
  escena(
    "06_publicar",
    async ({ page, listo }) => {
      await page.goto(BASE + "/cuestionarios/" + QUIZ);
      await page.waitForLoadState("networkidle").catch(() => {});
      await esperar(page, 800);
      await caption(page, "Al publicar el cuestionario, la plataforma genera un código para compartir con los estudiantes.");
      await listo();
      await esperar(page, 3000);
      const cod = page.getByText("Código para unirse").first();
      await apuntar(page, cod, { offset: 40 });
      await esperar(page, 3000);
      await caption(page, "También se puede copiar el enlace directo, o asignarlo a un grupo para que aparezca en «Mis cursos».");
      await clic(page, page.getByRole("button", { name: /Copiar enlace/ }), { despues: 1500 });
      await esperar(page, 3500);
    },
    { rol: "docente" },
  );

ESCENAS.estudiante = () =>
  escena("07_estudiante", async ({ page, listo, t, acelerar }) => {
    let tRapido = null;
    await page.goto(BASE + "/login");
    await page.waitForLoadState("networkidle").catch(() => {});
    await caption(page, "Ahora el estudiante: cierra la sesión del docente e ingresa con su propia cuenta.");
    await listo();
    await esperar(page, 2500);
    await escribir(page, page.locator('input[type="email"]'), "estudiante@demo.com");
    await escribir(page, page.locator('input[type="password"]'), CLAVE);
    await clic(page, page.locator('button[type="submit"]'));
    await page.waitForURL((u) => u.pathname === "/panel", { timeout: 30000 });
    await page.waitForLoadState("networkidle").catch(() => {});
    await esperar(page, 800);
    await caption(page, "El estudiante ve su propio panel: su progreso y los temas que debe reforzar.");
    await esperar(page, 3500);
    await caption(page, "Para entrar a un cuestionario usa «Unirse» con el código que le dio el docente.");
    await clic(page, page.getByRole("link", { name: "Unirse", exact: true }).first(), { despues: 1500 });
    await page.waitForURL(/unirse/);
    await esperar(page, 1200);
    await escribir(page, page.getByPlaceholder("ABC123"), CODIGO, { delay: 140 });
    await esperar(page, 800);
    await clic(page, page.getByRole("button", { name: "Unirme" }), { despues: 800 });
    await page.waitForURL(/cuestionarios\/\d+/, { timeout: 30000 });
    await page.waitForLoadState("networkidle").catch(() => {});
    await esperar(page, 1500);
    await caption(page, "Puede repasar el resumen y las ideas clave antes de empezar.");
    await esperar(page, 2500);
    await clic(page, page.getByRole("button", { name: /Empezar cuestionario/ }), { despues: 1500 });
    const tarjetas = page.locator("article");
    const n = await tarjetas.count();
    await caption(page, "Cada respuesta recibe retroalimentación inmediata, con el minuto del video donde se explica el tema.");
    for (let i = 0; i < n; i++) {
      const a = tarjetas.nth(i);
      await centrar(page, a, 60);
      const lento = i < 4;
      if (await a.locator("textarea").count()) {
        await escribir(page, a.locator("textarea"), "La integridad referencial evita registros huérfanos, porque obliga a que toda clave foránea apunte a una fila existente.", { delay: lento ? 45 : 15 });
        await clic(page, a.getByRole("button", { name: /Enviar/ }), { despues: 1500 });
        const w0 = t();
        await a.locator('[role="status"]').first().waitFor({ timeout: 170000 }).catch(() => {});
        if (t() - w0 > 8) acelerar.push([w0 + 3, t() - 1.5, 8]);
        await esperar(page, 2000);
      } else {
        const ops = a.locator('div[role="group"] button');
        const idx = i === 1 ? 1 : 0;
        if (lento) await clic(page, ops.nth(idx), { despues: 800 });
        else { const [x, y] = await L.centroDe(ops.nth(idx)); await moverA(page, x, y); await page.mouse.click(x, y); await esperar(page, 500); }
      }
      if (lento) {
        await a.locator('[role="status"]').first().waitFor({ timeout: 20000 }).catch(() => {});
        await centrar(page, a.locator('[role="status"]').first(), 120).catch(() => {});
        await esperar(page, i === 0 ? 4500 : 3000);
      }
      if (i === 3) {
        await caption(page, "Responde el resto del cuestionario a su ritmo…");
        tRapido = t();
      }
    }
    if (tRapido !== null) acelerar.push([tRapido + 1, t() - 1, 2.5]);
    const fin = page.getByRole("button", { name: /Finalizar y ver puntaje/ });
    await clic(page, fin, { despues: 1500 });
    await page.locator("text=/Puntaje:/").first().waitFor({ timeout: 30000 });
    await caption(page, "Al finalizar ve su puntaje y puede intentarlo de nuevo cuando quiera.");
    await centrar(page, page.locator("text=/Puntaje:/").first(), 0);
    await esperar(page, 5000);
  }, { });

ESCENAS.resultados = () =>
  escena(
    "08_resultados",
    async ({ page, listo }) => {
      await page.goto(BASE + "/cuestionarios/" + QUIZ);
      await page.waitForLoadState("networkidle").catch(() => {});
      await caption(page, "De vuelta con el docente: abre los resultados del cuestionario.");
      await listo();
      await esperar(page, 2000);
      await clic(page, page.getByRole("link", { name: /Ver resultados y sesiones en vivo/ }).or(page.getByRole("button", { name: /Ver resultados y sesiones en vivo/ })).first(), { despues: 1500 });
      await page.waitForURL(/resultados/);
      await page.waitForLoadState("networkidle").catch(() => {});
      await esperar(page, 1500);
      await caption(page, "Los resultados llegan al instante: intentos, estudiantes y promedio del grupo.");
      await esperar(page, 3000);
      await caption(page, "«Temas a reforzar» señala las preguntas donde el grupo más falló.");
      await scrollSuave(page, 330, 1400);
      await esperar(page, 4000);
      await caption(page, "El análisis de ítems indica la dificultad de cada pregunta y qué distractores no funcionan.");
      await centrar(page, page.getByRole("heading", { name: /Análisis de ítems/ }), 380);
      await esperar(page, 3500);
      await scrollSuave(page, 450, 1500);
      await esperar(page, 3500);
      await centrar(page, page.getByRole("heading", { name: /Acierto por pregunta/ }), 300);
      await caption(page, "Y el acierto por pregunta deja ver de un vistazo qué hay que reforzar en clase.");
      await esperar(page, 4000);
      await arriba(page, 1800);
      await caption(page, "La pestaña «Por estudiante» muestra cómo le fue a cada persona.");
      await clic(page, page.getByRole("tab", { name: /Por estudiante/ }), { despues: 2000 });
      await esperar(page, 2500);
      await caption(page, "El docente puede abrir las respuestas de un estudiante y ver cada pregunta con su resultado.");
      await clic(page, page.getByRole("button", { name: /Ver respuestas/ }).first(), { despues: 2000 });
      await esperar(page, 3000);
      await scrollSuave(page, 450, 1500);
      await esperar(page, 3500);
    },
    { rol: "docente" },
  );

ESCENAS.vivo = async () => {
  const L2 = L;
  const fs = require("fs");
  const path = require("path");
  const browser = await L.navegador();
  const nombre = (n) => path.join(L.CLIPS, n);
  const mk = async (n, vp, extra, rol) => {
    const dir = path.join(L.OUT, "tmp_" + n);
    const ctx = await browser.newContext({
      viewport: vp, recordVideo: { dir, size: vp }, locale: "es-CO", deviceScaleFactor: 1, ...extra,
      ...(rol ? { storageState: fs.existsSync(path.join(L.AUTH, rol + ".json")) ? path.join(L.AUTH, rol + ".json") : await L.guardarSesion(browser, rol) } : {}),
    });
    await ctx.addInitScript(L.OVERLAY);
    const t0 = Date.now();
    const page = await ctx.newPage();
    return { ctx, page, t0, dir, n };
  };
  const cierre = async (s, inicio) => {
    const v = s.page.video();
    await s.ctx.close();
    fs.copyFileSync(await v.path(), nombre(s.n + ".webm"));
    fs.writeFileSync(nombre(s.n + ".json"), JSON.stringify({ inicio, t0Epoch: s.t0, acelerar: [] }));
    fs.rmSync(s.dir, { recursive: true, force: true });
  };
  const docente = await mk("09_vivo_docente", { width: 1920, height: 1080 }, {}, "docente");
  const movil = await mk("09_vivo_movil", { width: 390, height: 844 }, { isMobile: true, hasTouch: true });
  // participantes de fondo (sin grabar)
  const extras = [];
  const P = docente.page, M = movil.page;
  const B = 140; // los subtítulos suben para no tapar los botones del presentador
  await P.goto(BASE + "/cuestionarios/" + QUIZ);
  await P.waitForLoadState("networkidle").catch(() => {});
  await M.goto(BASE + "/vivo");
  await caption(P, "Clase en vivo: el docente inicia una sesión desde su cuestionario.");
  await esperar(P, 800);
  const iniD = (Date.now() - docente.t0) / 1000 + 0.35;
  const iniM = (Date.now() - movil.t0) / 1000 + 0.35;
  await esperar(P, 2500);
  await clic(P, P.getByRole("button", { name: /Iniciar clase en vivo/ }), { despues: 1500 });
  await P.waitForURL(/vivo\/presentar/);
  await P.getByText("participantes").first().waitFor();
  await caption(P, "Se proyecta el PIN y un código QR: los estudiantes entran desde su celular, sin crear cuenta.", B);
  await esperar(P, 2500);
  const pin = (await P.evaluate(() => document.body.innerText.match(/\b\d{6}\b/)?.[0]));
  for (const nick of ["Valentina", "Santiago"]) {
    const c = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const p = await c.newPage();
    await p.goto(BASE + "/vivo");
    await p.getByPlaceholder("123456").fill(pin);
    await p.getByPlaceholder(/Tigre/).fill(nick);
    await p.getByRole("button", { name: "Unirme" }).click();
    extras.push([c, p]);
  }
  await esperar(M, 1000);
  await escribir(M, M.getByPlaceholder("123456"), pin, { delay: 120 });
  await escribir(M, M.getByPlaceholder(/Tigre/), "Camila", { delay: 120 });
  await clic(M, M.getByRole("button", { name: "Unirme" }), { despues: 1500 });
  await esperar(P, 2500);
  await caption(P, "Los participantes aparecen en la pantalla del docente a medida que se unen.", B);
  await esperar(P, 3000);
  await clic(P, P.getByRole("button", { name: /Iniciar \(/ }), { despues: 1500 });
  const rondas = 3;
  for (let q = 0; q < rondas; q++) {
    await caption(P, q === 0 ? "Cada pregunta tiene cuenta regresiva y los estudiantes responden desde el celular." : q === 1 ? "Los puntos dependen de acertar y de la rapidez al responder." : "El ranking se actualiza con cada pregunta.", B);
    const opM = M.getByRole("button", { name: /^Opción/ });
    await opM.first().waitFor({ timeout: 30000 });
    // los demás responden de fondo
    for (const [, p] of extras) {
      const o = p.getByRole("button", { name: /^Opción/ });
      await o.first().waitFor({ timeout: 30000 });
      setTimeout(() => o.nth(Math.floor(Math.random() * 3)).click().catch(() => {}), 800 + Math.random() * 2500);
    }
    await esperar(M, 2500);
    await opM.nth(q === 1 ? 1 : 0).tap();
    await esperar(M, 1200);
    await P.getByRole("button", { name: /Siguiente pregunta|Ver podio|Finalizar|Terminar/ }).first().waitFor({ timeout: 45000 });
    if (q === 0) await caption(P, "Al responder todos, aparece cuántos eligieron cada opción y cuál era la correcta.", B);
    await esperar(P, 5500);
    if (q < rondas - 1) await clic(P, P.getByRole("button", { name: /Siguiente pregunta/ }), { despues: 1200 });
  }
  await caption(P, "Al terminar, el podio reconoce a los mejores puntajes.", B);
  const sig = P.getByRole("button", { name: /Siguiente pregunta/ });
  // Termina la clase para mostrar el podio
  await clic(P, P.getByRole("button", { name: /Finalizar clase/ }), { despues: 1500 });
  const conf = P.getByRole("button", { name: /^(Finalizar|Sí|Confirmar|Aceptar)/ });
  if (await conf.count()) await clic(P, conf.first(), { despues: 1500 }).catch(() => {});
  await esperar(P, 7000);
  await esperar(M, 500);
  for (const [c] of extras) await c.close();
  await cierre(docente, iniD);
  await cierre(movil, iniM);
  console.log("escena lista: 09_vivo (docente + movil)");
};

ESCENAS.coordinador = () =>
  escena(
    "10_coordinador",
    async ({ page, listo }) => {
      await page.goto(BASE + "/panel");
      await page.waitForLoadState("networkidle").catch(() => {});
      await caption(page, "Por último, la coordinación académica: ingresa con el rol de coordinador.");
      await listo();
      await esperar(page, 2500);
      await clic(page, page.getByRole("link", { name: "Coordinación", exact: true }).first(), { despues: 1500 });
      await page.waitForURL(/coordinacion/);
      await page.waitForLoadState("networkidle").catch(() => {});
      await esperar(page, 2500);
      await caption(page, "El semáforo muestra el logro por resultado de aprendizaje: verde, amarillo o rojo.");
      await esperar(page, 3500);
      await scrollSuave(page, 420, 1500);
      await esperar(page, 3500);
      await recorrer(page, { paso: 460, pausa: 2200, max: 2 });
      await caption(page, "También se ve la distribución por nivel de Bloom, el desempeño por asignatura y la tendencia semanal.");
      await esperar(page, 3500);
      const alertas = page.getByRole("heading", { name: /Alertas/ }).first();
      if (await alertas.count()) {
        await centrar(page, alertas, 250);
        await caption(page, "Las alertas tempranas identifican estudiantes en riesgo e indican el motivo.");
        await esperar(page, 5000);
        await scrollSuave(page, 350, 1500);
        await esperar(page, 3000);
      }
      await arriba(page, 1800);
      await caption(page, "Y con un clic se descarga el informe en PDF para acreditación o seguimiento.");
      const pdf = page.getByRole("button", { name: /Descargar PDF/ }).or(page.getByRole("link", { name: /Descargar PDF/ })).first();
      await apuntar(page, pdf);
      await esperar(page, 800);
      const [dl] = await Promise.all([page.waitForEvent("download", { timeout: 30000 }).catch(() => null), clic(page, pdf, { despues: 500 })]);
      await esperar(page, 1500);
      await caption(page, dl ? "El informe se descargó como PDF: " + dl.suggestedFilename() : "El informe PDF se descarga al instante.");
      await esperar(page, 4500);
    },
    { rol: "coordinador" },
  );

ESCENAS.movil = () =>
  escena(
    "11_movil",
    async ({ page, listo }) => {
      await page.goto(BASE + "/panel");
      await page.waitForLoadState("networkidle").catch(() => {});
      await esperar(page, 600);
      await caption(page, "La plataforma es responsive: también funciona en el celular.");
      await listo();
      await esperar(page, 2500);
      await scrollSuave(page, 500, 1400);
      await esperar(page, 2000);
      await scrollSuave(page, 500, 1400);
      await esperar(page, 2500);
    },
    { rol: "estudiante", movil: true },
  );

ESCENAS.cierre = () =>
  escena("12_cierre", async ({ page, listo }) => {
    await page.goto(BASE + "/login");
    await tarjeta(page, {
      titulo: "Gracias",
      subtitulo: "Aprendizaje Activo CUL · Proyecto de grado · Ingeniería de Sistemas y Computación · Corporación Universitaria Latinoamericana",
    });
    await esperar(page, 600);
    await listo();
    await esperar(page, 4000);
  });

module.exports = { ESCENAS, QUIZ, CODIGO };
