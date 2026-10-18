# Protocolo de evaluación con usuarios

> Este documento reproduce el Anexo A del documento de proyecto (versión 6): *Desarrollo de una plataforma web de aprendizaje activo basada en inteligencia artificial para la generación automática de evaluaciones a partir de contenido audiovisual*. Los campos entre corchetes deben completarse antes de aplicar el protocolo. El formato de consentimiento informado se encuentra en el Anexo B (`Anexo_B_Consentimiento_Informado.docx`) y la escala SUS en el Anexo C del documento.

## A.1 Propósito y alcance del protocolo

Este protocolo describe, paso a paso, cómo se aplicará la evaluación con usuarios de la Plataforma de Aprendizaje Activo con IA. Su finalidad es medir (a) la comprensión y la ganancia de aprendizaje, (b) la retención diferida, (c) la usabilidad percibida mediante la escala SUS y (d) el ahorro de tiempo del docente al elaborar cuestionarios. Debe ser leído por el investigador y por el docente asesor antes de la primera sesión. Los datos que se registren con este protocolo son los únicos que se reportarán en la sección de resultados de la evaluación; mientras no se apliquen, dicha sección permanece como plantilla pendiente.

## A.2 Diseño y grupos

- **Diseño:** cuasi-experimental con grupo experimental y grupo control, medición previa (pre-test), medición inmediata (post-test) y medición diferida (post-test diferido).
- **Grupo experimental:** usa la plataforma completa (resumen, ideas clave, cuestionario con retroalimentación inmediata y marca de tiempo del video).
- **Grupo control:** usa el modo «grupo control» de la plataforma (el cuestionario se responde sin resumen ni retroalimentación); durante la fase de estudio revisa el video y sus propios apuntes.
- **Asignación:** por grupos intactos (por ejemplo, dos secciones del mismo curso) o, si no es posible, por disponibilidad de horario. No se aleatoriza; la equivalencia inicial se verifica con el pre-test. Registrar el criterio de asignación realmente usado: [completar].
- **Muestra propuesta:** mínimo 40 participantes (20 por grupo); meta de 52 (26 por grupo) para prever deserción en la medición diferida.

## A.3 Materiales y preparación (antes de la sesión)

1. Seleccionar un video corto (10 a 15 minutos), en español, sobre un tema de Ingeniería de Sistemas que los participantes no hayan visto en clase. Verificar que sea de licencia abierta, propio o que cuente con autorización; **preferir un archivo MP4 almacenado localmente** para no depender de la disponibilidad de YouTube durante la sesión.
2. Generar con la plataforma el resumen, las ideas clave y un cuestionario a partir del video. El docente asesor revisa y edita todas las preguntas con el editor de la plataforma y descarta las ambiguas o incorrectas.
3. Construir tres juegos de 12 ítems cada uno (por ejemplo, 8 de opción múltiple y 4 de verdadero/falso), de dificultad comparable y cubriendo los mismos objetivos del video: **Forma A** (pre-test e inmediato), **Forma B** (diferido, ítems distintos a los de la Forma A) y el **cuestionario de estudio** (el generado y revisado, que usa el grupo experimental durante la actividad). Usar la función de duplicado de cuestionario para crear las copias en modo control.
4. Crear en la plataforma las cuentas de los participantes con un código anónimo (P01, P02, …). La tabla de correspondencia entre código y persona se guarda aparte, en un archivo protegido que solo conoce el investigador.
5. Imprimir el formato de consentimiento informado (Anexo B, documento independiente) en dos copias por participante y el cuestionario SUS (Anexo C) para quien lo prefiera en papel.
6. Configurar en la plataforma el repaso diferido (días 1, 3, 7 y 14) y confirmar que el repaso principal queda programado al día 7. Probar que los equipos tengan conexión estable y navegador actualizado.
7. Realizar una prueba piloto con 2 o 3 personas ajenas a la muestra para estimar tiempos y detectar errores en las preguntas. Ajustar el material y descartar a esas personas del análisis.

## A.4 Sesión con participantes (día 0)

**Desarrollo de la sesión (duración total aproximada: 90 minutos)**

| Minutos | Actividad | Grupo experimental | Grupo control |
|---|---|---|---|
| 0–10 | Bienvenida, explicación del estudio, lectura y firma del consentimiento informado; resolver dudas | Igual | Igual |
| 10–20 | Pre-test: Forma A en modo control (sin retroalimentación) | Igual | Igual |
| 20–35 | Visualización del video (una sola vez, sin pausas para consulta externa) | Igual | Igual |
| 35–60 | Fase de estudio (25 min) | Lee el resumen y las ideas clave; responde el cuestionario de estudio con retroalimentación y marcas de tiempo; puede repetirlo | Estudia con el video y sus apuntes; responde el cuestionario en modo control, sin resumen ni retroalimentación |
| 60–70 | Post-test inmediato: Forma A en modo control (genera el «puntaje inicial») | Igual | Igual |
| 70–80 | Escala SUS (Anexo C) y comentarios libres | Responde | No aplica (no usó todas las funciones) |
| 80–90 | Cierre: agradecimiento, recordatorio del repaso diferido y del canal de contacto | Igual | Igual |

