-- SEO Analyzer Database Schema
-- PostgreSQL database initialization script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Users table
CREATE TABLE users (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    create_time TIMESTAMP DEFAULT NOW(),
    status SMALLINT DEFAULT 1
);

-- 2. Word groups table
CREATE TABLE word_groups (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL
);

-- 3. Words table
CREATE TABLE words (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    group_id UUID REFERENCES word_groups(uuid) ON DELETE SET NULL,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP,
    delete_time TIMESTAMP,
    status SMALLINT DEFAULT 1
);

-- 4. LLM providers table
CREATE TABLE llm (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    api_url TEXT,
    api_key TEXT,
    is_active SMALLINT DEFAULT 1
);

-- 5. SERP results table
CREATE TABLE word_serp (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    llm_id UUID REFERENCES llm(uuid) ON DELETE CASCADE,
    word_id UUID REFERENCES words(uuid) ON DELETE CASCADE,
    create_time TIMESTAMP DEFAULT NOW()
);

-- 6. Companies table
CREATE TABLE companies (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    serp_id UUID REFERENCES word_serp(uuid) ON DELETE SET NULL,
    create_time TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_words_group_id ON words(group_id);
CREATE INDEX idx_words_status ON words(status);
CREATE INDEX idx_word_serp_word_id ON word_serp(word_id);
CREATE INDEX idx_word_serp_llm_id ON word_serp(llm_id);
CREATE INDEX idx_word_serp_create_time ON word_serp(create_time);
CREATE INDEX idx_companies_serp_id ON companies(serp_id);
CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_users_email ON users(email);

-- Insert default LLM providers
INSERT INTO llm (name, api_url, is_active) VALUES
('openai', 'https://api.openai.com/v1/chat/completions', 1),
('grok', 'https://api.grok.com/v1/chat/completions', 1),
('gemini', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent', 1);

-- Insert sample data (optional)
-- Test user: admin@example.com / admin123
INSERT INTO users (email, password) VALUES 
('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq9S2Gu');

-- Sample word groups
INSERT INTO word_groups (name) VALUES 
('Технологии'),
('Маркетинг'),
('E-commerce');

-- Sample words (you can add more)
INSERT INTO words (name, group_id) 
SELECT 'искусственный интеллект', uuid FROM word_groups WHERE name = 'Технологии'
UNION ALL
SELECT 'машинное обучение', uuid FROM word_groups WHERE name = 'Технологии'
UNION ALL
SELECT 'SEO оптимизация', uuid FROM word_groups WHERE name = 'Маркетинг'
UNION ALL
SELECT 'интернет магазин', uuid FROM word_groups WHERE name = 'E-commerce';

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
