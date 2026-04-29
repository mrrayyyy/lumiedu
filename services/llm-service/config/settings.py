import os


class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "").strip()
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_timeout: float = float(os.getenv("OLLAMA_TIMEOUT", "30"))
    max_history_turns: int = int(os.getenv("MAX_HISTORY_TURNS", "10"))
    max_response_tokens: int = int(os.getenv("MAX_RESPONSE_TOKENS", "256"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))


settings = Settings()
