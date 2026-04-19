import os

from dotenv import load_dotenv #.env 파일에서 환경변수 로드
from sqlalchemy import create_engine #SQLAlchemy 엔진 생성 함수
from sqlalchemy.orm import declarative_base, sessionmaker #ORM 모델 베이스 클래스, 세션 팩토리 생성 함수

# .env 파일의 환경변수를 현재 프로세스에 로드
load_dotenv()

# DATABASE_URL이 있으면 사용, 없으면 기본 로컬 PostgreSQL 주소 사용
DATABASE_URL = os.getenv(
  'DATABASE_URL',
  'postgresql+psycopg2://diary_user:011643030@localhost:5432/diary_db',
)

# SQLAlchemy 엔진(실제 DB 연결 객체)
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
# 요청마다 사용할 세션 팩토리
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
# ORM 모델 클래스들이 상속할 베이스 클래스
Base = declarative_base()


# FastAPI 의존성 주입에서 사용하는 DB 세션 제공 함수
def get_db():
  db = SessionLocal()
  try:
    # API 함수에서 이 세션을 사용
    yield db
  finally:
    # 요청 처리가 끝나면 세션 정리
    db.close()
