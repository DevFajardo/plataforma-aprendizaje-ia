# Operación, mantenimiento y solución de problemas

Complemento del [Manual de despliegue](DESPLIEGUE.md) y del [Plan de publicación](PLAN_PUBLICACION.md). Orientado a quien deja la plataforma corriendo y debe responder cuando algo falla.

## 1. Diagnóstico rápido

| Síntoma | Causa probable | Acción |
|---|---|---|
| `/api/salud` tarda ~1 min o muestra página de carga | Render Free se durmió | Visita `/api/salud` unos minutos antes; considera un *ping* programado (consume horas gratis). |
| «El video no tiene subtítulos y no hay GROQ_API_KEY» | Falta la clave de Groq | Configura `GROQ_API_KEY` y reinicia el backend. |
| `IpBlocked` / `RequestBlocked` / *«not a bot»* | IP de nube bloqueada por YouTube | Usa video con subtítulos, sube el MP4 o sirve desde casa con Cloudflare Tunnel. Ver [Plan de publicación §2.1](PLAN_PUBLICACION.md#21-youtube-desde-ips-de-nube-el-bloqueo-más-importante). |
| `429` al generar | Cuota diaria agotada (20 videos propios o IA) | Revisa `LIMITE_DIARIO_PROCESAMIENTOS`, cuota de Gemini/Groq en consola y el orden de `PROVEEDORES_IA`. |
| Tarea queda en `pendiente` para siempre | Proceso reiniciado a mitad | Al arrancar, `lifespan` marca las huérfanas como `error`; vuelve a generar. |
| El tutor responde 503 | Todos los proveedores de IA fallaron | Revisa claves y cuotas; el cuestionario y las respuestas ya registradas no se pierden. |
| Cuestionario «listo» con preguntas sin verificar | Falló la verificación en lote | Pulsa «Verificar calidad» (`POST /api/cuestionarios/{id}/verificar`). |
| La clase en vivo se queda «sin conexión» | Más de 3 fallos WebSocket → sondeo HTTP; o varias instancias | El cliente ya cambia a HTTP solo. Si hay varias instancias, reduce a una. |
| Los participantes no ven el QR bien | `NEXT_PUBLIC_URL_PUBLICA` apunta a `localhost` | Recompila el frontend con la URL pública real. |
| Error de CORS en consola | Falta la URL de Vercel en `FRONTEND_URL` | Añádela (sin barra final) y reinicia el backend. |
| *Mixed content* / `wss` fallido | `NEXT_PUBLIC_API_URL` usa `http` en un sitio https | Cambia a `https` y vuelve a desplegar el frontend. |
| Los archivos subidos desaparecen | Disco efímero de Render | Normal en gratuito; sube de nuevo o añade almacenamiento de objetos. |
| El coordinador no ve datos | Sin `programa_id` o periodo sin grupos | Asigna programa en `/admin` y revisa el filtro de periodo. |

## 2. Qué revisar cada semana

1. **Salud:** `GET /api/salud` → proveedores y orden de respaldo.
2. **Cuotas:** AI Studio → *Rate limits*; Groq → *Limits* (modelos LLM y Whisper).
3. **Render:** horas consumidas, ancho de banda y minutos de build (Billing → Monthly Included Usage).
4. **Neon:** almacenamiento (1 GB), CU-h y egreso. Si se acerca al límite, exporta con `pg_dump`.
5. **Errores:** logs de Render y consola del navegador; busca `429`, `IpBlocked`, `RuntimeError`.
6. **Datos demo:** si alguien borró cuentas, `sembrar_demo.py --reset-demo --sembrar` reconstruye solo lo sembrado.

## 3. Respaldos

**SQLite (demo local):** copia `backend/datos.db` con el servicio detenido. Ejemplo en PowerShell:

```powershell
Copy-Item backend\datos.db "C:\Respaldos\datos-$(Get-Date -Format yyyyMMdd).db"
```

**PostgreSQL (Neon):** usa el botón *Export* / `pg_dump` desde la consola. Neon mantiene 6 h de restauración instantánea y 1 snapshot manual en el plan gratuito.

**Antes de borrar algo:** `DELETE /api/auth/cuenta` elimina intentos, repasos, encuesta, tareas y cuestionarios propios; no es reversible. `sembrar_demo.py --reset-demo` borra únicamente las filas marcadas en `registro_demo`.

## 4. Rotación de claves y secretos

1. Genera nuevas claves en Google AI Studio y Groq Console; revoca las anteriores.
2. Genera `SECRET_KEY` con `python -c "import secrets;print(secrets.token_urlsafe(48))"`.
   **Aviso:** cambiarla invalida todos los JWT vigentes (los usuarios deben volver a iniciar sesión).
3. Actualiza las variables en Render (y `NEXT_PUBLIC_API_URL` en Vercel si cambia el dominio).
4. Reinicia el backend y comprueba `/api/salud`.
5. Nunca pongas claves en `render.yaml`, `README`, capturas ni el chat. `.env` y `.env.local` están en `.gitignore`.
6. Si alguna vez subiste una clave a Git, **revócala**: borrarla del historial no basta.

## 5. Cambios de código

```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q

# Frontend
cd frontend
npm run lint
npm run build
```

Buenas prácticas del repo: los tests usan SQLite temporal, simulan transcripción e IA y no consumen red; un endpoint nuevo debe añadirse a `REFERENCIA_API.md`; una regla de negocio nueva, al `MANUAL_TECNICO.md`.

## 6. Checklist antes de publicar o presentar

- [ ] Claves y `SECRET_KEY` vigentes, nunca versionadas.
- [ ] Modelo de Gemini existente y con cuota suficiente ( Flash-Lite recomendado).
- [ ] Proveedores en orden `gemini,groq` y `/api/salud` correcto.
- [ ] Video con subtítulos y/o MP4 local listo como plan B.
- [ ] Render despierto (o backend local con túnel) y un solo worker.
- [ ] CORS y URL pública configurados; https en frontend y backend.
- [ ] Datos demo sembrados; contraseñas demo cambiadas si es público.
- [ ] `pytest`, `npm run lint` y `npm run build` en verde.
- [ ] Flujo completo probado desde un celular: registro → generar → responder → unirse → resultados → vivo.
- [ ] Texto de `/privacidad` con el correo del responsable.

## 7. Plan B para la presentación

Si falla internet, la nube o la IA: abre el backend local con `sembrar_demo.py` (datos realistas, sin IA), ejecuta `npm run build && npm run start` y muestra los cuestionarios ya generados. El [guion de la demo](GUION_DEMO.md) incluye tiempos, frases y plan B.
