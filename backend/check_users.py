"""
Render PostgreSQL에서 users 테이블 조회 (간단 버전)
"""
from sqlalchemy import create_engine, text

# Render DB URL
DB_URL = "postgresql://diary_user:sOTdNYyoI5fTmOP9If60VXDtFBwwfUO0@dpg-d7ij40vlk1mc739v7sp0-a.singapore-postgres.render.com/diary_db_4x2d"

engine = create_engine(DB_URL)

print("\n" + "=" * 70)
print("📊 Render PostgreSQL - users 테이블 조회")
print("=" * 70)

with engine.connect() as conn:
    # 테이블 목록 확인
    print("\n📋 테이블 목록:")
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """))
    tables = result.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    
    # users 테이블이 있는지 확인
    table_names = [t[0] for t in tables]
    if 'users' not in table_names:
        print("\n⚠️  'users' 테이블이 없습니다!")
        print("💡 백엔드가 한 번도 실행되지 않았거나, 테이블 생성에 실패했을 수 있습니다.")
    else:
        # users 테이블 데이터 조회
        print("\n👤 users 테이블 데이터:")
        print("-" * 70)
        result = conn.execute(text("SELECT * FROM users ORDER BY created_at DESC"))
        rows = result.fetchall()
        
        if rows:
            for row in rows:
                print(f"  ID: {row[0]}")
                print(f"  Username: {row[1]}")
                print(f"  Email: {row[2]}")
                print(f"  Password Hash: {row[3][:20]}..." if len(row[3]) > 20 else f"  Password Hash: {row[3]}")
                print(f"  Created At: {row[4]}")
                print("-" * 70)
            print(f"\n✅ 총 {len(rows)}명의 사용자가 있습니다.")
        else:
            print("  ⚠️  users 테이블이 비어있습니다!")
            print("\n💡 확인할 사항:")
            print("  1. 프론트엔드가 올바른 API URL을 사용하는지 확인")
            print("     → https://diary-lux2.onrender.com/api")
            print("  2. 회원가입 시 에러가 발생했는지 브라우저 콘솔 확인")
            print("  3. Render 백엔드 로그 확인")

print("\n" + "=" * 70)
print("🔍 완료!")
print("=" * 70 + "\n")
