import requests
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select, create_engine
from models import Word, LLM, WordSerp, Company, BrandProject, BrandMention, Competitor
import logging
from config_simple import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMWorker:
    """Worker for brand monitoring in LLM responses"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 60
        # Create sync database engine and session
        self.engine = create_engine(settings.database_url.replace('+asyncpg', ''))
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_llm_response(self, word: str, llm_name: str) -> str:
        """Get LLM response for a keyword query"""
        try:
            if llm_name.lower() == "openai":
                return self.get_openai_response(word)
            else:
                logger.warning(f"LLM {llm_name} not implemented, skipping")
                return None
                
        except Exception as e:
            logger.error(f"Error getting LLM response for '{word}' from {llm_name}: {e}")
            return None
    
    def get_openai_response(self, word: str) -> str:
        """Get response from OpenAI for keyword"""
        try:
            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": word}],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            response = self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error querying OpenAI: {e}")
            return None
    
    def extract_companies_from_response(self, llm_response: str) -> list:
        """Extract company names from LLM response using OpenAI"""
        try:
            prompt = f"""
            Extract company names, brands, and organizations mentioned in the following text.
            Return only a JSON array of company names, nothing else.
            
            Text: {llm_response[:1500]}
            """
            
            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            response = self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                companies_text = result["choices"][0]["message"]["content"]
                try:
                    import json
                    companies = json.loads(companies_text)
                    return companies[:10] if isinstance(companies, list) else []
                except:
                    # Fallback: split by comma
                    companies = [c.strip() for c in companies_text.split(',') if c.strip()]
                    return companies[:10]
            else:
                logger.error(f"OpenAI API error for company extraction: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting companies: {e}")
            return []

    def analyze_brand_mentions_in_response(self, llm_response: str, brand_names: list, competitor_names: list) -> dict:
        """Analyze LLM response for brand mentions with positions"""
        if not llm_response:
            return {
                "brand_mentioned": False,
                "competitor_mentioned": False,
                "mentioned_brands": [],
                "mentioned_competitors": [],
                "brand_position": None,
                "competitor_position": None,
                "confidence": 0
            }
        
        response_lower = llm_response.lower()
        lines = llm_response.split('\n')
        
        # Check for brand mentions with positions
        mentioned_brands = []
        brand_position = None
        for brand in brand_names:
            if brand.lower() in response_lower:
                mentioned_brands.append(brand)
                # Find position in text (line number)
                for i, line in enumerate(lines, 1):
                    if brand.lower() in line.lower():
                        brand_position = i
                        break
        
        # Check for competitor mentions with positions
        mentioned_competitors = []
        competitor_position = None
        mentioned_competitor = None
        for competitor in competitor_names:
            if competitor.lower() in response_lower:
                mentioned_competitors.append(competitor)
                mentioned_competitor = competitor
                # Find position in text (line number)
                for i, line in enumerate(lines, 1):
                    if competitor.lower() in line.lower():
                        competitor_position = i
                        break
                break  # Only track first competitor found
        
        return {
            "brand_mentioned": len(mentioned_brands) > 0,
            "competitor_mentioned": len(mentioned_competitors) > 0,
            "mentioned_brands": mentioned_brands,
            "mentioned_competitors": mentioned_competitors,
            "mentioned_competitor": mentioned_competitor,
            "brand_position": brand_position,
            "competitor_position": competitor_position,
            "confidence": 95
        }

    
    def process_word_with_llm(self, word: Word, llm: LLM, db: Session) -> bool:
        """Process word with LLM and analyze brand mentions"""
        try:
            # Check if already processed in last 2 weeks
            from datetime import timezone
            two_weeks_ago = datetime.now(timezone.utc) - timedelta(days=14)
            
            existing_serp = db.scalar(
                select(WordSerp).where(
                    WordSerp.word_id == word.uuid,
                    WordSerp.llm_id == llm.uuid,
                    WordSerp.create_time > two_weeks_ago
                )
            )
            
            if existing_serp:
                logger.info(f"Word '{word.name}' with LLM '{llm.name}' already processed")
                return False
            
            logger.info(f"Processing word '{word.name}' with {llm.name}")
            
            # Get LLM response
            llm_response = self.get_llm_response(word.name, llm.name)
            
            if not llm_response:
                logger.warning(f"No response from {llm.name} for word '{word.name}'")
                return False
            
            # Save LLM response
            word_serp = WordSerp(
                content=llm_response,
                llm_id=llm.uuid,
                word_id=word.uuid,
                create_time=datetime.now(timezone.utc)
            )
            
            db.add(word_serp)
            db.flush()
            
            # Extract companies from LLM response
            companies = self.extract_companies_from_response(llm_response)
            
            # Save companies
            for company_name in companies:
                # Check if company already exists for this SERP
                existing_company = db.scalar(
                    select(Company).where(
                        Company.name == company_name,
                        Company.serp_id == word_serp.uuid
                    )
                )
                if not existing_company:
                    new_company = Company(
                        name=company_name,
                        serp_id=word_serp.uuid
                    )
                    db.add(new_company)
            
            # Analyze brand mentions for this word's group
            self.analyze_brand_mentions_for_word(word, word_serp, llm_response, db)
            
            db.commit()
            logger.info(f"Successfully processed word '{word.name}' with {llm.name}, extracted {len(companies)} companies")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing word '{word.name}' with LLM '{llm.name}': {e}")
            return False

    def analyze_brand_mentions_for_word(self, word: Word, word_serp: WordSerp, llm_response: str, db: Session) -> bool:
        """Analyze brand mentions in LLM response for specific word"""
        try:
            if not word.group_id:
                return False
            
            # Find brand project for this word group
            brand_project = db.scalar(
                select(BrandProject).where(BrandProject.word_group_id == word.group_id)
            )
            
            if not brand_project:
                return False  # Not a brand monitoring project
            
            # Get competitors for this project
            competitors = db.execute(
                select(Competitor).where(Competitor.project_id == brand_project.uuid)
            )
            competitor_names = [comp.name for comp in competitors.scalars().all()]
            
            # Analyze mentions in LLM response
            analysis_result = self.analyze_brand_mentions_in_response(
                llm_response,
                [brand_project.brand_name],
                competitor_names
            )
            
            # Save brand mention analysis
            brand_mention = BrandMention(
                serp_id=word_serp.uuid,
                project_id=brand_project.uuid,
                brand_mentioned=1 if analysis_result.get("brand_mentioned", False) else 0,
                competitor_mentioned=1 if analysis_result.get("competitor_mentioned", False) else 0,
                mentioned_competitor=analysis_result.get("mentioned_competitor"),
                brand_position=analysis_result.get("brand_position"),
                competitor_position=analysis_result.get("competitor_position"),
                analysis_confidence=analysis_result.get("confidence", 95)
            )
            
            db.add(brand_mention)
            
            logger.info(f"Brand mention analysis completed for word '{word.name}': brand={analysis_result.get('brand_mentioned')}, competitors={analysis_result.get('mentioned_competitors')}")
            return True
            
        except Exception as e:
            logger.error(f"Error analyzing brand mentions for word '{word.name}': {e}")
            return False
    

    def run_worker_cycle(self):
        """Main worker cycle for brand monitoring"""
        logger.info("🚀 Starting brand monitoring cycle")
        
        with self.SessionLocal() as db:
            try:
                # Get all active words
                words_result = db.execute(
                    select(Word).where(Word.status == 1)
                )
                words = list(words_result.scalars().all())
                
                # Get all active LLM providers
                llms_result = db.execute(
                    select(LLM).where(LLM.is_active == 1)
                )
                llms = list(llms_result.scalars().all())
                
                logger.info(f"Found {len(words)} words and {len(llms)} LLM providers")
                
                processed_count = 0
                for word in words:
                    for llm in llms:
                        success = self.process_word_with_llm(word, llm, db)
                        if success:
                            processed_count += 1
                
                logger.info(f"✅ Cycle completed. Processed {processed_count} word-LLM combinations")
                
            except Exception as e:
                logger.error(f"❌ Error in worker cycle: {e}")

    def run_continuous(self, interval_hours: int = 24 * 14):  # 2 weeks by default
        """Continuous worker operation with specified interval"""
        logger.info(f"Starting continuous worker with {interval_hours} hour interval")
        
        while True:
            try:
                self.run_worker_cycle()
                
                # Wait until next cycle
                wait_seconds = interval_hours * 3600
                logger.info(f"Waiting {interval_hours} hours until next cycle")
                time.sleep(wait_seconds)
                
            except KeyboardInterrupt:
                logger.info("Received worker stop signal")
                break
            except Exception as e:
                logger.error(f"Critical worker error: {str(e)}")
                # Wait 1 hour before retry
                time.sleep(3600)

# Глобальный экземпляр воркера
llm_worker = LLMWorker()

# Function to start worker
def start_worker():
    """Start worker"""
    llm_worker.run_continuous()

if __name__ == "__main__":
    # Direct worker startup
    start_worker()
