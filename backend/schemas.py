from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Схемы для пользователей
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    uuid: uuid.UUID
    email: str
    create_time: datetime
    status: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Схемы для групп слов
class WordGroupCreate(BaseModel):
    name: str

class WordGroupUpdate(BaseModel):
    name: str

class WordGroupResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    
    class Config:
        from_attributes = True

# Схемы для слов
class WordCreate(BaseModel):
    name: str
    group_id: Optional[uuid.UUID] = None

class WordUpdate(BaseModel):
    name: Optional[str] = None
    group_id: Optional[uuid.UUID] = None
    status: Optional[int] = None

class WordResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    group_id: Optional[uuid.UUID]
    create_time: datetime
    update_time: Optional[datetime]
    status: int
    
    class Config:
        from_attributes = True

# Схемы для LLM
class LLMCreate(BaseModel):
    name: str
    api_url: Optional[str] = None
    api_key: Optional[str] = None

class LLMUpdate(BaseModel):
    name: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[int] = None

class LLMResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    api_url: Optional[str]
    is_active: int
    
    class Config:
        from_attributes = True

# Схемы для SERP результатов
class WordSerpResponse(BaseModel):
    uuid: uuid.UUID
    content: str
    llm_id: uuid.UUID
    word_id: uuid.UUID
    create_time: datetime
    
    class Config:
        from_attributes = True

# Схемы для компаний
class CompanyResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    serp_id: Optional[uuid.UUID]
    
    class Config:
        from_attributes = True

# Схемы для аналитики
class WordAnalytics(BaseModel):
    word: WordResponse
    serp_results: List[WordSerpResponse]
    companies: List[CompanyResponse]

class GroupAnalytics(BaseModel):
    group: WordGroupResponse
    words: List[WordAnalytics]

# Схемы для Brand Monitoring
class CompetitorCreate(BaseModel):
    name: str

class CompetitorResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    create_time: datetime
    
    class Config:
        from_attributes = True

class BrandProjectCreate(BaseModel):
    name: str
    brand_name: str
    brand_description: str
    keywords_count: int = 50
    competitors: List[str] = []

class BrandProjectUpdate(BaseModel):
    name: Optional[str] = None
    brand_name: Optional[str] = None
    brand_description: Optional[str] = None
    keywords_count: Optional[int] = None

class BrandProjectResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    brand_name: str
    brand_description: str
    keywords_count: int
    user_id: uuid.UUID
    word_group_id: Optional[uuid.UUID] = None
    create_time: datetime
    status: int
    competitors: List[CompetitorResponse] = []
    
    class Config:
        from_attributes = True

class BrandMentionResponse(BaseModel):
    uuid: uuid.UUID
    serp_id: uuid.UUID
    project_id: uuid.UUID
    brand_mentioned: int
    competitor_mentioned: int
    mentioned_competitor: Optional[str] = None
    brand_position: Optional[int] = None
    competitor_position: Optional[int] = None
    analysis_confidence: int
    create_time: datetime
    
    class Config:
        from_attributes = True

class BrandAnalytics(BaseModel):
    project_name: str
    brand_name: str
    total_queries: int
    brand_mentions: int
    competitor_mentions: int
    brand_visibility_percentage: float
    competitor_visibility_percentage: float
    top_competitors: List[Dict[str, Any]] = []
    recent_mentions: List[Dict[str, Any]] = []
