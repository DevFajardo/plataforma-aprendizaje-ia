# Scripts para regrabar el video de demostración

Graban cada escena con Playwright (video 1920x1080, cursor visible y subtítulos inyectados) y las une con FFmpeg.
No contienen secretos: solo usan las cuentas de demostración (`*@demo.com`, clave `Demo12345`) de los datos sembrados.

## Requisitos
- Node.js 20+, FFmpeg en el PATH (o variable `FFMPEG` / `FFPROBE`).
- `npm install` dentro de esta carpeta (instala Playwright) y `npx playwright install chromium`.
- Backend y frontend corriendo con datos de demostración (`backend/scripts/sembrar_demo.py`).
  **Usa una copia de la base de datos** para no ensuciar la tuya:
  ```powershell
  copy backend\datos.db $env:TEMP\video.db
  cd backend
  $env:DATABASE_URL="sqlite:///C:/Users/<tu_usuario>/AppData/Local/Temp/video.db"
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
  ```
  Frontend en producción (sin el indicador de desarrollo de Next): `npm run build` y `npx next start -p 3000` en `frontend/`.

## Uso
```powershell
cd docs\video\scripts
$env:VIDEO_OUT = "$env:TEMP\video_out"      # carpeta de trabajo (clips temporales)
node grabar.js                              # graba todas las escenas
node grabar.js quiz tutor                   # o solo algunas
node componer.js ..\demo_plataforma.mp4     # recorta, acelera esperas y une con fundidos
```
Escenas: `titulo, landing, login_docente, generar, quiz, tutor, publicar, estudiante, resultados, vivo, coordinador, movil, cierre`.
Grábalas en ese orden (el estudiante debe responder antes de ver «Resultados»).

Variables opcionales: `BASE_URL`, `API_URL`, `QUIZ_ID` (cuestionario sembrado, por defecto 2) y `CODIGO` (su código de acceso).
Si el tutor de IA tarda (los proveedores externos a veces responden en más de un minuto), el script marca ese tramo y
`componer.js` lo acelera. La generación real desde YouTube no se graba (depende de la red y de la IA): se muestra el formulario y luego un cuestionario ya generado.
