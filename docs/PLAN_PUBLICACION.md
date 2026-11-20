# Plan de publicación gratuita (2026)

**Objetivo:** publicar la plataforma sin pagar nada y conservar **todas** las funcionalidades actuales (generación desde video, tutor IA, clase en vivo por WebSocket, roles, reportes y PWA).

**Verificado:** 19 de noviembre de 2026. Los límites de planes gratuitos cambian sin aviso: confía siempre en los valores que muestre tu consola y vuelve a revisar este documento antes de desplegar.

## 1. Recomendación rápida

| Necesidad | Mejor opción gratuita | Por qué |
|---|---|---|
| **Demo ante jurado con YouTube funcionando** | Backend en **tu PC + Cloudflare Tunnel** (opción A del [Manual de despliegue](DESPLIEGUE.md)) | Tu IP es residencial: YouTube no bloquea subtítulos ni audio. Sin *cold start*. Sin costo. |
| **Publicación 24/7** | **Vercel Hobby** (frontend) + **Render Free** (backend Docker) + **Neon Free** (PostgreSQL) | Todo gratuito, HTTPS, WebSockets y BD persistente. Con las limitaciones de la sección 3. |
| **Si Render se duerme y eso rompe la demo** | **Oracle Cloud Always Free** (VM ARM con Docker) o mantener el túnel | Sin suspensión por inactividad; requiere más configuración. |
| **Si YouTube bloquea la nube** | Subir MP4 / pre-cargar subtítulos desde casa | Es el único arreglo **gratis** y fiable (ver sección 2). |

**No uses Render Postgres gratuito:** expira a los 30 días. Usa Neon o Supabase.

## 2. Bloqueos reales y cómo mitigarlos

### 2.1 YouTube desde IPs de nube (el bloqueo más importante)

`youtube-transcript-api` y `yt-dlp` funcionan en casa pero fallan en Render/Vercel/AWS con `IpBlocked`, `RequestBlocked` o *«Sign in to confirm you're not a bot»*. Es reputación de IP, no un error del código (`backend/app/services/transcripcion.py:104-126`, `:154-183`).

| Mitigación | ¿Gratis? | Fiabilidad | Cuándo usarla |
|---|---|---|---|
| Ejecutar el backend en casa + Cloudflare Tunnel | Sí | Alta | Demo y uso con videos de YouTube. **Recomendado.** |
| Pre-cargar subtítulos desde tu PC y reutilizar la caché por `video_id` | Sí | Alta | Cuando el despliegue es en nube pero los videos son conocidos. |
| Pestaña **«Subir archivo»** (MP4/MP3) | Sí | Alta | Plan B universal; no depende de YouTube. |
| Videos **con subtítulos** publicados | Sí | Media-alta | `obtener_transcripcion()` intenta subtítulos primero y solo baja audio si fallan. |
| `cookies.txt` de una cuenta secundaria | Sí | Media, temporal | Puede ayudar a `yt-dlp`; **la versión actual de `youtube-transcript-api` tiene la autenticación por cookies desactivada**, así que no arregla el primer paso. Nunca uses tu cuenta principal ni subas el archivo. |
| Cambiar `player_client` / `--js-runtimes node` | Sí | Baja | Parches que YouTube cambia seguido; el Dockerfile ya instala Node.js. |
| Proxy residencial rotativo | **No** | Alta | Último recurso; los proxies de centro de datos **no sirven** y los residenciales cuestan dinero. |

**Conclusión honesta:** no existe una solución 100 % gratuita y estable para descargar audio de YouTube desde un servidor en la nube. Para «igual de funcional» con YouTube, el backend debe correr detrás de una IP residencial o hay que subir el archivo.

**Vimeo:** siempre usa audio + Whisper (`transcripcion.py:276-279`) y no depende del bloqueo de YouTube, pero sí del límite de audio de Groq.

### 2.2 Cuotas de IA gratuitas

| Proveedor | Límite gratuito verificado (19-11-2026) | Impacto en la app |
|---|---|---|
| **Gemini** Flash (`gemini-3.8-flash`, `3.6`, `3.5`, `3`, `2.5`) | ~5 RPM / **20 peticiones por día** / 250k TPM | Muy bajo: se agota con 2-3 cuestionarios (generación + verificación + tutor). |
| **Gemini** Flash-Lite (`gemini-3.5-flash-lite`, `3.1-flash-lite`) | ~15 RPM / **500 RPD** / 250k TPM | Recomendado. Cambia `GEMINI_MODEL` a `gemini-3.5-flash-lite`. |
| **Groq LLM** (`openai/gpt-oss-120b`, `gpt-oss-20b`) | 30 RPM / 1.000 RPD / 8.000 TPM / 200.000 TPD | Buen respaldo; es el modelo por defecto en `.env.example`. |
| **Groq Whisper** (`whisper-large-v3-turbo`) | 20 RPM / 2.000 RPD / **7.200 s audio/hora, 28.800 s/día (8 h)** | Cada video sin subtítulos consume su duración en audio. Con 8 h/día basta para una demo, no para uso público intensivo. |

