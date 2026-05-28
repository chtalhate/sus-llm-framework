from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env.example', extra='ignore')

    app_env: str = 'development'
    api_port: int = 8000
    ui_port: int = 8501
    api_base_url: str = 'http://api:8000'
    database_url: str = 'sqlite:///./data/processed/audit.db'
    ollama_base_url: str = 'http://ollama:11434'
    ollama_model: str = 'qwen2.5:7b-instruct'
    collection_name: str = 'sus_norms'
    use_qdrant: bool = False
    qdrant_url: str = 'http://qdrant:6333'
    top_k: int = 6
    rerank_k: int = 4
    max_context_chunks: int = 4
    llm_timeout_seconds: int = 120


settings = Settings()
