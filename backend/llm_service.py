import httpx
import aiohttp
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from loguru import logger
from config import settings
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

class LLMService:
    """Современный сервис для работы с различными LLM провайдерами"""
    
    def __init__(self):
        self.session_timeout = aiohttp.ClientTimeout(total=60)
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Инициализируем конфигурации провайдеров
        self.providers_config = {
            provider.value: settings.get_llm_config(provider.value)
            for provider in LLMProvider
        }
    
    async def get_serp_from_openai(self, word: str) -> str:
        """Получение SERP данных от OpenAI"""
        prompt = f"""
        Представь, что ты поисковая система. Для запроса "{word}" выдай топ-10 результатов поиска в формате:
        1. Заголовок - краткое описание
        2. Заголовок - краткое описание
        ...
        
        Включи реальные компании, бренды и коммерческие предложения, связанные с этим запросом.
        """
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                return f"Ошибка получения данных от OpenAI: {str(e)}"
    
    async def get_serp_from_grok(self, word: str) -> str:
        """Получение SERP данных от Grok (заглушка)"""
        # Пока что мок-данные, так как нужен реальный API ключ
        return f"""
        Результаты поиска для "{word}" от Grok:
        1. Компания А - лидер в области {word}
        2. Бренд Б - качественные решения для {word}
        3. Сервис В - онлайн платформа для {word}
        4. Магазин Г - широкий выбор {word}
        5. Производитель Д - инновационные {word}
        """
    
    async def get_serp_from_gemini(self, word: str) -> str:
        """Получение SERP данных от Gemini"""
        if not self.gemini_api_key:
            return f"Мок результаты для {word} от Gemini: Компания X, Бренд Y, Сервис Z"
        
        prompt = f"""
        Создай список топ-10 поисковых результатов для запроса "{word}".
        Включи реальные компании и бренды.
        """
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.gemini_api_url}?key={self.gemini_api_key}",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                return f"Ошибка получения данных от Gemini: {str(e)}"
    
    async def extract_companies_from_text(self, text: str) -> List[str]:
        """Извлечение компаний из текста с помощью OpenAI"""
        if not self.openai_api_key:
            # Простое извлечение по ключевым словам как fallback
            companies = []
            keywords = ["компания", "бренд", "сервис", "магазин", "производитель", "платформа"]
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
        
        prompt = f"""
        В этом тексте найди все упоминания компаний, товаров, брендов и коммерческих слов.
        Дай только список названий через запятую, без лишнего текста и объяснений.
        
        Текст:
        {text}
        """
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                companies_text = result["choices"][0]["message"]["content"]
                
                # Парсим список компаний
                companies = [company.strip() for company in companies_text.split(',')]
                return [c for c in companies if c and len(c) > 2][:10]  # Фильтруем и ограничиваем
                
            except Exception as e:
                print(f"Ошибка извлечения компаний: {str(e)}")
                return []

    async def extract_companies_from_serp(self, serp_content: str) -> List[str]:
        """Извлечение компаний из SERP результатов"""
        prompt = f"""
        Из следующего списка результатов поиска извлеки названия компаний, брендов, магазинов.
        Верни только названия через запятую, без номеров и описаний.
        
        Результаты поиска:
        {serp_content}
        
        Компании:
        """
        
        try:
            response = await self._make_openai_request(prompt)
            companies = [company.strip() for company in response.split(',') if company.strip()]
            return companies[:10]  # Максимум 10 компаний
        except Exception as e:
            logger.error(f"Ошибка извлечения компаний: {e}")
            return []

    async def generate_keywords_for_brand(self, brand_name: str, brand_description: str, keywords_count: int = 50) -> List[str]:
        """Генерация ключевых слов для бренда на основе его описания"""
        prompt = f"""
        Ты SEO эксперт. На основе названия компании и её описания создай список из {keywords_count} ключевых запросов, 
        по которым пользователи могут искать информацию в этой тематике.
        
        Название компании: {brand_name}
        Описание: {brand_description}
        
        Требования:
        1. Запросы должны быть релевантными тематике компании
        2. Включи как коммерческие, так и информационные запросы
        3. Используй разные формулировки и синонимы
        4. Запросы на русском языке
        5. Каждый запрос с новой строки, без номеров
        
        Ключевые запросы:
        """
        
        try:
            response = await self._make_openai_request(prompt)
            keywords = [kw.strip() for kw in response.split('\n') if kw.strip() and not kw.strip().isdigit()]
            # Убираем пустые строки и номера
            keywords = [kw for kw in keywords if len(kw) > 3]
            return keywords[:keywords_count]
        except Exception as e:
            logger.error(f"Ошибка генерации ключевых слов: {e}")
            return []

    async def analyze_brand_mentions(self, serp_content: str, brand_name: str, competitors: List[str]) -> dict:
        """Анализ упоминаний бренда и конкурентов в SERP результатах"""
        competitors_str = ", ".join(competitors)
        
        prompt = f"""
        Проанализируй следующие результаты поиска и определи:
        1. Упоминается ли бренд "{brand_name}" в результатах (да/нет)
        2. Упоминается ли какой-либо из конкурентов: {competitors_str} (да/нет)
        3. Если упоминается конкурент, укажи его название
        4. На какой позиции (1-10) упоминается наш бренд (если упоминается)
        5. На какой позиции (1-10) упоминается конкурент (если упоминается)
        
        Результаты поиска:
        {serp_content}
        
        Ответь СТРОГО в формате JSON:
        {{
            "brand_mentioned": true/false,
            "competitor_mentioned": true/false,
            "mentioned_competitor": "название конкурента или null",
            "brand_position": число от 1 до 10 или null,
            "competitor_position": число от 1 до 10 или null,
            "confidence": число от 0 до 100
        }}
        """
        
        try:
            response = await self._make_openai_request(prompt)
            # Парсим JSON ответ
            import json
            result = json.loads(response.strip())
            return result
        except Exception as e:
            logger.error(f"Ошибка анализа упоминаний: {e}")
            return {
                "brand_mentioned": False,
                "competitor_mentioned": False,
                "mentioned_competitor": None,
                "brand_position": None,
                "competitor_position": None,
                "confidence": 0
            }

# Глобальный экземпляр сервиса
llm_service = LLMService()
