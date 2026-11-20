# Plataforma de Aprendizaje Activo con IA

Aplicación web que convierte un **video de YouTube o Vimeo** (o un **archivo de video/audio subido**) en un **resumen**, una lista de **ideas clave** y un **cuestionario interactivo** generados con inteligencia artificial. Está pensada para el aprendizaje activo: el estudiante responde, recibe retroalimentación inmediata con la marca de tiempo del video donde se explica el tema y puede seguir su progreso; el docente puede publicar, editar y compartir cuestionarios y ver los resultados de su grupo.

Proyecto universitario. Todo el stack usa planes **gratuitos**; la interfaz, los comentarios y la documentación están en español.

> Documentación: [Índice completo](docs/DOCUMENTACION.md) · [Manual de usuario](docs/MANUAL_USUARIO.md) · [Manual técnico](docs/MANUAL_TECNICO.md) · [Referencia de API](docs/REFERENCIA_API.md) · [Guía de despliegue](docs/DESPLIEGUE.md) · [Plan de publicación gratuita](docs/PLAN_PUBLICACION.md) · [Operación y soporte](docs/OPERACION.md)

## Capturas de pantalla

Interfaz con la identidad visual de la CUL (azul institucional, franja naranja, Montserrat), pensada primero para celular, con modo oscuro. Más capturas (3 tamaños y modo oscuro) en [`docs/capturas/`](docs/capturas/).

| Pantalla | Captura |
|---|---|
| Inicio para visitantes (celular) | <img src="docs/capturas/movil_inicio_visitante.png" width="220" alt="Inicio en celular"> |
| Panel del estudiante (celular) | <img src="docs/capturas/movil_panel_estudiante.png" width="220" alt="Panel del estudiante en celular"> |
| Menú móvil (hamburguesa) | <img src="docs/capturas/movil_menu_estudiante.png" width="220" alt="Menú móvil"> |
| Cuestionario y panel del docente (escritorio) | <img src="docs/capturas/escritorio_visor_docente.png" width="700" alt="Visor y panel del docente"> |
| Resultados del docente (escritorio) | <img src="docs/capturas/escritorio_resultados_docente.png" width="700" alt="Resultados del docente"> |
| Comparación de grupos (tablet) | <img src="docs/capturas/tablet_comparar_docente.png" width="400" alt="Comparar grupos en tablet"> |

### Logo institucional

La interfaz muestra un monograma de texto («CUL») porque no incluye el escudo oficial. Si la institución lo autoriza, coloca el logo oficial en `frontend/public/logo-cul.png` (PNG, preferiblemente con fondo transparente o claro) y reinicia o recompila el frontend: la barra superior, el pie y las pantallas de acceso lo usarán automáticamente sobre una placa blanca.

## Funcionalidades

- Generación de resumen, ideas clave y cuestionario (opción múltiple, verdadero/falso y abiertas) a partir de YouTube, Vimeo o de un archivo de video/audio.
- Transcripción con subtítulos de YouTube y, si no existen (o en Vimeo), con Whisper (Groq). No se procesan transmisiones en vivo ni videos de más de `MAX_DURACION_MIN` minutos.
- IA con respaldo automático: Gemini → Groq → Ollama (local), con reintentos.
- Cuentas con roles (estudiante / docente), calificación **en el servidor** e historial de intentos.
- Docentes: publicar, compartir con código de 6 caracteres, editar preguntas, ver resultados, exportar CSV y medir la **ganancia de aprendizaje** (primer intento vs. último intento).
- Panel de estadísticas con gráfico de evolución y temas a reforzar.
- Encuesta de usabilidad **SUS** con análisis para el docente.
- **Medición de retención**: repaso diferido (post-test a 1, 3, 7 o 14 días) sin retroalimentación por pregunta, con retención = diferido / inicial × 100.
- **Diseño cuasi-experimental**: modo «grupo control» (solo video y preguntas), duplicado del cuestionario y comparación de grupos (n, media, desviación, d de Cohen, CSV anónimo).
- **Tiempo del docente**: tiempo de generación y de edición frente a la estimación manual (% de ahorro).
- **Datos personales (Ley 1581 de 2012)**: aceptación de la política en el registro, consentimiento opcional de investigación, página de privacidad y «Mi cuenta» (editar, descargar mis datos, eliminar cuenta).

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, tipografía Montserrat |
| Backend | FastAPI, SQLAlchemy 2, Pydantic 2, JWT + bcrypt |
| Base de datos | SQLite (local) o PostgreSQL (producción) |
| IA | Google Gemini, Groq (LLM y Whisper), Ollama (opcional) |
| Medios | youtube-transcript-api, yt-dlp (YouTube y Vimeo), ffmpeg |
| Pruebas | pytest (backend) |

