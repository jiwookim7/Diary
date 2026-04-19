"""users 테이블에 password 컬럼을 추가하는 스크립트"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# 데이터베이스 연결
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # users 테이블의 현재 구조 확인
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users'
    """))
    
    print("현재 users 테이블 구조:")
    columns = []
    for row in result:
        columns.append(row[0])
        print(f"  - {row[0]}: {row[1]}")
    
    # password 컬럼이 없으면 추가
    if 'password' not in columns:
        print("\n❌ password 컬럼이 없습니다. 추가합니다...")
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN password VARCHAR(255) NOT NULL DEFAULT ''
        """))
        conn.commit()
        print("✅ password 컬럼이 추가되었습니다!")
    else:
        print("\n✅ password 컬럼이 이미 존재합니다.")

print("\n완료!")
