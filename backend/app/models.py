from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func #SQLAlchemy 컬럼 타입과 함수
from sqlalchemy.orm import Mapped, mapped_column #SQLAlchemy ORM 매핑용 타입과 컬럼 정의 함수

from .database import Base #ORM 모델 베이스 클래스

class Signup(Base):
  __tablename__ = 'users'

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
  email: Mapped[str | None] = mapped_column(String(100), nullable=True)
  password_hash: Mapped[str] = mapped_column(Text, nullable=False)
  created_at: Mapped[DateTime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
  )


# PostgreSQL의 posts 테이블과 매핑되는 ORM 모델
class Post(Base):
  # 실제 DB 테이블 이름
  __tablename__ = 'posts'

  # PK(기본키)
  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) #자동 증가하는 정수형 PK, 인덱스 생성
  # 작성자 ID(users.id를 참조, 현재는 null 허용)
  user_id: Mapped[int | None] = mapped_column(Integer, nullable=True) #참조 무결성은 나중에 회원 기능 붙일 때 설정, 현재는 null 허용
  # 글 제목(필수, 최대 200자)
  title: Mapped[str] = mapped_column(String(200), nullable=False) #최대 200자, null 불허
  # 글 본문(필수)
  content: Mapped[str] = mapped_column(Text, nullable=False) #길이 제한 없는 텍스트, null 불허
  # 생성 시각(기본값: DB 현재 시간)
  created_at: Mapped[DateTime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
  )# 생성 시각은 DB의 현재 시간으로 자동 설정, null 불허
  # 수정 시각(생성 시 now, UPDATE 시 now로 갱신)
  updated_at: Mapped[DateTime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now(),
    nullable=False,
  )# 수정 시각은 생성 시 now, UPDATE 시 now로 자동 갱신, null 불허


# PostgreSQL의 comments 테이블과 매핑되는 ORM 모델
class Comment(Base):
  __tablename__ = 'comments'

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  post_id: Mapped[int] = mapped_column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
  content: Mapped[str] = mapped_column(Text, nullable=False)
  created_at: Mapped[DateTime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
  )
