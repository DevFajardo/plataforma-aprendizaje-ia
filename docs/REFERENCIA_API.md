# Referencia de la API

Base: `http://localhost:8000` en local; documentación interactiva en `/docs` y `/redoc`.

Health check público: `GET /api/salud`.

**Autenticación:** todas las rutas salvo las marcadas «público» exigen `Authorization: Bearer <JWT>`. El token se obtiene en `POST /api/auth/login` o `POST /api/auth/registro` y dura `TOKEN_EXPIRA_HORAS` (72 h por defecto). En la clase en vivo también se usa un `token` de participante emitido por `POST /api/vivo/unirse`.

**Convenciones:** cuerpos JSON validados con Pydantic; las marcas de tiempo son `mm:ss`; las fechas se devuelven en ISO 8601 UTC con `Z`. Errores habituales: `400` validación de negocio, `401` sin token/válido, `403` rol o propiedad insuficiente, `404` recurso no visible, `409` conflicto (duplicado / intento ya respondido), `413` archivo demasiado grande, `422` error de esquema, `429` cuota excedida, `503` proveedor de IA caído, `410` sesión de vivo terminada.

> Los permisos indicados son los que aplica el servidor; el frontend oculta controles, pero **la seguridad real está en la API**.

## 1. App y autenticación (8)

| Método | Ruta | Permisos | Descripción |
|---|---|---|---|
| GET | `/api/salud` | público | Estado, proveedores configurados y orden de respaldo. |
| POST | `/api/auth/registro` | público | Crea cuenta (estudiante/docente), exige aceptar política de datos; devuelve token. |
| POST | `/api/auth/login` | público | Inicia sesión; devuelve token. |
| GET | `/api/auth/yo` | autenticado | Datos del usuario actual, incluidos consentimientos y tutorial. |
| PATCH | `/api/auth/cuenta` | autenticado | Edita nombre, contraseña (requiere `password_actual`) y consentimientos. |
| PUT | `/api/auth/tutorial` | autenticado | Marca/desmarca el tutorial del rol actual. |
| GET | `/api/auth/mis-datos` | autenticado | Derecho de acceso: usuario, cuestionarios, intentos, repasos y encuesta. |
| DELETE | `/api/auth/cuenta` | autenticado | Derecho de supresión; requiere `{password}`. |

## 2. Procesamiento de videos (3)

| Método | Ruta | Permisos | Descripción |
|---|---|---|---|
| POST | `/api/procesar` | autenticado | URL de YouTube/Vimeo → tarea en segundo plano. 400 URL inválida, 429 límite diario (20). |
| POST | `/api/procesar/archivo` | autenticado | Sube video/audio (multipart `archivo`, `num_preguntas`). 400 formato, 413 tamaño (200 MB). |
| GET | `/api/tareas/{tarea_id}` | dueño | Estado de la tarea (`pendiente`, `transcribiendo`, `generando`, `listo`, `error`). |

## 3. Cuestionarios del estudiante (8)

| Método | Ruta | Permisos | Descripción |
|---|---|---|---|
| GET | `/api/cuestionarios` | autenticado | Propios y ajenos publicados con los intentos del usuario. |
| GET | `/api/cuestionarios/{id}` | creador o publicado | Detalle; respuestas correctas solo para el creador. |
| DELETE | `/api/cuestionarios/{id}` | creador | Borra cuestionario, intentos y archivo subido si no se usa. |
| POST | `/api/cuestionarios/{id}/intentos` | creador o publicado | Inicia intento; devuelve `tipo` y `con_feedback`. |
| POST | `/api/intentos/{id}/responder` | dueño | Califica en servidor y devuelve retroalimentación (no en diferido/control). 409 si ya respondió. |
| POST | `/api/intentos/{id}/finalizar` | dueño | Puntaje final, tipo definitivo, crea/completa repaso y `revision`. |
| GET | `/api/intentos` | autenticado | Historial de intentos finalizados. |
| GET | `/api/repasos` | autenticado | Repasos pendientes (vencidos y próximos). |

## 4. Panel del docente (15)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/cuestionarios/{id}/publicar` | Publica/despublica; admite `estimacion_manual_min`. |
| POST | `/api/cuestionarios/{id}/tiempo-edicion` | Suma tiempo activo de edición (1-14400 s). |
| POST | `/api/cuestionarios/{id}/duplicar` | Copia (modo `aprendizaje` o `control`) con código nuevo. |
| GET | `/api/compartido/{codigo}` | Resuelve un código de 6 caracteres. |
| PATCH | `/api/cuestionarios/{id}` | Edita título, resumen, ideas clave, `repaso_dias`, `grupo_id` y estimación. |
| GET | `/api/cuestionarios/{id}/ras` | RA elegibles según la asignatura del grupo. |
| POST | `/api/cuestionarios/{id}/preguntas` | Agrega pregunta (tipo, opciones, respuesta, marca, RA, Bloom). |
| PUT | `/api/preguntas/{id}` | Edita pregunta; invalida su verificación si cambia enunciado/opciones/tipo/respuesta. |
| DELETE | `/api/preguntas/{id}` | Borra y reordena. |
| POST | `/api/cuestionarios/{id}/reordenar` | Reordena por lista de ids. |
| POST | `/api/cuestionarios/{id}/verificar` | (Re)verifica calidad de todas las preguntas; 503 si la IA falla. |
| PUT | `/api/intentos/{id}/abiertas/{pregunta_id}/nota` | Fija nota final 0-100 de una abierta y recalcula el intento. |
| GET | `/api/cuestionarios/{id}/resultados` | Intentos, aciertos, abiertas, análisis de ítems, ganancia y retención. |
| GET | `/api/cuestionarios/{id}/intentos/{intento_id}/detalle` | Detalle de un intento. |
| GET | `/api/cuestionarios/{id}/resultados.csv` | CSV del curso con BOM y anti-fórmulas. |

