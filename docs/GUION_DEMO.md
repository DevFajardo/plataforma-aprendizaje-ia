# Guion de la demostración ante el jurado (8 minutos)

## Preparación (el día anterior y 30 minutos antes)
- [ ] `backend\.venv\Scripts\python.exe backend\scripts\sembrar_demo.py` (datos de demostración cargados).
- [ ] Ejecutar `iniciar_demo.ps1` y comprobar desde un celular que abre la URL mostrada (misma red Wi-Fi; firewall abierto para los puertos 3000 y 8000).
- [ ] Proyector con la app abierta: pestaña 1 con `docente@demo.com`, pestaña 2 con `coordinador@demo.com` (clave `Demo12345`).
- [ ] Un video corto (2–4 min) descargado como MP4 por si YouTube bloquea la conexión.
- [ ] Cookies de YouTube configuradas (`backend/cookies_youtube.txt`) si se va a usar un enlace.

## Desarrollo
| Tiempo | Paso | Qué mostrar | Qué decir |
|---|---|---|---|
| 0:00–1:30 | Generar | Pegar el enlace o subir el MP4; mostrar resumen, preguntas con nivel Bloom y sello «Verificada en el video» | «La IA transcribe, resume, genera preguntas y verifica cada una contra el video» |
| 1:30–2:30 | Tutor IA | Preguntar algo del video y pulsar la cita | «Responde solo con lo que dice el video y cita el minuto exacto» |
| 2:30–5:30 | Clase en vivo | «Iniciar clase en vivo», mostrar el QR, el jurado se une, jugar 2–3 preguntas, resultados y podio | «Sin crear cuenta, desde el celular, con resultados en tiempo real» |
| 5:30–6:30 | Docente | Resultados de un cuestionario demo: análisis de ítems y temas a reforzar | «El docente sabe qué pregunta confunde y qué tema reforzar» |
| 6:30–8:00 | Coordinación | Semáforo por resultado de aprendizaje, alertas con motivo y descarga del PDF | «Evidencia para registro calificado y acreditación, y alertas para acompañar a tiempo» |

## Plan B
- YouTube bloquea → pestaña «Subir archivo» con el MP4.
- La IA no responde → usar los cuestionarios de los datos de demostración (ya generados).
- La red Wi-Fi falla → compartir datos desde el celular y volver a ejecutar `iniciar_demo.ps1`.

## Preguntas probables del jurado
- **¿Y si la IA se equivoca?** Verificación automática de cada pregunta, revisión y edición del docente, y respaldo entre proveedores.
- **¿Cuánto cuesta?** $0 con planes gratuitos; a escala institucional, el costo por uso de las API es bajo.
- **¿Datos personales?** Ley 1581 de 2012: consentimiento, descarga y eliminación de los datos.
- **¿Derechos de autor de los videos?** Se recomienda contenido propio o con licencia; la subida de archivos lo permite.
