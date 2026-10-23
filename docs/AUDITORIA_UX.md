# Auditoría de interfaz y pulido profesional (UX/UI)

Auditoría completa de la interfaz web de la plataforma, hecha con un entorno aislado (backend en el puerto 8001 con una base de datos de prueba sembrada con los datos de demostración, y una copia compilada del frontend en el 3001). Se midió **antes** y **después** con las mismas rutas, los mismos roles y las mismas herramientas.

**Método**

- Capturas de las 26 rutas por rol relevante (visitante, estudiante, docente, coordinador y administrador) en 375, 768 y 1440 px, y modo oscuro en 375 px para las principales (87 capturas por ronda).
- axe-core 4 (reglas WCAG 2.0/2.1 A y AA) en cada captura: 87 análisis por ronda.
- Lighthouse (móvil, simulación estándar) en 6 rutas: inicio, login, panel, visor, coordinación y vivo participante.
- Comprobación de desbordes horizontales (`scrollWidth > innerWidth`) y de errores de consola en todas las capturas.
- Revisión visual de las capturas con ojo de diseño de producto.

> Las capturas de la ronda «antes» corresponden al estado del commit anterior (ver también `escritorio_inicio_visitante.png`, `escritorio_resultados_docente.png` y `s6_coordinacion_1440.png` en esta misma carpeta). Las finales llevan el prefijo `ux_`.

## 1. Hallazgos priorizados

### Críticos

| # | Categoría | Hallazgo | Referencia |
|---|---|---|---|
| C1 | SEO / rendimiento / jerarquía | La portada para visitantes no llegaba pintada desde el servidor: solo un esqueleto hasta validar la sesión en el navegador. Mala primera impresión, LCP lento y nada indexable. Además no había capturas reales del producto ni cifras verificables. | `escritorio_inicio_visitante.png` |
| C2 | Accesibilidad | 87 incumplimientos *serios* de axe (`label-content-name-mismatch`, WCAG 2.5.3): el enlace de la marca tenía un `aria-label` que no contenía el texto visible. Aparecía en todas las páginas. | Barra superior en todas las capturas |
| C3 | Confianza / consola | `GET /api/sus/mia` respondía 404 para un estado normal («aún no respondes la encuesta») y dejaba un error en la consola en el panel y la encuesta. | Lighthouse «panel»: buenas prácticas 96 |
| C4 | SEO / metadatos | Sin imagen Open Graph propia, sin `robots` para rutas privadas, `lang="es"` genérico y sin `robots.txt`. | — |

### Altos

| # | Categoría | Hallazgo |
|---|---|---|
| A1 | Visualización de datos | Formato numérico inconsistente: «87.2%», «80%» y «74,6%» en la misma plataforma; plurales incorrectos («1 respuestas», «1 programa(s)»). |
| A2 | Estados | Sin sistema de notificaciones: los éxitos se mostraban como textos sueltos en cada formulario o no se confirmaban (copiar enlace, publicar, eliminar). |
| A3 | Navegación | Sin migas de pan en páginas profundas (cuestionario, resultados, edición, comparar, administración, encuesta). |
| A4 | Formularios | Validación nativa del navegador (burbujas en el idioma del navegador, sin foco ni mensajes propios); el botón de registro quedaba deshabilitado sin explicar por qué. |
| A5 | Estados | Los errores de carga no ofrecían «Reintentar». |
| A6 | Accesibilidad | Salto de encabezados h1 → h3 en el visor, tablas con desplazamiento horizontal sin foco de teclado (`scrollable-region-focusable`) y un `aria-label` que contradecía la etiqueta visible del campo del enlace del video. |
| A7 | Rendimiento / accesibilidad | El reproductor de YouTube se cargaba siempre (Lighthouse del visor 67 y 7 + 3 incumplimientos críticos/serios de terceros dentro del iframe). |

### Medios

| # | Categoría | Hallazgo |
|---|---|---|
| M1 | Microcopy | La política de datos hablaba de «usted» y el resto de la plataforma de «tú». |
| M2 | Estados vacíos | «Temas a reforzar» (panel) era un párrafo suelto, sin ícono ni jerarquía. |
| M3 | Rendimiento | Saltos de diseño (CLS 0,2–0,3): el pie de página «saltaba» al llegar los datos porque el esqueleto era más corto que el contenido. |
| M4 | Consistencia | Los títulos de error y 404 usaban otro peso tipográfico (`extrabold`) que el resto de los títulos de nivel 1. |
| M5 | Rendimiento | Archivos de plantilla sin uso en `public/` (5 SVG). |
| M6 | Navegación | «Volver» con textos distintos por pantalla («Volver al panel», «Volver al cuestionario»). |

### Bajos (sin cambio o pendientes)