Todas las rutas de esta sección exigen **docente creador** del cuestionario.

## 5. Estadísticas, comparación, medios y SUS (8)

| Método | Ruta | Permisos | Descripción |
|---|---|---|---|
| GET | `/api/estadisticas/yo` | autenticado | Métricas personales; si es docente, bloque `docente` con ahorro de tiempo. |
| GET | `/api/comparar?a=&b=` | creador de ambos | n, media, desviación, d de Cohen e interpretación (400 si `a == b`). |
| GET | `/api/comparar.csv?a=&b=` | creador de ambos | Datos anónimos solo de quienes consintieron investigación. |
| GET | `/api/medios/{nombre}` | público | Sirve subidas con `Range`; nombre `uuid-hex.extensión` (400 si no). |
| POST | `/api/sus` | autenticado | Guarda/actualiza los 10 ítems (1-5) y comentario. |
| GET | `/api/sus/mia` | autenticado | Tu respuesta SUS (404 si no). |
| GET | `/api/sus/resumen` | docente | n, promedio, desviación, distribución y promedio por ítem. |
| GET | `/api/sus/resumen.csv` | docente | CSV anónimo solo con consentimiento. |

## 6. Administración académica (19)

Todas exigen **admin** salvo `GET /api/catalogo/asignaturas` (docente/coordinador/admin).

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `/api/admin/facultades` | Listar/crear facultades. |
| PATCH/DELETE | `/api/admin/facultades/{id}` | Editar/eliminar (409 si tiene programas). |
| GET/POST | `/api/admin/programas` | Listar/crear programas (`codigo` único). |
| PATCH/DELETE | `/api/admin/programas/{id}` | Editar/eliminar. |
| GET/POST | `/api/admin/asignaturas` | Listar (`?programa_id`)/crear. |
| PATCH/DELETE | `/api/admin/asignaturas/{id}` | Editar/eliminar (no si tiene grupos). |
| PUT | `/api/admin/asignaturas/{id}/ras` | Asigna RA del mismo programa. |
| GET/POST | `/api/admin/ras` | Listar (`?programa_id`)/crear (código único por programa). |
| PATCH/DELETE | `/api/admin/ras/{id}` | Editar/eliminar (las preguntas quedan sin RA). |
| GET | `/api/admin/usuarios` | Lista de usuarios con rol y programa. |
| PATCH | `/api/admin/usuarios/{id}` | Cambia rol y programa (un admin no se quita su propio rol). |

## 7. Cursos y grupos (11)

| Método | Ruta | Permisos | Descripción |
|---|---|---|---|
| GET | `/api/catalogo/asignaturas` | docente/coordinador/admin | Asignaturas para crear grupos. |
| GET | `/api/grupos` | docente/coordinador/admin | Según alcance del rol. |
| POST | `/api/grupos` | docente | Crea grupo con código de ingreso de 6 caracteres. |
| PATCH/DELETE | `/api/grupos/{id}` | docente dueño o admin | Edita/elimina. |
| POST | `/api/grupos/{id}/nuevo-codigo` | docente dueño o admin | Renueva código. |
| GET | `/api/grupos/{id}/matriculados` | quien ve el grupo | Estudiantes inscritos. |
| DELETE | `/api/grupos/{id}/matriculados/{estudiante_id}` | docente dueño o admin | Quita matrícula. |
| POST | `/api/mis-cursos/unirse` | estudiante | `{codigo}`; 404 inexistente, 409 ya matriculado. |
| GET | `/api/mis-cursos` | estudiante | Cursos con cuestionarios publicados y mejor resultado. |
| DELETE | `/api/mis-cursos/{grupo_id}` | estudiante | Salir del curso. |

## 8. Coordinación y alertas (6)

