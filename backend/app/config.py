from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    groq_api_key: str = ""
    groq_llm_model: str = "openai/gpt-oss-120b"
    groq_whisper_model: str = "whisper-large-v3-turbo"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    proveedores_ia: str = "gemini,groq,ollama"
    ffmpeg_path: str = ""
    frontend_url: str = "http://localhost:3000"

    database_url: str = "sqlite:///./datos.db"
    secret_key: str = ""
    token_expira_horas: int = 72
    limite_diario_procesamientos: int = 20
    max_subida_mb: int = 200
    # Idioma del audio para Whisper (p. ej. "es", "en"). Vacío = detección automática.
    idioma_transcripcion: str = ""
    # Ruta a cookies.txt de YouTube (formato Netscape) para evitar bloqueos "not a bot" / 429.
    youtube_cookies: str = ""
    # Duración máxima (minutos) de los videos de YouTube/Vimeo que se transcriben con audio + Whisper.
    max_duracion_min: int = 180

    @property
    def origenes_cors(self) -> list[str]:
        """FRONTEND_URL admite varios orígenes separados por comas (sin barra final)."""
        origenes = [o.strip().rstrip("/") for o in self.frontend_url.split(",") if o.strip()]
        if "http://localhost:3000" in origenes:
            origenes.append("http://127.0.0.1:3000")
        return origenes

    @property
    def lista_proveedores(self) -> list[str]:
        return [p.strip().lower() for p in self.proveedores_ia.split(",") if p.strip()]


settings = Settings()