Durante la sesión el investigador **no explica contenidos del video** ni responde preguntas sobre las respuestas correctas. Registra incidentes (fallos de conexión, interrupciones, preguntas de los participantes) en la hoja de observación con la hora de ocurrencia. El tiempo de cada fase se registra automáticamente por la plataforma y se verifica con un cronómetro del investigador.

## A.5 Medición diferida (retención)

1. La plataforma notifica el repaso programado. El día 7 después de la sesión (repaso principal) cada participante responde la **Forma B** en modo control, sin consultar material.
2. Los repasos de los días 1, 3 y 14 son opcionales y se analizan de forma exploratoria; su aplicación depende de la disponibilidad de los participantes.
3. Si un participante no completa la medición diferida, se conserva en los análisis de pre-test y post-test inmediato y se excluye únicamente del análisis de retención. Registrar el número de pérdidas por grupo.

## A.6 Medición del tiempo del docente (eficiencia)

1. Participan al menos 3 docentes o monitores con experiencia en la elaboración de evaluaciones (si no es posible, se reportará como estudio de caso).
2. Antes de usar la herramienta, cada docente estima por escrito cuántos minutos le tomaría elaborar, de forma manual, un cuestionario de 10 preguntas con respuestas y justificaciones a partir del mismo video (estimación manual, *T*manual). Opcional y más robusto: cronometrar la elaboración manual real de un cuestionario.
3. El docente genera el cuestionario con la plataforma, lo revisa y lo edita hasta dejarlo listo para aplicar. La plataforma registra el tiempo con la herramienta (*T*herramienta), que incluye generación, revisión y edición.
4. Se calcula el porcentaje de ahorro: ahorro (%) = (*T*manual − *T*herramienta) / *T*manual × 100. Se reporta la media, la desviación estándar y el rango. La hipótesis de ahorro de 40 % se evalúa contra estos datos; no se asume.

## A.7 Registro y custodia de los datos

- Exportar los resultados de cada cuestionario en CSV desde la plataforma y guardarlos en una carpeta cifrada o protegida con contraseña, nombrados con la fecha y la forma del cuestionario.
- Consolidar en una hoja de cálculo una fila por participante con: código, grupo, pre-test, post-test inmediato, post-test diferido, tiempo por fase, SUS (solo experimental) y observaciones.
- Verificar que los datos exportados no incluyan nombres ni correos antes de compartirlos con el docente asesor.
- Conservar los datos únicamente durante el período indicado en el consentimiento informado y eliminarlos al vencer el plazo: [completar el plazo de conservación].

## A.8 Manejo de incidentes

**Incidentes frecuentes y acción prevista**

| Incidente | Acción |
|---|---|
| El video de YouTube no carga o la plataforma lo rechaza (bloqueo por exceso de solicitudes) | Usar el archivo MP4 local previsto; si falta, reprogramar la sesión. No improvisar otro video: rompe la equivalencia entre grupos. |
| Se agotó la cuota gratuita de los proveedores de IA | Se generaron y revisaron los cuestionarios con antelación (A.3); la sesión no depende de la generación en vivo. |
| Falla de internet durante el post-test | Reiniciar el intento si no se había finalizado; registrar el incidente y la hora en la hoja de observación. |
| El participante desea retirarse | Se respeta de inmediato; sus datos se eliminan y no se incluyen en el análisis (A.9). |
| Un participante conoce previamente el video | Registrar la condición y analizar con y sin su dato (análisis de sensibilidad). |

## A.9 Retiro del participante y eliminación de datos

Cada participante puede retirarse en cualquier momento sin consecuencia académica. Mediante la función «Eliminar cuenta» de la plataforma o por solicitud al investigador, se eliminan su cuenta y sus datos asociados. Quien lo solicite puede además descargar sus datos con la función «Descargar mis datos». Los datos ya anonimizados y agregados que formen parte de un análisis finalizado no pueden desagregarse; esta condición se informa en el consentimiento.

## A.10 Lista de verificación final

- Consentimiento firmado por todos los participantes y archivado.
- Formas A y B revisadas por el docente asesor; cuestionario de estudio listo.
- Cuentas con códigos anónimos creadas; tabla de correspondencia protegida.
- Video MP4 local probado; equipos y conexión verificados.
- Repasos diferidos programados (día 7 como principal).
- Hoja de observación y SUS impresos.
- Plan de análisis (sección 7.6) definido antes de ver los datos.