| Método | Ruta | Permisos | Descripción |
|---|---|---|---|
| GET | `/api/coordinacion/resumen` | coordinador (su programa) / admin | Logro por RA, Bloom, asignatura/grupo, tendencia y periodos. |
| GET | `/api/coordinacion/reporte-ra.pdf` | coordinador / admin | PDF institucional. |
| GET | `/api/cuestionarios/{id}/reporte.pdf` | docente creador | PDF de resultados del cuestionario/grupo. |
| GET | `/api/alertas?grupo_id` | docente/coordinador/admin | Alertas vigentes calculadas al vuelo. |
| POST | `/api/alertas/atender` | ídem | Registra atención `{grupo_id, estudiante_id, nota}`. |
| GET | `/api/alertas/seguimientos` | ídem | Historial de atenciones. |

## 9. Clase en vivo (9)

| Método | Ruta | Permisos | Descripción |
|---|---|---|---|
| POST | `/api/cuestionarios/{id}/vivo` | docente dueño | Crea sesión; devuelve PIN. |
| GET | `/api/vivo/sesiones/{id}` | docente dueño | Datos de la sesión (410 si terminó). |
| POST | `/api/vivo/sesiones/{id}/accion` | docente dueño | `iniciar`, `siguiente`, `saltar`, `finalizar` (respaldo HTTP). |
| POST | `/api/vivo/unirse` | público | `{pin, apodo}` → token de participante. Máx. 200. |
| GET | `/api/vivo/{pin}/estado` | participante / presentador / público | Sondeo de respaldo; el público ve datos mínimos. |
| POST | `/api/vivo/{pin}/responder` | participante | Respuesta por HTTP (respaldo). |
| **WS** | `/ws/vivo/{pin}?token=<JWT\|participante>` | docente dueño / participante | Tiempo real (cierres 4404/4403/4401). |
| GET | `/api/cuestionarios/{id}/vivo` | docente dueño | Historial de sesiones. |
| GET | `/api/cuestionarios/{id}/vivo.csv` | docente dueño | CSV (BOM y anti-fórmulas). |

**Protocolo WebSocket.** Cliente → servidor: `{"accion":"iniciar|siguiente|saltar|finalizar"}`, `{"accion":"responder","respuesta":"..."}`, `{"accion":"ping"}`. Servidor → cliente: `{"tipo":"estado", ...}` (snapshot con `estado`, pregunta sin respuesta correcta, `respondieron`, `restante_ms`, `ranking` y `yo`) o `{"tipo":"error","mensaje":...}`. El cliente reintenta con *backoff* y, tras 3 fallos, pasa al sondeo HTTP cada 1,5 s (`frontend/src/lib/vivo.ts`).

## 10. Notificaciones, tutor, banco y videos (16)

| Método | Ruta | Permisos | Descripción |
|---|---|---|---|
| GET | `/api/notificaciones` | autenticado | Lista paginada (`?pagina&por_pagina&solo_no_leidas`). |
| GET | `/api/notificaciones/no-leidas` | autenticado | Contador. |
| POST | `/api/notificaciones/leer-todas` | autenticado | Marca todas como leídas. |
| POST | `/api/notificaciones/{id}/leer` | autenticado (dueño) | Marca una como leída. |
| GET | `/api/cuestionarios/{id}/tutor` | creador o publicado | Disponibilidad, historial, mensajes restantes y 3 sugerencias. |
| POST | `/api/cuestionarios/{id}/tutor` | ídem | `{pregunta}` (1-1000) → respuesta con citas; 403 bloqueado, 429 límite, 503 IA caída. |
| POST | `/api/cuestionarios/{id}/tutor/nueva` | ídem | Nueva conversación. |
| POST | `/api/preguntas/{id}/banco` | docente creador | Copia al banco con visibilidad y etiquetas. |
| GET | `/api/banco` · `/api/banco/filtros` | docente/coordinador/admin | Búsqueda paginada y valores de filtros. |
| PATCH/DELETE | `/api/banco/{id}` | autor | Edita visibilidad/etiquetas o elimina. |
| POST | `/api/banco/{id}/agregar` | docente | Copia la pregunta a un cuestionario propio. |
| GET | `/api/videos/{id}/subtitulos.vtt` | creador o publicado | WebVTT (se descarga con `fetch` porque `<track>` no envía JWT). |
| GET | `/api/videos/{id}/transcripcion.txt` | creador o publicado | Descarga con marcas `[mm:ss]`. |
| GET | `/api/videos/{id}/transcripcion` | creador o publicado | JSON de segmentos. |

## 11. Límites que puede devolver la API

| Variable | Límite | Error |
|---|---|---|
| `LIMITE_DIARIO_PROCESAMIENTOS` | 20 videos / usuario / 24 h | 429 |
| `LIMITE_TUTOR_DIARIO` | 30 mensajes / usuario / 24 h | 429 |
| `MAX_SUBIDA_MB` | 200 MB por archivo | 413 |
| `MAX_DURACION_MIN` | 180 min por video | `Tarea` en `error` con mensaje |
| Participantes en vivo | 200 por sesión | 409 |
| `TOKEN_EXPIRA_HORAS` | 72 h de sesión | 401 |

La definición autoritativa de los esquemas está en `backend/app/schemas_api.py` y la implementación en `backend/app/routers/`. Esta tabla se actualiza con cada cambio de endpoints.
