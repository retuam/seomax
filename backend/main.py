from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from loguru import logger

# Configuration and logging imports
from config_simple import settings
from logging_config import setup_logging, setup_sentry
from database import get_db, check_database_connection, init_database, close_database, AsyncSessionLocal
from models import User, WordGroup, Word, LLM, WordSerp, Company, BrandProject, Competitor, BrandMention
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    WordGroupCreate, WordGroupUpdate, WordGroupResponse,
    WordCreate, WordUpdate, WordResponse,
    LLMCreate, LLMUpdate, LLMResponse,
    WordSerpResponse, CompanyResponse,
    WordAnalytics, GroupAnalytics,
    BrandProjectCreate, BrandProjectResponse, BrandProjectUpdate,
    CompetitorResponse, BrandMentionResponse, BrandAnalytics
)
from auth import hash_password, verify_password, create_access_token, get_current_user
from llm_service_modern import llm_service
import requests
import json
from datetime import datetime, timedelta

# === DIRECT SERP UPDATE FUNCTIONS ===

async def get_gemini_response_direct(word: str) -> str:
    """Direct Gemini response retrieval for brand analysis"""
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{"text": word}]
            }],
            "generationConfig": {
                "maxOutputTokens": 2000,
                "temperature": 0.7
            }
        }
        
        response = requests.post(
            f"{settings.gemini_api_url}?key={settings.gemini_api_key}",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            logger.error(f"Gemini API error: {response.status_code}")
            raise Exception(f"Gemini API failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {e}")
        raise Exception(f"Failed to get Gemini response: {e}")

async def get_anthropic_response_direct(word: str) -> str:
    """Direct Anthropic response retrieval for brand analysis"""
    try:
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": settings.anthropic_model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": word}]
        }
        
        response = requests.post(
            settings.anthropic_api_url,
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text']
        else:
            logger.error(f"Anthropic API error: {response.status_code}")
            raise Exception(f"Anthropic API failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting response from Anthropic: {e}")
        raise Exception(f"Failed to get Anthropic response: {e}")

async def get_grok_response_direct(word: str) -> str:
    """Direct Grok response retrieval for brand analysis"""
    try:
        headers = {
            "Authorization": f"Bearer {settings.grok_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": settings.grok_model,
            "messages": [{"role": "user", "content": word}],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        response = requests.post(
            settings.grok_api_url,
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"Grok API error: {response.status_code}")
            raise Exception(f"Grok API failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting response from Grok: {e}")
        raise Exception(f"Failed to get Grok response: {e}")

async def get_mistral_response_direct(word: str) -> str:
    """Direct Mistral response retrieval for brand analysis"""
    try:
        headers = {
            "Authorization": f"Bearer {settings.mistral_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": settings.mistral_model,
            "messages": [{"role": "user", "content": word}],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        response = requests.post(
            settings.mistral_api_url,
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"Mistral API error: {response.status_code}")
            raise Exception(f"Mistral API failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting response from Mistral: {e}")
        raise Exception(f"Failed to get Mistral response: {e}")

async def get_perplexity_response_direct(word: str) -> str:
    """Direct Perplexity response retrieval for brand analysis"""
    try:
        headers = {
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": settings.perplexity_model,
            "messages": [{"role": "user", "content": word}],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        response = requests.post(
            settings.perplexity_api_url,
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"Perplexity API error: {response.status_code}")
            raise Exception(f"Perplexity API failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting response from Perplexity: {e}")
        raise Exception(f"Failed to get Perplexity response: {e}")

async def get_openai_response_direct(word: str) -> str:
    """Direct OpenAI response retrieval for brand analysis"""
    try:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": word}],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"OpenAI API error: {response.status_code}")
            raise Exception(f"OpenAI API failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting response from OpenAI: {e}")
        raise Exception(f"Failed to get OpenAI response: {e}")

async def extract_companies_from_response_direct(llm_response: str) -> list:
    """Direct company extraction from LLM response"""
    try:
        prompt = f"""
        Analyze the following text and extract company names, brands, and organizations.
        Return only a list of names separated by commas, without additional text.
        
        Text:
        {llm_response}
        """
        
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            companies_text = result['choices'][0]['message']['content']
            companies = [c.strip() for c in companies_text.split(',') if c.strip()]
            return companies[:10]  # Maximum 10 companies
        else:
            logger.error(f"OpenAI API error during company extraction: {response.status_code}")
            raise Exception(f"OpenAI API failed during company extraction: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error extracting companies: {e}")
        raise Exception(f"Failed to extract companies: {e}")

async def update_serp_data_direct(db: AsyncSession, group_id: Optional[uuid.UUID] = None):
    """Direct SERP data update without worker with brand monitoring support"""
    try:
        logger.info("🚀 Starting direct SERP data update")
        
        # Get active words
        words_query = select(Word).where(Word.status == 1)
        if group_id:
            words_query = words_query.where(Word.group_id == group_id)
        
        words_result = await db.execute(words_query)
        words = list(words_result.scalars().all())
        
        # Get active LLMs
        llms_result = await db.execute(select(LLM).where(LLM.is_active == 1))
        llms = list(llms_result.scalars().all())
        
        logger.info(f"Found {len(words)} words and {len(llms)} LLMs for processing")
        
        processed_count = 0
        
        for word in words:
            for llm in llms:
                try:
                    # Check if data needs updating
                    from datetime import timezone
                    two_weeks_ago = datetime.now(timezone.utc) - timedelta(days=14)
                    # Remove timezone for PostgreSQL comparison
                    two_weeks_ago_naive = two_weeks_ago.replace(tzinfo=None)
                    
                    existing_serp = await db.scalar(
                        select(WordSerp).where(
                            and_(
                                WordSerp.word_id == word.uuid,
                                WordSerp.llm_id == llm.uuid,
                                WordSerp.create_time > two_weeks_ago_naive
                            )
                        )
                    )
                    
                    if existing_serp:
                        logger.info(f"Word '{word.name}' with LLM '{llm.name}' already processed")
                        continue
                    
                    logger.info(f"Processing word '{word.name}' with {llm.name}")
                    
                    # Get LLM response
                    if llm.name.lower() == "openai":
                        if not settings.openai_api_key:
                            logger.error(f"OpenAI API key not configured, skipping LLM '{llm.name}'")
                            continue
                        llm_response = await get_openai_response_direct(word.name)
                    elif llm.name.lower() == "gemini":
                        if not settings.gemini_api_key:
                            logger.error(f"Gemini API key not configured, skipping LLM '{llm.name}'")
                            continue
                        llm_response = await get_gemini_response_direct(word.name)
                    elif llm.name.lower() == "anthropic":
                        if not settings.anthropic_api_key:
                            logger.error(f"Anthropic API key not configured, skipping LLM '{llm.name}'")
                            continue
                        llm_response = await get_anthropic_response_direct(word.name)
                    elif llm.name.lower() == "grok":
                        if not settings.grok_api_key:
                            logger.error(f"Grok API key not configured, skipping LLM '{llm.name}'")
                            continue
                        llm_response = await get_grok_response_direct(word.name)
                    elif llm.name.lower() == "mistral":
                        if not settings.mistral_api_key:
                            logger.error(f"Mistral API key not configured, skipping LLM '{llm.name}'")
                            continue
                        llm_response = await get_mistral_response_direct(word.name)
                    elif llm.name.lower() == "perplexity":
                        if not settings.perplexity_api_key:
                            logger.error(f"Perplexity API key not configured, skipping LLM '{llm.name}'")
                            continue
                        llm_response = await get_perplexity_response_direct(word.name)
                    else:
                        logger.warning(f"LLM {llm.name} not implemented, skipping")
                        continue
                    
                    if not llm_response:
                        logger.warning(f"No response from {llm.name} for word '{word.name}'")
                        continue
                    
                    # Save LLM response
                    word_serp = WordSerp(
                        content=llm_response,
                        llm_id=llm.uuid,
                        word_id=word.uuid,
                        create_time=datetime.now(timezone.utc).replace(tzinfo=None)
                    )
                    
                    db.add(word_serp)
                    await db.flush()
                    
                    # Extract companies from LLM response
                    companies = await extract_companies_from_response_direct(llm_response)
                    
                    # Save companies
                    for company_name in companies:
                        existing_company = await db.scalar(
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
                    
                    # Analyze brand mentions for this word group (if brand projects exist)
                    if word.group_id:
                        await analyze_brand_mentions_for_word_direct(word, word_serp, llm_response, db)
                    
                    processed_count += 1
                    
                    # Commit every 10 processed pairs
                    if processed_count % 10 == 0:
                        await db.commit()
                        logger.info(f"Processed {processed_count} word-LLM pairs")
                    
                except Exception as e:
                    logger.error(f"Error processing word '{word.name}' with LLM '{llm.name}': {e}")
                    continue
        
        # Final commit
        await db.commit()
        logger.info(f"✅ SERP data update completed. Processed {processed_count} pairs, extracted companies and analyzed brands")
        
    except Exception as e:
        logger.error(f"Error in direct SERP data update: {e}")
        await db.rollback()
        raise

async def analyze_brand_mentions_for_word_direct(word, word_serp, llm_response, db):
    """Analyze brand mentions in LLM response for specific word"""
    try:
        from datetime import timezone
        
        # Get all brand projects for this word's group
        brand_projects = await db.execute(
            select(BrandProject).where(BrandProject.word_group_id == word.group_id)
        )
        
        for brand_project in brand_projects.scalars().all():
            logger.info(f"🔍 Analyzing brand project: {brand_project.name} (brand: {brand_project.brand_name})")
            
            # Get competitors for this project
            competitors = await db.execute(
                select(Competitor).where(Competitor.project_id == brand_project.uuid)
            )
            competitors_list = list(competitors.scalars().all())
            logger.info(f"📋 Found {len(competitors_list)} competitors: {[c.name for c in competitors_list]}")
            
            # Check brand and competitor mentions
            brand_mentioned = brand_project.brand_name.lower() in llm_response.lower()
            logger.info(f"🏷️ Brand '{brand_project.brand_name}' mentioned: {brand_mentioned}")
            
            # Always create a record for the brand project, even if no competitors
            if not competitors_list:
                logger.info("⚠️ No competitors found, creating brand-only mention record")
                brand_mention = BrandMention(
                    project_id=brand_project.uuid,
                    serp_id=word_serp.uuid,
                    brand_mentioned=1 if brand_mentioned else 0,
                    mentioned_competitor=None,
                    competitor_mentioned=0
                )
                db.add(brand_mention)
                logger.info(f"✅ Created brand mention record: brand={brand_mentioned}")
            
            for competitor in competitors_list:
                competitor_mentioned = competitor.name.lower() in llm_response.lower()
                logger.info(f"🏢 Competitor '{competitor.name}' mentioned: {competitor_mentioned}")
                
                # Create mention record for each competitor (whether mentioned or not)
                brand_mention = BrandMention(
                    project_id=brand_project.uuid,
                    serp_id=word_serp.uuid,
                    brand_mentioned=1 if brand_mentioned else 0,
                    mentioned_competitor=competitor.name,
                    competitor_mentioned=1 if competitor_mentioned else 0
                )
                db.add(brand_mention)
                logger.info(f"✅ Created mention record: brand={brand_mentioned}, competitor={competitor.name}, mentioned={competitor_mentioned}")
                    
    except Exception as e:
        logger.error(f"Error analyzing brand mentions: {e}")

# Logging and monitoring setup
setup_logging()
if settings.sentry_dsn:
    setup_sentry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info(" Starting SEO Analyzer API...")
    
    # Check database connection
    if await check_database_connection():
        logger.info("Database connection established")
    else:
        logger.warning("Database connection failed - starting without DB")
        # Don't stop server, just warn
    
    # Initialize database (only if connection successful)
    try:
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
    
    # Initialize LLM service
    available_providers = llm_service.get_available_providers()
    logger.info(f"LLM Service initialized with providers: {available_providers}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SEO Analyzer API...")
    await close_database()
    logger.info("Database connections closed")

app = FastAPI(
    title="SEO Analyzer API",
    description="API for SEO keyword analysis with LLM integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.allowed_hosts or ["*"]
)

# CORS settings for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains
    allow_credentials=False,  # Disable credentials for security when allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# === AUTHENTICATION ===

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    existing_user = await db.scalar(select(User).where(User.email == user_data.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """User authentication"""
    user = await db.scalar(select(User).where(User.email == user_data.email))
    
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# === WORD GROUPS ===

@app.get("/api/word-groups", response_model=List[WordGroupResponse])
async def get_word_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all user word groups"""
    result = await db.execute(select(WordGroup).where(WordGroup.user_id == current_user.uuid))
    return result.scalars().all()

@app.post("/api/word-groups", response_model=WordGroupResponse)
async def create_word_group(
    group_data: WordGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new word group"""
    new_group = WordGroup(name=group_data.name, user_id=current_user.uuid)
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group

@app.put("/api/word-groups/{group_id}", response_model=WordGroupResponse)
async def update_word_group(
    group_id: uuid.UUID,
    group_data: WordGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update word group"""
    group = await db.scalar(select(WordGroup).where(
        WordGroup.uuid == group_id,
        WordGroup.user_id == current_user.uuid
    ))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group.name = group_data.name
    await db.commit()
    await db.refresh(group)
    return group

@app.delete("/api/word-groups/{group_id}")
async def delete_word_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete word group"""
    group = await db.scalar(select(WordGroup).where(
        WordGroup.uuid == group_id,
        WordGroup.user_id == current_user.uuid
    ))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    await db.delete(group)
    await db.commit()
    return {"message": "Group deleted"}

# === WORDS ===

@app.get("/api/words", response_model=List[WordResponse])
async def get_words(
    group_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all words or words from specific group"""
    query = select(Word).where(Word.status == 1)
    if group_id:
        query = query.where(Word.group_id == group_id)
    
    result = await db.execute(query)
    return result.scalars().all()

@app.post("/api/words", response_model=WordResponse)
async def create_word(
    word_data: WordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new word"""
    new_word = Word(
        name=word_data.name,
        group_id=word_data.group_id
    )
    db.add(new_word)
    await db.commit()
    await db.refresh(new_word)
    return new_word

@app.put("/api/words/{word_id}", response_model=WordResponse)
async def update_word(
    word_id: uuid.UUID,
    word_data: WordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update word"""
    word = await db.scalar(select(Word).where(Word.uuid == word_id))
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    
    if word_data.name is not None:
        word.name = word_data.name
    if word_data.group_id is not None:
        word.group_id = word_data.group_id
    if word_data.status is not None:
        word.status = word_data.status
    
    await db.commit()
    await db.refresh(word)
    return word

@app.delete("/api/words/{word_id}")
async def delete_word(
    word_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete word"""
    word = await db.scalar(select(Word).where(Word.uuid == word_id))
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    
    word.status = 0  # Soft delete
    await db.commit()
    return {"message": "Word deleted"}

# === LLM PROVIDERS ===

@app.get("/api/llm", response_model=List[LLMResponse])
async def get_llm_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all LLM providers"""
    result = await db.execute(select(LLM))
    return result.scalars().all()

@app.post("/api/llm", response_model=LLMResponse)
async def create_llm_provider(
    llm_data: LLMCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new LLM provider"""
    new_llm = LLM(
        name=llm_data.name,
        api_url=llm_data.api_url,
        api_key=llm_data.api_key
    )
    db.add(new_llm)
    await db.commit()
    await db.refresh(new_llm)
    return new_llm

# === АНАЛИТИКА ===

async def _get_word_analytics_data(
    word_id: uuid.UUID,
    db: AsyncSession
) -> WordAnalytics:
    """Internal function to get word analytics"""
    try:
        word = await db.scalar(select(Word).where(Word.uuid == word_id))
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")
        
        # Get SERP results
        serp_results = await db.execute(
            select(WordSerp).where(WordSerp.word_id == word_id)
        )
        serp_list = list(serp_results.scalars().all())
        
        # Get companies (without JOIN for simplicity)
        companies_list = []
        if serp_list:
            for serp in serp_list:
                companies_result = await db.execute(
                    select(Company).where(Company.serp_id == serp.uuid)
                )
                companies_list.extend(companies_result.scalars().all())
        
        return WordAnalytics(
            word=word,
            serp_results=serp_list,
            companies=companies_list
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting word analytics {word_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")

@app.get("/api/analytics/word/{word_id}")
async def get_word_analytics(
    word_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for specific word"""
    try:
        logger.info(f"Getting analytics for word: {word_id}")
        
        # Get word
        word = await db.scalar(select(Word).where(Word.uuid == word_id))
        if not word:
            logger.warning(f"Word {word_id} not found")
            return {"error": "Word not found"}

        logger.info(f"Word found: {word.name}")

        # Get SERP results
        serp_results = await db.execute(select(WordSerp).where(WordSerp.word_id == word_id))
        serp_list = list(serp_results.scalars().all())

        # Get companies
        companies_list = []
        for serp in serp_list:
            companies_result = await db.execute(select(Company).where(Company.serp_id == serp.uuid))
            companies_list.extend(companies_result.scalars().all())

        logger.info(f"Found SERP: {len(serp_list)}, companies: {len(companies_list)}")

        # Return simple structure
        return {
            "word": {
                "uuid": str(word.uuid),
                "name": word.name,
                "group_id": str(word.group_id) if word.group_id else None,
                "status": word.status,
                "create_time": word.create_time.isoformat() if word.create_time else None
            },
            "serp_results": [
                {
                    "uuid": str(serp.uuid),
                    "content": serp.content[:100] + "..." if len(serp.content) > 100 else serp.content,
                    "llm_id": str(serp.llm_id) if serp.llm_id else None,
                    "create_time": serp.create_time.isoformat() if serp.create_time else None
                } for serp in serp_list
            ],
            "companies": [
                {
                    "uuid": str(company.uuid),
                    "name": company.name,
                    "serp_id": str(company.serp_id) if company.serp_id else None
                } for company in companies_list
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting word analytics {word_id}: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Error: {str(e)}"}

@app.post("/api/analytics/start")
async def start_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start general analytics"""
    try:
        # Direct SERP data update without worker
        await update_serp_data_direct(db)
        return {"message": "Analytics started", "status": "started"}
    except Exception as e:
        logger.error(f"Error starting analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting analytics: {str(e)}")

@app.post("/api/analytics/group/start")
async def start_group_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start analytics for all groups"""
    try:
        # Direct SERP data update without worker
        await update_serp_data_direct(db)
        return {"message": "Group analytics started", "status": "started"}
    except Exception as e:
        logger.error(f"Error starting group analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting group analytics: {str(e)}")

@app.post("/api/analytics/group/{group_id}/start")
async def start_group_analytics_by_id(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start brand analysis for specific word group"""
    try:
        # Check group existence
        group = await db.scalar(select(WordGroup).where(WordGroup.uuid == group_id))
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if there are brand projects for this group
        brand_projects = await db.execute(
            select(BrandProject).where(BrandProject.word_group_id == group_id)
        )
        brand_projects_list = list(brand_projects.scalars().all())
        
        if not brand_projects_list:
            logger.warning(f"No brand projects found for group {group_id}")
            return {
                "message": f"No brand projects found for group {group.name}",
                "status": "no_projects",
                "group_name": group.name
            }
        
        logger.info(f"Starting brand analysis for group {group.name} with {len(brand_projects_list)} brand projects")
        
        # Run SERP data update and brand analysis
        await update_serp_data_direct(db, group_id=group_id)
        
        # Get analysis results including company extraction
        total_mentions = 0
        brand_mentions = 0
        competitor_mentions = 0
        extracted_companies = set()
        tracked_brands = []
        tracked_competitors = []
        
        for project in brand_projects_list:
            # Get brand mentions for this project
            mentions_result = await db.execute(
                select(BrandMention).where(BrandMention.project_id == project.uuid)
            )
            mentions = list(mentions_result.scalars().all())
            
            total_mentions += len(mentions)
            brand_mentions += sum(1 for m in mentions if m.brand_mentioned)
            competitor_mentions += sum(1 for m in mentions if m.competitor_mentioned)
            
            # Track brands and competitors for this project
            tracked_brands.append({
                "brand_name": project.brand_name,
                "mentions": sum(1 for m in mentions if m.brand_mentioned),
                "project_name": project.name
            })
            
            # Get competitors for this project
            competitors_result = await db.execute(
                select(Competitor).where(Competitor.project_id == project.uuid)
            )
            competitors = list(competitors_result.scalars().all())
            
            for competitor in competitors:
                competitor_mention_count = sum(1 for m in mentions if m.competitor_mentioned and m.mentioned_competitor == competitor.name)
                if competitor_mention_count > 0:
                    tracked_competitors.append({
                        "competitor_name": competitor.name,
                        "mentions": competitor_mention_count,
                        "project_name": project.name
                    })
        
        # Get all companies extracted from LLM responses for this group
        words_in_group = await db.execute(
            select(Word).where(Word.group_id == group_id, Word.status == 1)
        )
        words_list = list(words_in_group.scalars().all())
        
        for word in words_list:
            # Get SERP results for this word
            serp_results = await db.execute(
                select(WordSerp).where(WordSerp.word_id == word.uuid)
            )
            serp_list = list(serp_results.scalars().all())
            
            # Get companies extracted from these SERP results
            for serp in serp_list:
                companies_result = await db.execute(
                    select(Company).where(Company.serp_id == serp.uuid)
                )
                companies = list(companies_result.scalars().all())
                for company in companies:
                    extracted_companies.add(company.name)
        
        return {
            "message": f"Brand analysis for group {group.name} completed",
            "status": "completed",
            "group_name": group.name,
            "brand_projects_count": len(brand_projects_list),
            "analysis_results": {
                "total_mentions": total_mentions,
                "brand_mentions": brand_mentions,
                "competitor_mentions": competitor_mentions,
                "brand_visibility_percentage": (brand_mentions / total_mentions * 100) if total_mentions > 0 else 0,
                "extracted_companies_count": len(extracted_companies),
                "extracted_companies": sorted(list(extracted_companies)),
                "tracked_brands": tracked_brands,
                "tracked_competitors": tracked_competitors
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting brand analysis for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Error starting brand analysis")

@app.get("/api/analytics/group/{group_id}")
async def get_group_analytics(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for word group"""
    try:
        logger.info(f"Getting analytics for group: {group_id}")
        
        # Get group
        group = await db.scalar(select(WordGroup).where(WordGroup.uuid == group_id))
        if not group:
            logger.warning(f"Group {group_id} not found")
            return {"error": "Group not found"}
        
        logger.info(f"Group found: {group.name}")
        
        # Get words in group
        words_result = await db.execute(select(Word).where(Word.group_id == group_id))
        words_list = list(words_result.scalars().all())
        
        logger.info(f"Found words in group: {len(words_list)}")
        
        # Build analytics for each word
        words_analytics = []
        for word in words_list:
            # Get SERP for each word
            serp_results = await db.execute(select(WordSerp).where(WordSerp.word_id == word.uuid))
            serp_list = list(serp_results.scalars().all())
            
            # Get companies
            companies_list = []
            for serp in serp_list:
                companies_result = await db.execute(select(Company).where(Company.serp_id == serp.uuid))
                companies_list.extend(companies_result.scalars().all())
            
            words_analytics.append({
                "word": {
                    "uuid": str(word.uuid),
                    "name": word.name,
                    "status": word.status,
                    "create_time": word.create_time.isoformat() if word.create_time else None
                },
                "serp_count": len(serp_list),
                "companies_count": len(companies_list)
            })
        
        return {
            "group": {
                "uuid": str(group.uuid),
                "name": group.name
            },
            "words": words_analytics,
            "words_count": len(words_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting group analytics {group_id}: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Error: {str(e)}"}


@app.post("/api/serp/update")
async def update_serp_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start SERP data update cycle"""
    try:
        # Direct SERP data update without worker
        await update_serp_data_direct(db)
        return {"message": "SERP data update cycle started"}
    except Exception as e:
        logger.error(f"Error updating SERP data: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating SERP data: {str(e)}")

# === STATISTICS ===

@app.get("/api/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get general statistics"""
    # Count various entities
    words_count = await db.scalar(select(func.count(Word.uuid)).where(Word.status == 1))
    groups_count = await db.scalar(select(func.count(WordGroup.uuid)))
    serp_count = await db.scalar(select(func.count(WordSerp.uuid)))
    companies_count = await db.scalar(select(func.count(Company.uuid)))
    
    return {
        "words_count": words_count,
        "groups_count": groups_count,
        "serp_results_count": serp_count,
        "companies_count": companies_count
    }

# === BRAND MONITORING ===

@app.post("/api/brand-projects", response_model=BrandProjectResponse, status_code=201)
async def create_brand_project(
    project_data: BrandProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Debug logging
        logger.info(f"Creating brand project with word_group_id: {project_data.word_group_id}")
        
        # Check word group existence if specified
        if project_data.word_group_id:
            group_result = await db.execute(
                select(WordGroup).where(WordGroup.uuid == project_data.word_group_id)
            )
            word_group = group_result.scalar_one_or_none()
            if not word_group:
                logger.warning(f"Word group with ID {project_data.word_group_id} not found")
                raise HTTPException(status_code=400, detail="Word group not found")
            logger.info(f"Found word group: {word_group.name}")
        
        # 1. Create project
        brand_project = BrandProject(
            name=project_data.name,
            brand_name=project_data.brand_name,
            brand_description=project_data.brand_description,
            keywords_count=project_data.keywords_count,
            user_id=current_user.uuid,
            word_group_id=project_data.word_group_id  # Link to word group
        )
        db.add(brand_project)
        await db.flush()
        
        # Logging after creation
        logger.info(f"Brand project created with UUID: {brand_project.uuid}, word_group_id: {brand_project.word_group_id}")

        # 2. Create competitors (if provided)
        competitors = []
        for competitor_name in (project_data.competitors or [])[:10]:
            competitor = Competitor(
                name=competitor_name.strip(),
                project_id=brand_project.uuid
            )
            db.add(competitor)
            competitors.append(competitor)

        await db.commit()
        await db.refresh(brand_project)

        # 3. Load competitors
        competitors_result = await db.execute(
            select(Competitor).where(Competitor.project_id == brand_project.uuid)
        )
        competitors_db = competitors_result.scalars().all()

        # 4. Build dict for BrandProjectResponse (Pydantic v2)
        response = {
            "uuid": brand_project.uuid,
            "name": brand_project.name,
            "brand_name": brand_project.brand_name,
            "brand_description": brand_project.brand_description,
            "keywords_count": brand_project.keywords_count,
            "user_id": brand_project.user_id,
            "word_group_id": brand_project.word_group_id,
            "create_time": brand_project.create_time,
            "status": brand_project.status,
            "competitors": [
                {
                    "uuid": c.uuid,
                    "name": c.name,
                    "create_time": c.create_time
                }
                for c in competitors_db
            ]
        }

        # Response logging
        logger.info(f"Sending response with word_group_id: {response['word_group_id']}")

        # 5. Return via Pydantic v2 model (if doesn't match - catch error in log!)
        return BrandProjectResponse.model_validate(response)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating brand project: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.put("/api/brand-projects/{project_id}", response_model=BrandProjectResponse)
async def update_brand_project(
    project_id: uuid.UUID,
    project_data: BrandProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Debug logging
        logger.info(f"Updating brand project {project_id} with word_group_id: {project_data.word_group_id}")
        
        # 1. Find project
        project_result = await db.execute(
            select(BrandProject).where(
                BrandProject.uuid == project_id,
                BrandProject.user_id == current_user.uuid
            )
        )
        brand_project = project_result.scalar_one_or_none()
        
        if not brand_project:
            raise HTTPException(status_code=404, detail="Brand project not found")
        
        logger.info(f"Current project word_group_id: {brand_project.word_group_id}")
        
        # Check word group existence if specified
        if project_data.word_group_id:
            group_result = await db.execute(
                select(WordGroup).where(WordGroup.uuid == project_data.word_group_id)
            )
            word_group = group_result.scalar_one_or_none()
            if not word_group:
                logger.warning(f"Word group with ID {project_data.word_group_id} not found")
                raise HTTPException(status_code=400, detail="Word group not found")
            logger.info(f"Found word group for update: {word_group.name}")
        
        # 2. Update fields
        if project_data.name is not None:
            brand_project.name = project_data.name
        if project_data.brand_name is not None:
            brand_project.brand_name = project_data.brand_name
        if project_data.brand_description is not None:
            brand_project.brand_description = project_data.brand_description
        if project_data.keywords_count is not None:
            brand_project.keywords_count = project_data.keywords_count
        if project_data.word_group_id is not None:
            brand_project.word_group_id = project_data.word_group_id
        
        # 3. Update competitors if provided
        if project_data.competitors is not None:
            # Delete old competitors
            existing_competitors = await db.execute(
                select(Competitor).where(Competitor.project_id == brand_project.uuid)
            )
            for competitor in existing_competitors.scalars().all():
                await db.delete(competitor)
            
            # Add new competitors
            for competitor_name in project_data.competitors[:10]:
                if competitor_name.strip():
                    competitor = Competitor(
                        name=competitor_name.strip(),
                        project_id=brand_project.uuid
                    )
                    db.add(competitor)
            
        await db.commit()
        await db.refresh(brand_project)
        
        # Logging after update
        logger.info(f"Brand project updated, new word_group_id: {brand_project.word_group_id}")
        
        # 3. Load competitors
        competitors_result = await db.execute(
            select(Competitor).where(Competitor.project_id == brand_project.uuid)
        )
        competitors_db = competitors_result.scalars().all()
        
        # 4. Build response
        response = {
            "uuid": brand_project.uuid,
            "name": brand_project.name,
            "brand_name": brand_project.brand_name,
            "brand_description": brand_project.brand_description,
            "keywords_count": brand_project.keywords_count,
            "user_id": brand_project.user_id,
            "word_group_id": brand_project.word_group_id,
            "create_time": brand_project.create_time,
            "status": brand_project.status,
            "competitors": [
                {
                    "uuid": c.uuid,
                    "name": c.name,
                    "create_time": c.create_time
                }
                for c in competitors_db
            ]
        }
        
        # PUT response logging
        logger.info(f"Sending PUT response with word_group_id: {response['word_group_id']}")
        
        return BrandProjectResponse.model_validate(response)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating brand project: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/api/brand-projects", response_model=List[BrandProjectResponse])
async def get_brand_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects_result = await db.execute(
        select(BrandProject).where(
            BrandProject.user_id == current_user.uuid,
            BrandProject.status == 1
        )
    )
    projects = projects_result.scalars().all()
    responses = []
    for project in projects:
        competitors_result = await db.execute(
            select(Competitor).where(Competitor.project_id == project.uuid)
        )
        competitors = competitors_result.scalars().all()
        competitors_resp = [
            CompetitorResponse(
                uuid=c.uuid,
                name=c.name,
                create_time=c.create_time
            ) for c in competitors
        ]
        responses.append(BrandProjectResponse.model_validate({
            "uuid": project.uuid,
            "name": project.name,
            "brand_name": project.brand_name,
            "brand_description": project.brand_description,
            "keywords_count": project.keywords_count,
            "user_id": project.user_id,
            "word_group_id": project.word_group_id,
            "create_time": project.create_time,
            "status": project.status,
            "competitors": competitors_resp,
        }))
    return responses


@app.get("/api/brand-projects/{project_id}", response_model=BrandProjectResponse)
async def get_brand_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await db.scalar(
        select(BrandProject)
        .where(BrandProject.uuid == project_id)
        .where(BrandProject.user_id == current_user.uuid)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    competitors_result = await db.execute(
        select(Competitor).where(Competitor.project_id == project.uuid)
    )
    competitors = competitors_result.scalars().all()
    competitors_resp = [
        CompetitorResponse(
            uuid=c.uuid,
            name=c.name,
            create_time=c.create_time
        ) for c in competitors
    ]

    return BrandProjectResponse.model_validate({
        "uuid": project.uuid,
        "name": project.name,
        "brand_name": project.brand_name,
        "brand_description": project.brand_description,
        "keywords_count": project.keywords_count,
        "user_id": project.user_id,
        "word_group_id": project.word_group_id,
        "create_time": project.create_time,
        "status": project.status,
        "competitors": competitors_resp,
    })

@app.get("/api/brand-projects/{project_id}/analytics")
async def get_brand_analytics(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Check project existence
        project = await db.scalar(
            select(BrandProject)
            .where(BrandProject.uuid == project_id)
            .where(BrandProject.user_id == current_user.uuid)
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get all mentions for project
        mentions_result = await db.execute(
            select(BrandMention).where(BrandMention.project_id == project_id)
        )
        mentions_list = mentions_result.scalars().all()

        total_queries = len(mentions_list)
        brand_mentions = sum(1 for m in mentions_list if m.brand_mentioned == 1)
        competitor_mentions = sum(1 for m in mentions_list if m.competitor_mentioned == 1)

        competitor_stats = {}
        for mention in mentions_list:
            if mention.mentioned_competitor:
                competitor_stats[mention.mentioned_competitor] = competitor_stats.get(mention.mentioned_competitor, 0) + 1
        top_competitors = [
            {"name": name, "mentions": count}
            for name, count in sorted(competitor_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # If you need schema - BrandAnalytics (as in your schemas.py)
        return {
            "project_name": project.name,
            "brand_name": project.brand_name,
            "total_queries": total_queries,
            "brand_mentions": brand_mentions,
            "competitor_mentions": competitor_mentions,
            "brand_visibility_percentage": (brand_mentions / total_queries * 100) if total_queries > 0 else 0,
            "competitor_visibility_percentage": (competitor_mentions / total_queries * 100) if total_queries > 0 else 0,
            "top_competitors": top_competitors,
            "recent_mentions": [
                {
                    "uuid": str(m.uuid),
                    "serp_id": str(m.serp_id),
                    "brand_mentioned": m.brand_mentioned,
                    "competitor_mentioned": m.competitor_mentioned,
                    "mentioned_competitor": m.mentioned_competitor,
                    "brand_position": m.brand_position,
                    "competitor_position": m.competitor_position,
                    "analysis_confidence": m.analysis_confidence,
                    "create_time": m.create_time.isoformat() if m.create_time else None,
                }
                for m in mentions_list[:10]
            ]
        }
        # Can wrap this in BrandAnalytics.model_validate(...) if you want strict validation

    except Exception as e:
        logger.error(f"Error getting brand analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")


@app.delete("/api/brand-projects/{project_id}")
async def delete_brand_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await db.scalar(
        select(BrandProject)
        .where(BrandProject.uuid == project_id)
        .where(BrandProject.user_id == current_user.uuid)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Soft delete
    project.status = 0
    await db.commit()
    return {"message": "Project deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
