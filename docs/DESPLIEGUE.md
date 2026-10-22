# Guía de despliegue

Hay dos caminos. Para la **presentación** se recomienda la **opción A (demo local)**: no depende de servicios externos, YouTube no bloquea tu conexión de casa y tienes control total.

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

## Opción B: nube gratuita

| Pieza | Servicio | Notas |
|---|---|---|
| Frontend | **Vercel** | Plan *Hobby* gratuito. |
| Backend | **Render** (con el `Dockerfile`) o **Hugging Face Spaces** (Docker) | Plan gratuito con limitaciones (abajo). |
| Base de datos | **Neon** o **Supabase** (PostgreSQL) | El disco del backend gratuito es efímero: SQLite se perdería. |

### 1. Base de datos PostgreSQL

1. Crea un proyecto en [Neon](https://neon.tech) o [Supabase](https://supabase.com) y copia la cadena de conexión.
2. Conviértela al formato de SQLAlchemy con el driver `psycopg` (3):

   ```
   postgresql+psycopg://usuario:clave@host/basededatos?sslmode=require
   ```

   (Si el proveedor entrega `postgres://…` o `postgresql://…`, el backend lo convierte automáticamente.) Las tablas se crean solas al arrancar.

### 2. Backend en Render

1. Sube el proyecto a GitHub (el `.env` no se versiona).
2. En Render: **New → Web Service** → tu repositorio → **Root Directory** `backend` → **Runtime: Docker** (usa `backend/Dockerfile`; Render define `$PORT`).
3. Variables de entorno: `SECRET_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `PROVEEDORES_IA=gemini,groq`, `DATABASE_URL` (la de PostgreSQL), `FRONTEND_URL` (la URL de Vercel; admite varias separadas por comas) y, si quieres, `IDIOMA_TRANSCRIPCION`.
4. Despliega y comprueba `https://TU-BACKEND.onrender.com/api/salud`.
5. Para crear las cuentas demo, abre una *Shell* del servicio y ejecuta `python scripts/crear_demo.py`, o simplemente regístralas desde la aplicación.

**Hugging Face Spaces**: crea un Space de tipo *Docker*, sube el contenido de `backend/` y define el puerto `7860` (variable `PORT=7860` y `app_port: 7860` en el README del Space). Las variables se configuran como *Secrets*.

### 3. Frontend en Vercel

1. **Add New → Project** → importa el repositorio → **Root Directory** `frontend`.
2. Variable de entorno: `NEXT_PUBLIC_API_URL=https://TU-BACKEND.onrender.com`.
3. Despliega. Después añade la URL de Vercel a `FRONTEND_URL` del backend (CORS) y reinícialo.

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
