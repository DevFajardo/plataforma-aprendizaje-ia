# Backend (FastAPI)

```powershell
cd backend
# edita .env (GEMINI_API_KEY, GROQ_API_KEY, SECRET_KEY)
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

- Documentación interactiva: http://localhost:8000/docs
- Pruebas: `.\.venv\Scripts\python.exe -m pytest -q` (requiere `requirements-dev.txt`)
- Cuentas demo: `.\.venv\Scripts\python.exe scripts\crear_demo.py`
- Estructura académica de ejemplo + coordinador/admin demo: `.\.venv\Scripts\python.exe scripts\sembrar_estructura.py`

Documentación completa en el [README principal](../README.md) y en [`docs/`](../docs/).
