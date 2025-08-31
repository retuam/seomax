"""
Упрощенная конфигурация приложения
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional, Dict, Any
from pathlib import Path

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    environment: str = Field(default="development", description="Окружение")
    debug: bool = Field(default=True, description="Режим отладки")
    secret_key: str = Field(description="Секретный ключ для JWT")
    algorithm: str = Field(default="HS256", description="Алгоритм JWT")
    access_token_expire_minutes: int = Field(default=30, description="Время жизни токена в минутах")
    
    # База данных
    database_url: str = Field(description="URL базы данных")
    
    # CORS
    cors_origins: str = Field(default="http://localhost:3000", description="CORS origins")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API ключ")
    openai_api_url: str = Field(default="https://api.openai.com/v1/chat/completions", description="OpenAI API URL")
    openai_model: str = Field(default="gpt-4o-mini", description="Модель OpenAI")
    openai_max_tokens: int = Field(default=1000, description="Максимальное количество токенов")
    
    # Gemini
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API ключ")
    gemini_api_url: str = Field(default="https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent", description="Gemini API URL")
    gemini_model: str = Field(default="gemini-pro", description="Модель Gemini")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API ключ")
    anthropic_api_url: str = Field(default="https://api.anthropic.com/v1/messages", description="Anthropic API URL")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", description="Модель Anthropic")
    
    # Grok
    grok_api_key: Optional[str] = Field(default=None, description="Grok API ключ")
    grok_api_url: str = Field(default="https://api.x.ai/v1/chat/completions", description="Grok API URL")
    grok_model: str = Field(default="grok-beta", description="Модель Grok")
    
    # Mistral
    mistral_api_key: Optional[str] = Field(default=None, description="Mistral API ключ")
    mistral_api_url: str = Field(default="https://api.mistral.ai/v1/chat/completions", description="Mistral API URL")
    mistral_model: str = Field(default="mistral-large-latest", description="Модель Mistral")
    
    # Perplexity
    perplexity_api_key: Optional[str] = Field(default=None, description="Perplexity API ключ")
    perplexity_api_url: str = Field(default="https://api.perplexity.ai/chat/completions", description="Perplexity API URL")
    perplexity_model: str = Field(default="llama-3.1-sonar-small-128k-online", description="Модель Perplexity")
    
    # Worker
    worker_interval_hours: int = Field(default=336, description="Интервал воркера в часах (14 дней)")
    worker_batch_size: int = Field(default=10, description="Размер batch для воркера")
    worker_delay_seconds: int = Field(default=2, description="Задержка между запросами в секундах")
    
    # Logging
    log_level: str = Field(default="INFO", description="Уровень логирования")
    log_file: str = Field(default="logs/app.log", description="Файл логов")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN для мониторинга")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Получение списка CORS origins"""
        return [origin.strip() for origin in self.cors_origins.split(',')]
    
    @property
    def allowed_hosts(self) -> List[str]:
        """Разрешенные хосты"""
        return ["*"]
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Получение конфигурации для конкретного LLM провайдера"""
        configs = {
            'openai': {
                'api_key': self.openai_api_key,
                'api_url': self.openai_api_url,
                'model': self.openai_model,
                'max_tokens': self.openai_max_tokens
            },
            'gemini': {
                'api_key': self.gemini_api_key,
                'api_url': self.gemini_api_url,
                'model': self.gemini_model
            },
            'anthropic': {
                'api_key': self.anthropic_api_key,
                'api_url': self.anthropic_api_url,
                'model': self.anthropic_model
            },
            'grok': {
                'api_key': self.grok_api_key,
                'api_url': self.grok_api_url,
                'model': self.grok_model
            },
            'mistral': {
                'api_key': self.mistral_api_key,
                'api_url': self.mistral_api_url,
                'model': self.mistral_model
            },
            'perplexity': {
                'api_key': self.perplexity_api_key,
                'api_url': self.perplexity_api_url,
                'model': self.perplexity_model
            }
        }
        return configs.get(provider.lower(), {})
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Создаем глобальный экземпляр настроек
settings = Settings()
