-- JJikMuk RAG 데이터베이스 초기화 스크립트
-- PostgreSQL + pgvector

-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 기존 테이블 삭제 (있는 경우)
DROP TABLE IF EXISTS knowledge_documents CASCADE;
DROP TABLE IF EXISTS analysis_rules CASCADE;

-- 3. 지식 베이스 문서 테이블
CREATE TABLE knowledge_documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 4. 분석 규칙 테이블
CREATE TABLE analysis_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(50) NOT NULL,
    condition_key VARCHAR(100) NOT NULL,
    condition_aliases TEXT[] DEFAULT '{}',
    allergen_keywords TEXT[] DEFAULT '{}',
    nutrient_limits JSONB,
    forbidden_ingredients TEXT[] DEFAULT '{}',
    warning_message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',
    score_impact INTEGER DEFAULT -10,
    description TEXT,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. 인덱스 생성
CREATE INDEX idx_knowledge_category ON knowledge_documents(category);
CREATE INDEX idx_knowledge_embedding ON knowledge_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_rules_type ON analysis_rules(rule_type);
CREATE INDEX idx_rules_condition ON analysis_rules(condition_key);
CREATE INDEX idx_rules_condition_lower ON analysis_rules(LOWER(condition_key));

-- 6. 전문 검색을 위한 GIN 인덱스 (keywords 배열)
CREATE INDEX idx_knowledge_keywords ON knowledge_documents USING GIN(keywords);
CREATE INDEX idx_rules_aliases ON analysis_rules USING GIN(condition_aliases);
CREATE INDEX idx_rules_allergens ON analysis_rules USING GIN(allergen_keywords);

-- 7. 업데이트 트리거
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_knowledge_updated
    BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- 8. 확인
SELECT 'Database initialized successfully!' as status;