Notas importantes:

- Los límites de Gemini son **por proyecto**, no por clave: crear otra clave no suma cuota. El contador diario se reinicia a medianoche (hora del Pacífico). Google **ya no publica** los valores exactos en la web; aparecen en AI Studio → *Rate limits*.
- El valor `GEMINI_MODEL=gemini-flash-latest` de `.env.example` es un alias: **verifícalo en AI Studio y fija un nombre concreto**. Los modelos antiguos se están retirando (p. ej. `gemini-2.5-flash` deja de estar disponible el 1 de diciembre de 2026 y se redirige a Flash-Lite).
- El orquestador `services/ia/__init__.py:78-104` ya maneja 429 y 5xx con reintentos (2 s y 5 s) y cambia al siguiente proveedor. Por eso conviene dejar **`PROVEEDORES_IA=gemini,groq`** y una clave de cada. Ollama solo aporta si corres un modelo local.
- Si **todos** los proveedores fallan, la generación termina en error visible. El tutor devuelve 503; la verificación deja las preguntas «sin verificar» y el cuestionario sigue listo.
- Los planes gratuitos pueden usar los datos para mejorar los servicios: no subas videos con datos personales (advertencia ya incluida en `/privacidad`).

### 2.3 Limpieza de la nube gratuita

| Plataforma | Límite verificado | Consecuencia y mitigación |
|---|---|---|
| **Render Free** | 0,1 CPU / 512 MB; se duerme tras **15 min** sin tráfico HTTP **ni WebSocket**; arranque ~1 min; 750 h/mes; 5 GB ancho de banda; 500 min de build; sistema de archivos efímero; sin SSH/Shell; puede reiniciarse cuando quiera; una sola instancia | Despierta `/api/salud` antes de presentar. Un *ping* periódico evita el sueñopero consume horas. No guardes nada importante en `subidas/`. Ejecuta los scripts de semilla **desde tu PC** contra Neon. |
| **Neon Free** | 1 GB por proyecto (20 GB por cuenta), 100 CU-h/mes, 5 GB egreso, *scale to zero* tras 5 min (no se puede desactivar), reanudación en cientos de ms | Suficiente para la demo. Si se agotan CU-h o egreso, la BD se suspende hasta el mes siguiente; no pierde datos. |
| **Vercel Hobby** | 100 GB transferencia, 1 M invocaciones, 4 CPU-h, 300 s por función, 2 GB RAM, uso **no comercial** | El frontend es estático, no afecta. Proyecto académico = uso permitido. Para negocio haría falta Pro. |
| **Render Postgres Free** | **Expira a los 30 días**, 1 GB | No usar. Neon no expira. |

### 2.4 Restricciones de la propia aplicación

| Restricción | Por qué | Qué hacer |
|---|---|---|
| **Un solo worker / una sola instancia** | El estado de la clase en vivo vive en memoria (`services/vivo.py:1-9`) | El `Dockerfile` ya lanza un solo `uvicorn`. No añadas `--workers` ni escales. |
| `BackgroundTasks` en el mismo proceso | No hay cola externa | Si Render reinicia a mitad de generación, la tarea queda `error` al arrancar (limpieza en `main.py:38-57`). Reintenta. |
| Archivos subidos en disco local | `subidas/` es efímero en la nube | Aceptable para demo. Para persistencia haría falta almacenamiento de objetos (cambio de código). |
| CORS | `FRONTEND_URL` debe contener la URL de Vercel, sin barra final | Añade la URL y reinicia el backend. |
| Contenido mixto | Con `NEXT_PUBLIC_API_URL=http://…`, el navegador bloquea API y WebSocket | Usa **https** siempre en nube. |
| QR de clase en vivo | Si el docente abre `localhost`, el QR apunta a `localhost` | Define `NEXT_PUBLIC_URL_PUBLICA=https://TU-FRONTEND.vercel.app` antes de compilar. |
| PWA | Requiere contexto seguro | En Vercel (https) funciona; sobre `http://IP` en LAN no. |

## 3. Matriz «¿sigue funcionando igual?»