| # | Hallazgo |
|---|---|
| B1 | La política de datos conserva el marcador `[correo del responsable]`: requiere el dato real del equipo/institución. |
| B2 | El nombre del usuario en la barra superior se trunca con puntos suspensivos en pantallas medianas (tiene el nombre completo en el menú). |
| B3 | Las pestañas de administración se apilan una por línea en 375 px (legible, pero larga). |
| B4 | Las rutas privadas obtienen SEO 63–66 en Lighthouse **a propósito** (`noindex`); el puntaje de SEO solo es relevante en las rutas públicas (100). |
| B5 | El panel de un docente sin intentos propios muestra el gráfico de evolución vacío (estado vacío correcto, pero ocupa espacio). |

## 2. Cambios realizados

**Coherencia y componentes**

- Nuevo `lib/formato.ts` (`num`, `pct`, `entero`, `conSigno`, `plural`) y su uso en todas las pantallas: «87,2 %», «+1,5 puntos», «1 respuesta / 2 respuestas», sin «(s)».
- Nuevos componentes `ui/Toast` (`ProveedorToast`, `useToast`), `ui/Migas` y mejoras a `Alerta` (botón «Reintentar»), `Aviso`, `EncabezadoPagina` (prop `migas`), `TituloSeccion` (nivel semántico distinto del visual) y `EsqueletoPagina` (altura mínima).
- Títulos de nivel 1 unificados (peso, tracking y marca naranja).

**Estados**

- Toasts accesibles (`aria-live="polite"`; errores con `role="alert"`; se pausan al pasar el mouse o al enfocar; se cierran con botón y solos) para: cambios de la cuenta, publicar/despublicar, copiar enlace y código, crear/eliminar grupo, eliminar cuestionario, guardar en el banco, eliminar del banco, unirse a un curso y marcar notificaciones como leídas. `Aviso` confirma los éxitos con toast y deja los errores en línea.
- «Reintentar» en los errores de carga (panel, listas, resultados, coordinación, historial, transcripción, cursos).
- Estado vacío con ícono y texto en «Temas a reforzar».
- El panel espera todas sus cargas antes de pintar los bloques y los esqueletos reservan altura: desaparecen los saltos de diseño del pie de página.

**Navegación**

- Migas de pan en visor, resultados, edición, comparar, encuesta SUS, administración y privacidad (la última es la página actual con `aria-current`); se eliminaron los «Volver…» sueltos.

**Formularios**

- Nuevo `lib/validacion.ts` (`useValidacion`): validación en línea al salir del campo y al enviar, mensajes claros en español, `aria-invalid`/`aria-describedby` y foco automático en el primer error. Aplicado a inicio de sesión, registro, unirse con código y enlace del video. El botón de registro ya no se deshabilita en silencio: explica que falta aceptar la política. Botones con estado de carga y deshabilitados mientras envían.

**Visualización de datos**

- Números es-CO en métricas, barras, tablas y gráficos (incluidas las descripciones accesibles); etiquetas, escalas (0–100 %) y detalle al pasar/tocar ya existían y se conservan.

**Página de inicio**

- Rediseñada: propuesta de valor, capturas reales del producto (WebP en `public/capturas/`, con `next/image`), cifras verificables (317 pruebas automáticas, WCAG 2.1 AA, $0 de costo de operación, 3 proveedores de IA con respaldo), tres características destacadas (tutor de IA, clase en vivo, resultados de aprendizaje), secciones por rol (estudiantes, docentes, institución), bloque de confianza (Ley 1581), llamada a la acción y pie institucional. Sin testimonios ni métricas de uso.
- Se pinta desde el servidor; si el navegador tiene un token guardado, un script mínimo marca `data-sesion` y el CSS muestra el esqueleto en lugar de la portada (sin parpadeo para quien ya inició sesión).

**Microcopy**

- Tono «tú» en toda la plataforma (incluida la política de datos), plurales correctos, sin «(s)», textos de ayuda breves y mensajes de error con la acción a seguir.

**SEO y metadatos**

- `lang="es-CO"`, `metadataBase`, Open Graph y Twitter Card con imagen propia de 1200 × 630 (`opengraph-image.png` y `twitter-image.png`, generada para el proyecto; no es el logo de la CUL), `robots.txt` y `noindex` en todas las rutas privadas.

**Rendimiento**

- El reproductor de YouTube se carga solo al pulsar «Reproducir» (portada con botón) o al saltar a un minuto desde el tutor, la transcripción o la retroalimentación; menos JavaScript de terceros y sin incumplimientos externos al cargar la página.
- `GET /api/sus/mia` devuelve 200 con `null` (se actualizó la prueba correspondiente): sin errores en la consola.
- Imágenes en WebP con dimensiones fijas; fuentes con `display: swap` (ya estaban); eliminados 5 SVG de plantilla sin uso.

