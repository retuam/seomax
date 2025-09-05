from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, Text, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    status = Column(SmallInteger, default=1)

class WordGroup(Base):
    """Модель группы слов"""
    __tablename__ = "word_groups"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"))
    create_time = Column(TIMESTAMP, server_default=func.now())
    
    # Связи
    user = relationship("User", lazy="selectin")
    words = relationship("Word", back_populates="group", lazy="selectin")

class Word(Base):
    """Модель слова"""
    __tablename__ = "words"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("word_groups.uuid", ondelete="SET NULL"))
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, onupdate=func.now())
    delete_time = Column(TIMESTAMP)
    status = Column(SmallInteger, default=1)
    
    # Связи
    group = relationship("WordGroup", back_populates="words", lazy="selectin")
    serp_results = relationship("WordSerp", back_populates="word", lazy="selectin")

class LLM(Base):
    """Модель LLM провайдера"""
    __tablename__ = "llm"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    api_url = Column(String)
    api_key = Column(String)
    is_active = Column(SmallInteger, default=1)
    
    # Связь с результатами SERP
    serp_results = relationship("WordSerp", back_populates="llm", lazy="selectin")

class WordSerp(Base):
    """Модель результатов SERP от LLM"""
    __tablename__ = "word_serp"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    llm_id = Column(UUID(as_uuid=True), ForeignKey("llm.uuid", ondelete="CASCADE"))
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.uuid", ondelete="CASCADE"))
    create_time = Column(TIMESTAMP, server_default=func.now())
    
    # Связи
    llm = relationship("LLM", back_populates="serp_results", lazy="selectin")
    word = relationship("Word", back_populates="serp_results", lazy="selectin")
    companies = relationship("Company", back_populates="serp", lazy="selectin")
    brand_mentions = relationship("BrandMention", back_populates="serp", lazy="selectin")

class Company(Base):
    """Модель компании, извлеченной из SERP"""
    __tablename__ = "companies"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    serp_id = Column(UUID(as_uuid=True), ForeignKey("word_serp.uuid", ondelete="SET NULL"))
    
    # Связь с SERP результатом
    serp = relationship("WordSerp", back_populates="companies", lazy="selectin")

class BrandProject(Base):
    """Модель проекта мониторинга бренда"""
    __tablename__ = "brand_projects"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # Название проекта
    brand_name = Column(String, nullable=False, index=True)  # Название бренда
    brand_description = Column(Text, nullable=False)  # Описание бренда
    keywords_count = Column(Integer, default=50)  # Количество ключевых слов
    word_group_id = Column(UUID(as_uuid=True), ForeignKey("word_groups.uuid", ondelete="SET NULL"))  # Связь с группой слов
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"))
    create_time = Column(TIMESTAMP, server_default=func.now())
    status = Column(SmallInteger, default=1)  # 1 - активный, 0 - неактивный
    
    # Связи
    word_group = relationship("WordGroup", lazy="selectin")
    competitors = relationship("Competitor", back_populates="project", lazy="selectin")
    brand_mentions = relationship("BrandMention", back_populates="project", lazy="selectin")

class Competitor(Base):
    """Модель конкурента в проекте"""
    __tablename__ = "competitors"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)  # Название конкурента
    project_id = Column(UUID(as_uuid=True), ForeignKey("brand_projects.uuid", ondelete="CASCADE"))
    create_time = Column(TIMESTAMP, server_default=func.now())
    
    # Связь с проектом
    project = relationship("BrandProject", back_populates="competitors", lazy="selectin")

class BrandMention(Base):
    """Модель упоминания бренда/конкурента в SERP"""
    __tablename__ = "brand_mentions"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serp_id = Column(UUID(as_uuid=True), ForeignKey("word_serp.uuid", ondelete="CASCADE"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("brand_projects.uuid", ondelete="CASCADE"))
    
    # Результаты анализа упоминаний
    brand_mentioned = Column(SmallInteger, default=0)  # 1 - упомянут, 0 - не упомянут
    competitor_mentioned = Column(SmallInteger, default=0)  # 1 - упомянут, 0 - не упомянут
    mentioned_competitor = Column(String, nullable=True)  # Какой конкурент упомянут
    
    # Дополнительная информация
    brand_position = Column(Integer, nullable=True)  # Позиция упоминания бренда (1-10)
    competitor_position = Column(Integer, nullable=True)  # Позиция упоминания конкурента
    analysis_confidence = Column(SmallInteger, default=100)  # Уверенность анализа (0-100)
    
    create_time = Column(TIMESTAMP, server_default=func.now())
    
    # Связи
    serp = relationship("WordSerp", back_populates="brand_mentions", lazy="selectin")
    project = relationship("BrandProject", back_populates="brand_mentions", lazy="selectin")