| Funcionalidad | En PC + túnel | En Render + Vercel + Neon |
|---|---|---|
| Generar desde YouTube | Sí (IP residencial) | Solo con subtítulos o subiendo archivo |
| Generar desde Vimeo | Sí | Sí, dentro de 8 h de audio/día en Groq |
| Generar desde archivo subido | Sí | Sí, mientras el archivo siga en disco (efímero) |
| Tutor IA y calificación de abiertas | Sí (con cuota) | Sí, con fallback Gemini → Groq |
| Clase en vivo WebSocket | Sí | Sí (Render admite WS), una sola instancia |
| Notificaciones, roles, RA, alertas, PDF | Sí | Sí |
| PWA / instalación | Solo con túnel https | Sí (https) |
| Datos persistentes | SQLite local | PostgreSQL de Neon |
| Arranque inmediato | Sí | ~1 min tras 15 min inactivo |

## 4. Paso a paso: Vercel + Render + Neon

1. **GitHub.** El repo `DevFajardo/plataforma-aprendizaje-ia` ya está en `main` con `gh` autenticado. Verifica que no haya secretos: `.env`, `*.db`, `subidas/` y `cookies_youtube.txt` están en `.gitignore`.
2. **Neon.** Crea proyecto gratuito → copia *Connection string* con `sslmode=require`. Formato aceptado: `postgresql+psycopg://usuario:clave@host/db?sslmode=require`.
3. **Render.** *New → Blueprint* → selecciona el repo (lee `render.yaml`). Variables: `DATABASE_URL` (Neon), `FRONTEND_URL` (URL de Vercel), `GEMINI_API_KEY`, `GROQ_API_KEY`, `PROVEEDORES_IA=gemini,groq`, `GEMINI_MODEL=gemini-3.5-flash-lite`, `IDIOMA_TRANSCRIPCION=es`, `SECRET_KEY` (la genera el Blueprint). Health check: `/api/salud`.
4. **Vercel.** *Add New → Project* → importa el repo → **Root Directory `frontend`** → variables `NEXT_PUBLIC_API_URL=https://TU-BACKEND.onrender.com` y `NEXT_PUBLIC_URL_PUBLICA=https://TU-FRONTEND.vercel.app`.
5. **CORS.** Actualiza `FRONTEND_URL` en Render con la URL de Vercel y reinicia.
6. **Datos demo.** Desde tu PC (con `DATABASE_URL` apuntando a Neon): `crear_demo.py`, `sembrar_estructura.py` y `sembrar_demo.py`. **Cambia las contraseñas `Demo12345` antes de abrir al público.**
7. **Verificación.** `GET /api/salud` debe listar los proveedores; prueba registro → generar (usa un video con subtítulos) → responder → publicar → unirse desde otro navegador → resultados/CSV → SUS → clase en vivo.

## 5. Checklist antes de publicar

- [ ] Claves de API **regeneradas** y nunca commits; `SECRET_KEY` larga y aleatoria.
- [ ] `GEMINI_MODEL` fijado a un modelo existente en AI Studio (revisa su RPD real).
- [ ] Claves de Gemini y Groq cargadas en Render; `PROVEEDORES_IA` con ambos.
- [ ] `FRONTEND_URL` con la URL exacta de Vercel; `NEXT_PUBLIC_API_URL` en **https**.
- [ ] `NEXT_PUBLIC_URL_PUBLICA` definida para el QR.
- [ ] Neon como BD (no Render Postgres); cadena con `sslmode=require`.
- [ ] Un solo worker/instancia en Render.
- [ ] Video MP4 de respaldo subido y/o cuestionario ya generado y publicado.
- [ ] Datos demo sembrados y contraseñas cambiadas.
- [ ] `pytest -q`, `npm run lint` y `npm run build` en verde.
- [ ] `/api/salud` responde y `/ws/vivo/{pin}` conecta desde el celular.
- [ ] Texto de `/privacidad` con el correo real del responsable (marcador `[correo del responsable]`).

## 6. Fuentes consultadas

- Render: <https://render.com/docs/free> y <https://render.com/pricing> (15 min de inactividad, 750 h, efímero, expiración de Postgres gratis).
- Neon: <https://neon.com/docs/introduction/plans> (1 GB, 100 CU-h, scale-to-zero).
- Vercel: <https://vercel.com/docs/plans/hobby> y <https://vercel.com/docs/functions/limitations>.
- Google: <https://ai.google.dev/gemini-api/docs/rate-limits> y <https://aistudio.google.com/docs/pricing>; valores de RPD leídos en AI Studio según seguimientos de noviembre de 2026.
- Groq: <https://console.groq.com/docs/rate-limits>.
- YouTube: README de `youtube-transcript-api` y guías de `yt-dlp` sobre bloqueo por IP de centros de datos.

> Este plan complementa —no sustituye— la [Guía de despliegue](DESPLIEGUE.md), que conserva los pasos concretos del túnel, la LAN y los scripts de semilla.
