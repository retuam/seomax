import asyncio
import asyncpg

async def fix_llm_table():
    """Добавляет недостающее поле api_url в таблицу llm"""
    conn = await asyncpg.connect(
        'postgresql://postgres.usshslzenyrubetvwenc:1GmN3pj6kBWbcRsJ@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
    )
    
    try:
        # Добавляем поле api_url если его нет
        await conn.execute('ALTER TABLE llm ADD COLUMN IF NOT EXISTS api_url VARCHAR;')
        print("✅ Поле api_url добавлено в таблицу llm")
        
        # Проверяем структуру таблицы
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'llm'
            ORDER BY ordinal_position;
        """)
        
        print("\n📋 Структура таблицы llm:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_llm_table())
