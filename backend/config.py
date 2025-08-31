"""
Конфигурация приложения с валидацией через Pydantic
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional, Dict, Any
from pathlib import Path

class Settings(BaseSettings):
    """Настройки приложения с валидацией"""
    
    # Database
    database_url: str = Field(..., description="URL подключения к базе данных")
    
    # JWT
    secret_key: str = Field(..., min_length=32, description="Секретный ключ для JWT")
    algorithm: str = Field(default="HS256", description="Алгоритм JWT")
    access_token_expire_minutes: int = Field(default=20160, description="Время жизни токена в минутах")
    
    # Environment
    environment: str = Field(default="development", description="Окружение")
    debug: bool = Field(default=False, description="Режим отладки")
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
    log_rotation: str = Field(default="10 MB", description="Ротация логов")
    log_retention: str = Field(default="30 days", description="Хранение логов")
    
    # Redis (optional)
    redis_url: Optional[str] = Field(default=None, description="Redis URL для кеширования")
    redis_password: Optional[str] = Field(default=None, description="Redis пароль")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN для мониторинга")
    sentry_environment: str = Field(default="development", description="Sentry окружение")
    
    # Security
    allowed_hosts: List[str] = Field(default=["*"], description="Разрешенные хосты")
    trusted_proxies: List[str] = Field(default=["127.0.0.1", "::1"], description="Доверенные прокси")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Включить ограничение запросов")
    rate_limit_requests: int = Field(default=100, description="Количество запросов")
    rate_limit_window: int = Field(default=3600, description="Окно ограничения в секундах")
    
    # Worker
    worker_enabled: bool = Field(default=True, description="Включить воркер")
    worker_max_concurrent: int = Field(default=5, description="Максимум одновременных задач")
    
    @validator('cors_origins')
    def parse_cors_origins(cls, v):
        """Парсинг CORS origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('allowed_hosts')
    def parse_allowed_hosts(cls, v):
        """Парсинг allowed hosts"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    @validator('trusted_proxies')
    def parse_trusted_proxies(cls, v):
        """Парсинг trusted proxies"""
        if isinstance(v, str):
            return [proxy.strip() for proxy in v.split(',')]
        return v
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Валидация секретного ключа"""
        if len(v) < 32:
            raise ValueError('SECRET_KEY должен быть минимум 32 символа')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """Валидация URL базы данных"""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('DATABASE_URL должен начинаться с postgresql:// или postgresql+asyncpg://')
        return v
    
    @property
    def is_production(self) -> bool:
        """Проверка на продакшн окружение"""
        return self.environment.lower() == 'production'
    
    @property
    def log_dir(self) -> Path:
        """Директория для логов"""
        log_path = Path(self.log_file).parent
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Получение конфигурации для конкретного LLM провайдера"""
        configs = {
            'openai': {
                'api_key': self.openai_api_key,
                'api_url': getattr(self, 'openai_api_url', 'https://api.openai.com/v1/chat/completions'),
                'model': self.openai_model,
                'max_tokens': self.openai_max_tokens
            },
            'gemini': {
                'api_key': self.gemini_api_key,
                'api_url': self.gemini_api_url,
                'model': getattr(self, 'gemini_model', 'gemini-pro')
            },
            'anthropic': {
                'api_key': self.anthropic_api_key,
                'api_url': getattr(self, 'anthropic_api_url', 'https://api.anthropic.com/v1/messages'),
                'model': self.anthropic_model
            },
            'grok': {
                'api_key': self.grok_api_key,
                'api_url': self.grok_api_url,
                'model': getattr(self, 'grok_model', 'grok-beta')
            },
            'mistral': {
                'api_key': self.mistral_api_key,
                'api_url': self.mistral_api_url,
                'model': getattr(self, 'mistral_model', 'mistral-large-latest')
            },
            'perplexity': {
                'api_key': self.perplexity_api_key,
                'api_url': self.perplexity_api_url,
                'model': getattr(self, 'perplexity_model', 'llama-3.1-sonar-small-128k-online')
            }
        }
        return configs.get(provider.lower(), {})
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Глобальный экземпляр настроек
settings = Settings()

# Создаем директорию для логов
settings.log_dir
