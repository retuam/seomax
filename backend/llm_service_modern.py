"""
Современный сервис для работы с LLM провайдерами
Поддерживает все популярные LLM API с retry логикой, кешированием и мониторингом
"""
import aiohttp
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import hashlib
from loguru import logger
from config_simple import settings
from logging_config import log_execution

class LLMProvider(Enum):
    """Перечисление поддерживаемых LLM провайдеров"""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    GROK = "grok"
    MISTRAL = "mistral"
    PERPLEXITY = "perplexity"

@dataclass
class LLMResponse:
    """Структура ответа от LLM"""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    cached: bool = False

@dataclass
class LLMRequest:
    """Структура запроса к LLM"""
    prompt: str
    provider: LLMProvider
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    system_prompt: Optional[str] = None

class BaseLLMProvider(ABC):
    """Базовый класс для LLM провайдеров"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.api_url = config.get('api_url')
        self.model = config.get('model')
        
        if not self.api_key:
            raise ValueError(f"API key is required for {self.__class__.__name__}")
    
    @abstractmethod
    async def make_request(self, request: LLMRequest) -> LLMResponse:
        """Выполнение запроса к LLM API"""
        pass

class OpenAIProvider(BaseLLMProvider):
    """Провайдер для OpenAI GPT"""
    
    async def make_request(self, request: LLMRequest) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        data = {
            "model": request.model or self.model or "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": request.max_tokens or 1000,
            "temperature": request.temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return LLMResponse(
                        content=result["choices"][0]["message"]["content"],
                        provider="openai",
                        model=data["model"],
                        tokens_used=result.get("usage", {}).get("total_tokens")
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")

class GeminiProvider(BaseLLMProvider):
    """Провайдер для Google Gemini"""
    
    async def make_request(self, request: LLMRequest) -> LLMResponse:
        url = f"{self.api_url}?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Формируем промпт для Gemini
        full_prompt = request.prompt
        if request.system_prompt:
            full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
        
        data = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens or 1000
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return LLMResponse(
                        content=content,
                        provider="gemini",
                        model="gemini-pro"
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error: {response.status} - {error_text}")

class AnthropicProvider(BaseLLMProvider):
    """Провайдер для Anthropic Claude"""
    
    async def make_request(self, request: LLMRequest) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": request.model or self.config.get('model', 'claude-3-sonnet-20240229'),
            "max_tokens": request.max_tokens or 1000,
            "temperature": request.temperature,
            "messages": [
                {"role": "user", "content": request.prompt}
            ]
        }
        
        if request.system_prompt:
            data["system"] = request.system_prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return LLMResponse(
                        content=result["content"][0]["text"],
                        provider="anthropic",
                        model=data["model"],
                        tokens_used=result.get("usage", {}).get("input_tokens", 0) + 
                                   result.get("usage", {}).get("output_tokens", 0)
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error: {response.status} - {error_text}")

class GenericProvider(BaseLLMProvider):
    """Универсальный провайдер для Grok, Mistral, Perplexity и других OpenAI-совместимых API"""
    
    async def make_request(self, request: LLMRequest) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        data = {
            "model": request.model or self.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1000,
            "temperature": request.temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return LLMResponse(
                        content=result["choices"][0]["message"]["content"],
                        provider=request.provider.value,
                        model=data["model"],
                        tokens_used=result.get("usage", {}).get("total_tokens")
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"{request.provider.value} API error: {response.status} - {error_text}")

class LLMService:
    """Современный сервис для работы с различными LLM провайдерами"""
    
    def __init__(self):
        self.providers = {}
        self.cache = {}  # Простой in-memory кеш
        self.cache_ttl = 3600  # 1 час
        self.session_timeout = aiohttp.ClientTimeout(total=60)
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Инициализируем провайдеров
        self._init_providers()
    
    def _init_providers(self):
        """Инициализация провайдеров"""
        configs = {
            LLMProvider.OPENAI: settings.get_llm_config('openai'),
            LLMProvider.GEMINI: settings.get_llm_config('gemini'),
            LLMProvider.ANTHROPIC: settings.get_llm_config('anthropic'),
            LLMProvider.GROK: settings.get_llm_config('grok'),
            LLMProvider.MISTRAL: settings.get_llm_config('mistral'),
            LLMProvider.PERPLEXITY: settings.get_llm_config('perplexity'),
        }
        
        # Создаем провайдеров только для тех, у кого есть API ключи
        for provider, config in configs.items():
            if config.get('api_key'):
                try:
                    if provider == LLMProvider.OPENAI:
                        self.providers[provider] = OpenAIProvider(config)
                    elif provider == LLMProvider.GEMINI:
                        self.providers[provider] = GeminiProvider(config)
                    elif provider == LLMProvider.ANTHROPIC:
                        self.providers[provider] = AnthropicProvider(config)
                    else:
                        # Используем универсальный провайдер для остальных
                        self.providers[provider] = GenericProvider(config)
                    
                    logger.info(f"✅ Initialized {provider.value} provider")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize {provider.value} provider: {e}")
            else:
                logger.warning(f"⚠️ {provider.value} provider not configured (missing API key)")
    
    def _get_cache_key(self, request: LLMRequest) -> str:
        """Генерация ключа кеша для запроса"""
        request_str = f"{request.provider.value}:{request.prompt}:{request.model}:{request.temperature}"
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """Получение ответа из кеша"""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                cached_response = LLMResponse(**cached_data)
                cached_response.cached = True
                return cached_response
            else:
                # Удаляем устаревший кеш
                del self.cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, response: LLMResponse):
        """Сохранение ответа в кеш"""
        # Не кешируем ошибки
        if not response.error:
            self.cache[cache_key] = (asdict(response), time.time())
    
    @log_execution("LLM Request")
    async def make_request_with_retry(self, request: LLMRequest) -> LLMResponse:
        """Выполнение запроса с retry логикой"""
        
        # Проверяем кеш
        cache_key = self._get_cache_key(request)
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            logger.debug(f"📦 Cache hit for {request.provider.value}")
            return cached_response
        
        # Проверяем доступность провайдера
        if request.provider not in self.providers:
            return LLMResponse(
                content="",
                provider=request.provider.value,
                model="unavailable",
                error=f"Provider {request.provider.value} not configured"
            )
        
        provider = self.providers[request.provider]
        
        # Выполняем запрос с retry
        last_error = None
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                response = await provider.make_request(request)
                response.response_time = time.time() - start_time
                
                # Сохраняем в кеш
                self._save_to_cache(cache_key, response)
                
                logger.debug(f"✅ {request.provider.value} request successful in {response.response_time:.2f}s")
                return response
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"⚠️ {request.provider.value} attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        # Все попытки неудачны
        logger.error(f"❌ {request.provider.value} failed after {self.max_retries} attempts")
        return LLMResponse(
            content="",
            provider=request.provider.value,
            model="error",
            error=last_error
        )
    
    async def get_serp_data(self, word: str, provider: LLMProvider) -> str:
        """Получение SERP данных от указанного провайдера"""
        system_prompt = """