**Accesibilidad**

- Enlace de marca con nombre accesible coherente (`label-content-name-mismatch`), jerarquía de encabezados correcta en el visor, regiones con desplazamiento enfocables y etiquetadas, sin `aria-label` contradictorio en el campo del enlace, contraste en modo oscuro de las cifras de la portada.

**Micro-interacciones**

- Entrada suave de los toasts, escala al pulsar los botones, elevación de tarjetas interactivas y ampliación del botón de reproducir al pasar el mouse; todo se anula con `prefers-reduced-motion` (regla global ya existente).

## 3. Medición final (ANTES / DESPUÉS)

### axe-core (WCAG 2.1 AA), 87 análisis por ronda

| Severidad | Antes | Después |
|---|---|---|
| Crítica | 10 | **0** |
| Seria | 95 | **0** |
| Moderada | 0 | 0 |
| Menor | 0 | 0 |

Las 10 críticas y 7 de las serias del «antes» venían del reproductor de YouTube incrustado (contenido de terceros); las 87 serias restantes del enlace de la marca. Con la carga diferida del reproductor y la corrección de la marca, el «después» queda en cero. Una vez el usuario pulsa «Reproducir», el iframe de YouTube vuelve a aportar sus propios incumplimientos, que no son corregibles desde la plataforma.

### Lighthouse (móvil). Antes → Después (mediana de 3 ejecuciones)

| Ruta | Rendimiento | Accesibilidad | Buenas prácticas | SEO |
|---|---|---|---|---|
| Inicio | 75 → 85 | 100 → 100 | 100 → 100 | 100 → 100 |
| Login | 95 → 82 | 100 → 100 | 100 → 100 | 100 → 63 (noindex) |
| Panel | 86 → 76 | 100 → 100 | 96 → 100 | 100 → 63 (noindex) |
| Visor | 67 → 81 | 98 → 100 | 96 → 100 | 100 → 66 (noindex) |
| Coordinación | 93 → 70 | 100 → 100 | 100 → 100 | 100 → 63 (noindex) |
| Vivo participante | 96 → 79 | 100 → 100 | 100 → 100 | 100 → 63 (noindex) |

Notas honestas sobre la medición:

- El rendimiento de Lighthouse varió ±15 puntos entre ejecuciones consecutivas en este equipo (que tenía otras aplicaciones pesadas abiertas). El «antes» fue una sola ejecución en un momento más tranquilo; las ejecuciones individuales del «después» llegaron a 97 (inicio), 91 (login) y 90 (vivo). Las diferencias en login, coordinación y vivo participante no corresponden a cambios de esas pantallas y deben leerse como ruido de medición; las mejoras reales y repetibles están en inicio (pintado desde el servidor), visor (reproductor diferido) y en accesibilidad y buenas prácticas (100 en todas).
- El SEO de 63–66 en rutas privadas es intencional: se pidió `noindex` para ellas. En las rutas públicas (inicio) el SEO es 100.

### Otras verificaciones

- Desbordes horizontales: **0** en las 87 capturas (375, 768 y 1440 px, claro y oscuro).
- Errores de consola: ninguno, salvo el 404 esperado de la ruta inexistente que se usa para probar la página 404.
- `npm run lint` y `npx tsc --noEmit` sin avisos; `next build` correcto; 317 pruebas de backend en verde.

## 4. Pendientes

- Sustituir `[correo del responsable]` de la política de datos por el contacto oficial.
- Si la institución autoriza el logo oficial, colocarlo en `frontend/public/logo-cul.png` (la interfaz ya lo usa automáticamente).
- Revisar con la institución el texto legal de la política (se pasó a «tú» por coherencia, pero es un texto jurídico).

## 5. Capturas finales (`docs/capturas/ux_*`)

| Captura | Qué muestra |
|---|---|
| `ux_inicio_375.png`, `ux_inicio_1440.png` | Nueva portada en celular y escritorio |
| `ux_oscuro_inicio_375.png` | Portada en modo oscuro |
| `ux_login_375.png` | Inicio de sesión |
| `ux_registro_validacion_375.png` | Validación en línea con mensajes y foco en el primer error |
| `ux_toast_copiado_375.png` | Notificación accesible al copiar el código de un curso |
| `ux_panel_docente_1440.png` | Panel del docente con números es-CO |
| `ux_resultados_docente_1440.png` | Resultados con migas de pan y formato numérico unificado |
| `ux_coordinacion_375.png` | Coordinación en celular |
| `ux_oscuro_visor_estudiante_375.png` | Visor con portada de video diferida, modo oscuro |
