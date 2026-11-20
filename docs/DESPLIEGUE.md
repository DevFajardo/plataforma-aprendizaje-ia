# Guía de despliegue

Hay dos caminos. Para la **presentación** se recomienda la **opción A (demo local)**: no depende de servicios externos, YouTube no bloquea tu conexión de casa y tienes control total.

> Para publicar de forma permanente con planes gratuitos, consulta el [Plan de publicación](PLAN_PUBLICACION.md): límites vigentes de Vercel/Render/Neon, bloqueos de YouTube y cuotas de IA con sus mitigaciones. Para mantener el sistema después, [Operación y soporte](OPERACION.md).

## Opción A: demo local (recomendada para la presentación)

### 1. Preparar el backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\crear_demo.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

`crear_demo.py` crea `docente@demo.com` y `estudiante@demo.com` (contraseña `Demo12345`) si no existen. Es seguro ejecutarlo varias veces.

Para cargar la estructura académica de ejemplo (facultad, programa, asignaturas, resultados de aprendizaje, `coordinador@demo.com`, `admin@demo.com` y un grupo demo) ejecuta también `scripts\sembrar_estructura.py` (idempotente; en Render: `python scripts/sembrar_estructura.py`).

### 2. Preparar el frontend

Para la demo es mejor la versión de producción (más rápida):

```powershell
cd frontend
npm run build
npm run start
```

Abre <http://localhost:3000>. En desarrollo basta `npm run dev`.

### 3. Enlace público temporal con Cloudflare Tunnel (gratis)

Sirve para que otras personas (jurado, compañeros) entren desde sus teléfonos mientras tu computador está encendido.

1. Instala `cloudflared` (<https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/>), por ejemplo `winget install Cloudflare.cloudflared`.
2. Expón el **backend** y copia la URL `https://….trycloudflare.com` que aparece:

   ```powershell
   cloudflared tunnel --url http://localhost:8000
   ```

3. Detén el frontend, y reinícialo apuntando a esa URL (la variable se incrusta al compilar):

   ```powershell
   cd frontend
   $env:NEXT_PUBLIC_API_URL = "https://URL-DEL-BACKEND.trycloudflare.com"
   npm run build
   npm run start
   ```

4. En otra terminal expón el **frontend**:

   ```powershell
   cloudflared tunnel --url http://localhost:3000
   ```

   Comparte la URL `https://….trycloudflare.com` que muestre. Es la dirección que abrirá el público.

5. Permite ese origen en el backend: en `backend/.env` pon `FRONTEND_URL=http://localhost:3000,https://URL-DEL-FRONTEND.trycloudflare.com` y reinicia uvicorn.

Las URL cambian cada vez que reinicias `cloudflared`; por eso es un enlace *temporal*. Si solo vas a presentar desde tu computador, no necesitas el túnel.

## Opción A2: demo en red local (LAN) con `iniciar_demo.ps1`

Para que el jurado o los compañeros entren **desde sus celulares en el mismo Wi-Fi** (sin internet público ni túneles), usa el script de la raíz del repositorio:

```powershell
.\iniciar_demo.ps1          # build + start (más rápido para presentar)
.\iniciar_demo.ps1 -Dev     # next dev (sin compilar)
.\iniciar_demo.ps1 -Ip 192.168.1.50   # si la detección automática elige otra tarjeta de red
```

El script: (1) detecta la IPv4 del adaptador Wi-Fi/Ethernet activo (el que tiene puerta de enlace), (2) arranca el backend en `0.0.0.0:8000` con `FRONTEND_URL=http://localhost:3000,http://127.0.0.1:3000,http://IP:3000`, (3) arranca el frontend en `0.0.0.0:3000` con `NEXT_PUBLIC_API_URL=http://IP:8000` y `NEXT_PUBLIC_URL_PUBLICA=http://IP:3000`, y (4) imprime las URLs. Los puertos 3000 y 8000 deben estar libres (detén antes tus servidores de desarrollo).

**Firewall de Windows (una sola vez, PowerShell como administrador).** Sin esta regla, los otros dispositivos no podrán conectarse. El script **no** la crea por ti:

```powershell
New-NetFirewallRule -DisplayName "Aprendizaje Activo (demo LAN)" -Direction Inbound -Protocol TCP -LocalPort 3000,8000 -Action Allow -Profile Private
# Para quitarla al terminar:
Remove-NetFirewallRule -DisplayName "Aprendizaje Activo (demo LAN)"
```

**QR de la clase en vivo.** El QR y los enlaces para compartir usan el origen con el que se abrió la página. Si el docente abre `http://localhost:3000`, el QR apuntaría a `localhost` (inútil en los celulares). Por eso el script define `NEXT_PUBLIC_URL_PUBLICA`; si ejecutas el frontend a mano, defínela antes de compilar/iniciar (por ejemplo `$env:NEXT_PUBLIC_URL_PUBLICA="http://192.168.1.50:3000"`). También sirve para poner la URL pública de un despliegue o de un túnel. Si el docente abre la página directamente por la IP, no hace falta.

