import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Word, LLM, WordSerp, Company, BrandProject, BrandMention, Competitor
from database import get_async_session
from llm_service import llm_service
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMWorker:
    """Воркер для автоматического обновления SERP данных"""
    
    def __init__(self):
        self.llm_providers = {
            "openai": llm_service.get_serp_from_openai,
            "grok": llm_service.get_serp_from_grok,
            "gemini": llm_service.get_serp_from_gemini
        }
    
    async def process_word_with_llm(self, word: Word, llm: LLM, db: AsyncSession) -> bool:
        """Обработка одного слова с одним LLM провайдером"""
        try:
            # Проверяем, был ли уже запрос за последние 2 недели
            two_weeks_ago = datetime.utcnow() - timedelta(days=14)
            
            existing_serp = await db.scalar(
                select(WordSerp).where(
                    WordSerp.word_id == word.uuid,
                    WordSerp.llm_id == llm.uuid,
                    WordSerp.create_time > two_weeks_ago
                )
            )
            
            if existing_serp:
                logger.info(f"SERP для слова '{word.name}' и LLM '{llm.name}' уже обновлен")
                return False
            
            # Получаем SERP данные от LLM
            llm_function = self.llm_providers.get(llm.name.lower())
            if not llm_function:
                logger.warning(f"Неизвестный LLM провайдер: {llm.name}")
                return False
            
            logger.info(f"Получаем SERP для '{word.name}' от {llm.name}")
            serp_content = await llm_function(word.name)
            
            # Сохраняем результат SERP
            word_serp = WordSerp(
                content=serp_content,
                llm_id=llm.uuid,
                word_id=word.uuid,
                create_time=datetime.utcnow()
            )
            
            db.add(word_serp)
            await db.flush()  # Получаем ID для связи с компаниями
            
            # Извлекаем компании из SERP
            companies = await llm_service.extract_companies_from_serp_simple(serp_content)
            
            # Сохраняем компании
            for company_name in companies:
                company = Company(
                    name=company_name,
                    serp_id=word_serp.uuid
                )
                db.add(company)
            
            await db.commit()
            logger.info(f"Извлечено {len(companies)} компаний из SERP для слова '{word.name}'")
            
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка обработки слова '{word.name}' с LLM '{llm.name}': {e}")
            return False

    async def analyze_brand_mentions_for_serp(self, serp: WordSerp, db: AsyncSession) -> bool:
        """Анализ упоминаний брендов в SERP результате"""
        try:
            # Получаем все brand проекты, которые могут быть связаны с этим словом
            # Находим проекты через группу слов
            word = await db.scalar(select(Word).where(Word.uuid == serp.word_id))
            if not word or not word.group_id:
                return False
            
            # Ищем brand проект для этой группы
            brand_project = await db.scalar(
                select(BrandProject).where(BrandProject.word_group_id == word.group_id)
            )
            
            if not brand_project:
                return False  # Это не brand проект
            
            # Получаем конкурентов проекта
            competitors = await db.execute(
                select(Competitor).where(Competitor.project_id == brand_project.uuid)
            )
            competitor_names = [comp.name for comp in competitors.scalars().all()]
            
            # Анализируем упоминания через LLM
            analysis_result = await llm_service.analyze_brand_mentions(
                serp.content,
                brand_project.brand_name,
                competitor_names
            )
            
            # Сохраняем результат анализа
            brand_mention = BrandMention(
                serp_id=serp.uuid,
                project_id=brand_project.uuid,
                brand_mentioned=1 if analysis_result.get("brand_mentioned", False) else 0,
                competitor_mentioned=1 if analysis_result.get("competitor_mentioned", False) else 0,
                mentioned_competitor=analysis_result.get("mentioned_competitor"),
                brand_position=analysis_result.get("brand_position"),
                competitor_position=analysis_result.get("competitor_position"),
                analysis_confidence=analysis_result.get("confidence", 100)
            )
            
            db.add(brand_mention)
            await db.commit()
            
            logger.info(f"Анализ упоминаний завершен для SERP {serp.uuid}: brand={analysis_result.get('brand_mentioned')}, competitor={analysis_result.get('competitor_mentioned')}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка анализа упоминаний для SERP {serp.uuid}: {e}")
            return False

    async def run_worker_cycle(self):
        """Основной цикл воркера"""
        logger.info("🚀 Запуск цикла обновления SERP данных")
        
        async with get_async_session() as db:
            try:
                # Получаем все активные слова
                words_result = await db.execute(
                    select(Word).where(Word.status == 1)
                )
                words = list(words_result.scalars().all())
                
                # Получаем все активные LLM провайдеры
                llms_result = await db.execute(
                    select(LLM).where(LLM.is_active == 1)
                )
                llms = list(llms_result.scalars().all())
                
                logger.info(f"Найдено {len(words)} слов и {len(llms)} LLM провайдеров")
                
                processed_count = 0
                for word in words:
                    for llm in llms:
                        success = await self.process_word_with_llm(word, llm, db)
                        if success:
                            processed_count += 1
                            
                            # После успешной обработки SERP, анализируем упоминания брендов
                            # Получаем последний созданный SERP для этого слова и LLM
                            latest_serp = await db.scalar(
                                select(WordSerp)
                                .where(WordSerp.word_id == word.uuid)
                                .where(WordSerp.llm_id == llm.uuid)
                                .order_by(WordSerp.create_time.desc())
                                .limit(1)
                            )
                            
                            if latest_serp:
                                await self.analyze_brand_mentions_for_serp(latest_serp, db)
                
                logger.info(f"✅ Цикл завершен. Обработано {processed_count} комбинаций слово-LLM")
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле воркера: {e}")

    async def run_continuous(self, interval_hours: int = 24 * 14):  # 2 недели по умолчанию
        """Непрерывная работа воркера с заданным интервалом"""
        logger.info(f"Запуск непрерывного воркера с интервалом {interval_hours} часов")
        
        while True:
            try:
                await self.run_worker_cycle()
                
                # Ждем до следующего цикла
                wait_seconds = interval_hours * 3600
                logger.info(f"Ожидание {interval_hours} часов до следующего цикла")
                await asyncio.sleep(wait_seconds)
                
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки воркера")
                break
            except Exception as e:
                logger.error(f"Критическая ошибка воркера: {str(e)}")
                # Ждем 1 час перед повторной попыткой
                await asyncio.sleep(3600)

# Глобальный экземпляр воркера
llm_worker = LLMWorker()

# Функция для запуска воркера
async def start_worker():
    """Запуск воркера"""
    await llm_worker.run_continuous()

if __name__ == "__main__":
    # Запуск воркера напрямую
    asyncio.run(start_worker())