Ты поисковая система. Для данного запроса выдай топ-10 результатов поиска в формате:
1. Заголовок - краткое описание
2. Заголовок - краткое описание
...

Включи реальные компании, бренды и коммерческие предложения, связанные с этим запросом.
Отвечай только списком результатов, без дополнительных комментариев.
"""
        
        request = LLMRequest(
            prompt=f"Поисковый запрос: {word}",
            provider=provider,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        response = await self.make_request_with_retry(request)
        return response.content if not response.error else f"Ошибка получения данных от {provider.value}: {response.error}"
    
    async def extract_companies_from_text(self, text: str) -> List[str]:
        """Извлечение компаний из текста с помощью наиболее доступного LLM"""
        
        # Выбираем первый доступный провайдер
        available_providers = [p for p in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.GEMINI] 
                             if p in self.providers]
        
        if not available_providers:
            logger.warning("⚠️ No LLM providers available for company extraction")
            return self._extract_companies_fallback(text)
        
        provider = available_providers[0]
        
        system_prompt = """
Из данного текста извлеки все упоминания компаний, товаров, брендов и коммерческих названий.
Верни только список названий через запятую, без лишнего текста и объяснений.
Если компаний не найдено, верни пустую строку.
"""
        
        request = LLMRequest(
            prompt=f"Текст для анализа:\n{text}",
            provider=provider,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=200
        )
        
        response = await self.make_request_with_retry(request)
        
        if response.error:
            logger.warning(f"⚠️ Company extraction failed, using fallback method")
            return self._extract_companies_fallback(text)
        
        # Парсим результат
        companies_text = response.content.strip()
        if not companies_text:
            return []
        
        companies = [company.strip() for company in companies_text.split(',')]
        return [c for c in companies if c and len(c) > 2][:10]  # Фильтруем и ограничиваем
    
    def _extract_companies_fallback(self, text: str) -> List[str]:
        """Fallback метод извлечения компаний по ключевым словам"""
        companies = []
        keywords = ["компания", "бренд", "сервис", "магазин", "производитель", "платформа", "корпорация"]
        lines = text.split('\n')
        
        for line in lines:
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    # Извлекаем название после ключевого слова
                    parts = line.split(' - ')
                    if len(parts) > 0:
                        company_name = parts[0].strip().split('. ')[-1]
                        if company_name and len(company_name) > 2:
                            companies.append(company_name)
        
        return list(set(companies))[:10]  # Убираем дубликаты и ограничиваем
    
    def get_available_providers(self) -> List[str]:
        """Получение списка доступных провайдеров"""
        return [provider.value for provider in self.providers.keys()]
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Получение статуса всех провайдеров"""
        status = {}
        for provider in LLMProvider:
            status[provider.value] = provider in self.providers
        return status

# Глобальный экземпляр сервиса
llm_service = LLMService()