## Arquitectura

```mermaid
flowchart LR
    U[Navegador<br/>Next.js] -->|REST + JWT| API[FastAPI]
    API --> BD[(SQLite / PostgreSQL)]
    API --> ST[Servicio de transcripción]
    ST --> YT[Subtítulos de YouTube]
    ST --> W[Whisper en Groq]
    API --> IA[Adaptador de IA<br/>Strategy + respaldo]
    IA --> G[Gemini]
    IA --> Q[Groq LLM]
    IA --> O[Ollama local]
    API --> F[(subidas/)]
```

Más detalle en el [Manual técnico](docs/MANUAL_TECNICO.md).

## Requisitos

- Windows 11 (también funciona en Linux/macOS), Python 3.12+, Node.js 20+.
- `ffmpeg` en el PATH (o `FFMPEG_PATH` en `.env`) para procesar audio.
- Claves gratuitas de [Google AI Studio](https://aistudio.google.com/apikey) y/o [Groq](https://console.groq.com/keys).

## Instalación y ejecución en local

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
# Edita .env: GEMINI_API_KEY, GROQ_API_KEY y SECRET_KEY
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

No hace falta activar el entorno virtual: se invoca el Python del `.venv` directamente. Para generar una `SECRET_KEY`:

```powershell
.\.venv\Scripts\python.exe -c "import secrets;print(secrets.token_urlsafe(48))"
```

La documentación interactiva de la API queda en <http://localhost:8000/docs>.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abre <http://localhost:3000>. Si el backend no está en `http://localhost:8000`, crea `frontend/.env.local` con `NEXT_PUBLIC_API_URL=http://localhost:8000`.

### Cuentas de demostración

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\crear_demo.py
```

Crea (si no existen) `docente@demo.com` y `estudiante@demo.com`, ambas con contraseña `Demo12345` y con los consentimientos (política de datos e investigación) aceptados. El script es idempotente y no genera cuestionarios (eso consume cuota de IA).

### Estructura académica institucional (Sprint 6)

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\sembrar_estructura.py
```

Idempotente (solo añade lo que falta): Facultad de Ingeniería → programa «Ingeniería de Sistemas y Computación» con 4 asignaturas y 5 resultados de aprendizaje de **ejemplo** (marcados «(ejemplo)»; reemplázalos desde `/admin`), las cuentas `coordinador@demo.com` y `admin@demo.com` (contraseña `Demo12345`) y un grupo del docente demo con el estudiante demo matriculado. Muestra el código de ingreso del grupo.

## Demo rápida

Con datos de demostración realistas (sin usar IA) en tres pasos:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\sembrar_demo.py      # estructura + 24 estudiantes, 5 cuestionarios, intentos, alertas, SUS...
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# en otra terminal:  cd frontend ; npm run dev     (abre http://localhost:3000)
```

| Rol | Correo | Contraseña | Qué mostrar |
|---|---|---|---|
| Docente | `docente@demo.com` | `Demo12345` | Panel con 24 estudiantes, resultados con **análisis de ítems**, repasos y retención, **Comparar** (ordenamiento vs. su versión control), alertas en «Cursos», clase en vivo, banco |
| Coordinador | `coordinador@demo.com` | `Demo12345` | Logro por RA, Bloom, asignaturas, tendencia de 6 semanas y alertas |
| Administrador | `admin@demo.com` | `Demo12345` | Estructura académica |
| Estudiante | `estudiante@demo.com` o cualquiera de los 24 (p. ej. `valentina.gomez@demo.com`) | `Demo12345` | Panel, cursos, tutorial de primer uso |

- `sembrar_demo.py` es idempotente; `--reset-demo` borra **solo** lo que sembró (y `--reset-demo --sembrar` lo rehace).
- Para que otros entren desde sus celulares en el mismo Wi-Fi: `.\iniciar_demo.ps1` (ver [Guía de despliegue](docs/DESPLIEGUE.md), incluye la regla del firewall).
- Los videos de la demo son públicos en español; si alguno deja de estar disponible, cambia su `youtube_id` en `backend/scripts/datos_demo.py`.

## Variables de entorno (`backend/.env`)

| Variable | Descripción | Por defecto |
|---|---|---|
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Clave y modelo de Gemini | — / `gemini-flash-latest` |
| `GROQ_API_KEY` | Clave de Groq (LLM y Whisper) | — |
| `GROQ_LLM_MODEL`, `GROQ_WHISPER_MODEL` | Modelos de Groq | `openai/gpt-oss-120b` / `whisper-large-v3-turbo` |
| `OLLAMA_URL`, `OLLAMA_MODEL` | Ollama local (opcional) | `http://localhost:11434` / `llama3.1:8b` |
| `PROVEEDORES_IA` | Orden de proveedores de IA | `gemini,groq,ollama` |
| `IDIOMA_TRANSCRIPCION` | Idioma de Whisper (`es`, `en`…). Vacío = detección automática | vacío |
| `FFMPEG_PATH` | Ruta a ffmpeg (carpeta o exe); vacío si está en el PATH | vacío |
| `FRONTEND_URL` | Origen(es) permitidos por CORS, separados por comas | `http://localhost:3000` |
| `DATABASE_URL` | SQLite o PostgreSQL (`postgresql+psycopg://usuario:clave@host/db`) | `sqlite:///./datos.db` |
| `SECRET_KEY` | Clave para firmar los JWT (obligatoria) | — |
| `TOKEN_EXPIRA_HORAS` | Vigencia de la sesión | `72` |
| `LIMITE_DIARIO_PROCESAMIENTOS` | Videos por usuario cada 24 h | `20` |
| `LIMITE_TUTOR_DIARIO` | Mensajes al tutor IA del video por usuario cada 24 h | `30` |
| `MAX_SUBIDA_MB` | Tamaño máximo de archivo subido | `200` |
| `MAX_DURACION_MIN` | Duración máxima (min) de videos de YouTube/Vimeo transcritos con audio + Whisper | `180` |

Frontend: `NEXT_PUBLIC_API_URL` (URL pública del backend).

## Pruebas automáticas

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Más de 300 casos (uno por sprint en `tests/test_sprint*.py`). Las pruebas usan una base de datos SQLite temporal y simulan la transcripción y la IA: no usan internet ni consumen cuota. Para el frontend: `npm run lint` y `npm run build`.

## Privacidad y consentimiento

El registro exige aceptar la **política de tratamiento de datos personales** (`/privacidad`, Ley 1581 de 2012); el consentimiento para el estudio de evaluación es opcional y revocable en `/cuenta`. Las exportaciones con fines de investigación (`/api/sus/resumen.csv`, `/api/comparar.csv`) incluyen solo a quienes consintieron. Antes de publicar la plataforma, reemplaza el marcador `[correo del responsable]` en `frontend/src/app/privacidad/page.tsx`. Recuerda que el texto de los videos se envía a Gemini y Groq (planes gratuitos que pueden usar los datos para mejorar sus servicios): no subas videos con datos personales.

## Despliegue

Consulta la [Guía de despliegue](docs/DESPLIEGUE.md): demo local, demo en red local (`iniciar_demo.ps1`), enlace público temporal (Cloudflare Tunnel) o nube gratuita (Vercel + Render + Neon; el repositorio incluye `render.yaml`). La app es instalable (PWA).

## Estructura

```
plataforma-aprendizaje-ia/
├── backend/        API FastAPI, pruebas y Dockerfile
├── frontend/       Aplicación Next.js
├── docs/           Manuales y guía de despliegue
└── README.md
```