**Instalar como app (PWA).** El botón «Instalar app» de Chrome/Edge exige un contexto seguro: funciona en `localhost` y en `https://`, pero **no** sobre `http://IP` en la red local (el navegador no ofrece la instalación ni registra el service worker). En LAN la plataforma funciona igual como página web; para la instalación usa el despliegue en la nube (https) o un túnel.

## Opción B: nube gratuita

| Pieza | Servicio | Notas |
|---|---|---|
| Todo en un clic | **Render Blueprint** (`render.yaml`) | Frontend + backend + PostgreSQL gratis; la BD expira a 30 días. Ver [Plan de publicación](PLAN_PUBLICACION.md). |
| Frontend | **Vercel** | Plan *Hobby* gratuito. Alternativa al frontend del Blueprint. |
| Backend | **Render** (con el `Dockerfile`) o **Hugging Face Spaces** (Docker) | Plan gratuito con limitaciones (abajo). |
| Base de datos | **Neon** o **Supabase** (PostgreSQL) | Para BD permanente; el disco del backend gratuito es efímero: SQLite se perdería. |

### 1. Base de datos en Neon (PostgreSQL)

1. Crea un proyecto en [Neon](https://neon.tech) (plan gratuito) y copia la cadena de conexión (*Connection string*, con `sslmode=require`).
2. El backend acepta `postgres://…` y `postgresql://…` y los convierte al driver `psycopg` 3 (`postgresql+psycopg://usuario:clave@host/basededatos?sslmode=require`). Las tablas se crean solas al arrancar (`create_all`) y las columnas nuevas se migran con `ALTER TABLE` si faltan.
3. Guarda esa cadena: será `DATABASE_URL` en Render y en los scripts de semilla.

### 2. Backend en Render (Docker, plan gratuito)

El repositorio incluye `render.yaml` (Blueprint) con el servicio web Docker del backend, el frontend Next.js, una PostgreSQL gratuita, el *health check* `/api/salud` y la lista de variables. Para desplegar solo el backend con Neon, crea el servicio manualmente como se describe abajo.

1. Sube el proyecto a GitHub (el `.env` y los `*.db` están en `.gitignore`).
2. En Render: **New → Blueprint** → elige el repositorio (lee `render.yaml`), o **New → Web Service** → **Root Directory** `backend` → **Runtime: Docker**. Render define `$PORT`.
3. Variables de entorno: `DATABASE_URL` (Neon), `FRONTEND_URL` (la URL de Vercel; se puede dejar `http://localhost:3000` al principio y actualizarla), `GEMINI_API_KEY`, `GROQ_API_KEY`, `PROVEEDORES_IA=gemini,groq`, `SECRET_KEY` e `IDIOMA_TRANSCRIPCION=es`. Si aplicas el Blueprint completo, solo se piden las claves de IA; `DATABASE_URL`, `FRONTEND_URL` y las URLs públicas se resuelven entre servicios.
4. **Un solo worker y una sola instancia.** La clase en vivo guarda su estado (sesiones, conexiones WebSocket) en la memoria del proceso. El `Dockerfile` lanza `uvicorn` con un único proceso; no uses `--workers N` ni escales a varias instancias.
5. **WebSockets.** Render los admite sobre el mismo servicio: el navegador usa `wss://TU-BACKEND.onrender.com/…` automáticamente porque la API es `https://`. No hay configuración adicional.
6. Despliega y comprueba `https://TU-BACKEND.onrender.com/api/salud`.

**Hugging Face Spaces** (alternativa): Space de tipo *Docker*, sube el contenido de `backend/`, `PORT=7860` y `app_port: 7860`; las variables van como *Secrets*.

### 3. Frontend en Vercel

1. **Add New → Project** → importa el repositorio → **Root Directory** `frontend` (Next.js, sin configuración extra).
2. Variable de entorno: `NEXT_PUBLIC_API_URL=https://TU-BACKEND.onrender.com` (**https**; con `http` el navegador bloquearía las peticiones y los WebSockets por contenido mixto). Opcional: `NEXT_PUBLIC_URL_PUBLICA=https://TU-FRONTEND.vercel.app` para fijar el origen del QR.
3. Despliega. Después añade la URL de Vercel a `FRONTEND_URL` del backend (CORS; varias separadas por comas, sin barra final) y reinicia el servicio. Si cambias `NEXT_PUBLIC_API_URL`, hay que volver a desplegar (se incrusta al compilar).
4. Con https, el navegador ofrece **Instalar app** (PWA) y registra el service worker.

### 4. Datos de ejemplo en producción

Los scripts leen `DATABASE_URL`, así que se pueden ejecutar contra Neon desde tu computador o desde la *Shell* de Render (servicio → **Shell**):

```powershell
# Desde tu equipo (PowerShell), apuntando a Neon
cd backend
$env:DATABASE_URL = "postgresql+psycopg://usuario:clave@host/db?sslmode=require"
.\.venv\Scripts\python.exe scripts\crear_demo.py            # docente y estudiante demo
.\.venv\Scripts\python.exe scripts\sembrar_estructura.py    # facultad, programa, RA, coordinador y admin
.\.venv\Scripts\python.exe scripts\sembrar_demo.py          # 24 estudiantes, 5 cuestionarios, intentos, alertas...
# En la Shell de Render:  python scripts/sembrar_demo.py
```

`sembrar_demo.py --reset-demo` borra solo lo que sembró. Cambia las contraseñas demo antes de abrir el sitio al público.

### Compatibilidad con PostgreSQL: qué se verificó (y qué no)

- **Verificado:** el código y los modelos no usan nada exclusivo de SQLite: solo tipos genéricos de SQLAlchemy (`Integer`, `String`, `Text`, `Boolean`, `Float`, `DateTime(timezone=True)`), sin SQL crudo específico. Hay una prueba (`test_modelos_compilan_para_postgresql`) que genera el DDL de **todas** las tablas con el dialecto de PostgreSQL. Las migraciones usan `ALTER TABLE … ADD COLUMN` con valores por defecto estándar (`BOOLEAN DEFAULT FALSE`, `TEXT DEFAULT '[]'`). Las 300+ pruebas pasan con SQLite.
- **No verificado:** no se ejecutó la aplicación contra un servidor PostgreSQL real porque en el equipo de desarrollo no había Docker ni PostgreSQL instalados. Antes de la presentación en la nube conviene hacer una pasada completa (registro → generar → responder → clase en vivo → coordinación) y revisar los registros de Render.

### Limitaciones de la nube gratuita (léelas antes de elegir)

- **Render gratuito se duerme tras 15 minutos** sin tráfico: la primera petición tarda ~30–60 s en responder. Despierta el servicio con unos minutos de antelación visitando `/api/salud`.
- **YouTube suele bloquear las descargas de audio desde servidores en la nube** (IPs de centros de datos). En ese caso falla el respaldo con Whisper para videos sin subtítulos. Recomendación: usar videos **con subtítulos** o la **subida de archivos**, que no depende de YouTube.
- El disco es efímero: los archivos subidos (`subidas/`) desaparecen al reiniciar. Para la demo es suficiente; para persistencia haría falta almacenamiento externo.
- Cuotas gratuitas de Gemini y Groq (ver el [Manual técnico](MANUAL_TECNICO.md)).

## Checklist antes de presentar

- [ ] **Regenerar las claves de API** (Gemini y Groq) y `SECRET_KEY` si alguna vez estuvieron en un repositorio, captura o chat. Nunca subas `backend/.env`.
- [ ] `datos.db` limpia: borra `backend/datos.db` y vacía `backend/subidas/` para empezar sin datos de pruebas (se recrea al iniciar).
- [ ] Ejecutar `scripts\crear_demo.py` para tener las cuentas demo.
- [ ] Tener preparados 1–2 **cuestionarios ya generados** (con un video con subtítulos y/o un archivo corto), publicados, con su código, por si falla internet o se agota la cuota.
- [ ] `pytest -q` en verde, `npm run lint` y `npm run build` sin errores.
- [ ] Probar el flujo completo: registro → generar → responder → panel → publicar → unirse con otra cuenta → resultados/CSV → encuesta SUS.
- [ ] Verificar `/api/salud` (proveedores configurados) y que `ffmpeg` funciona.
- [ ] Si usas nube: despertar Render con antelación; si usas túnel: confirmar `FRONTEND_URL` y `NEXT_PUBLIC_API_URL`.
- [ ] Plan B: video de la demo grabado y capturas en `docs/capturas/`.

## Si YouTube bloquea las descargas ("not a bot", 429, IpBlocked)

YouTube limita las IP que hacen muchas solicitudes. El bloqueo suele durar de horas a un día. Soluciones:

1. **Subir el archivo**: pestaña "Subir archivo" (MP4/MP3). No depende de YouTube.
2. **Cookies de YouTube** (recomendado para la presentación):
   - Instala en Chrome la extensión **"Get cookies.txt LOCALLY"**.
   - Abre youtube.com con tu sesión iniciada (de preferencia una cuenta de Google secundaria).
   - Exporta las cookies de youtube.com y guarda el archivo como `backend/cookies_youtube.txt`.
   - En `backend/.env` debe estar `YOUTUBE_COOKIES=cookies_youtube.txt` (ya configurado).
   - El archivo está en `.gitignore`: **nunca lo subas ni lo compartas** (da acceso a tu sesión).
3. **Cambiar de red**: por ejemplo, compartir datos desde el celular para obtener otra IP.
