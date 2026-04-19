from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# POST /api/posts 요청 바디 검증용 스키마
class PostCreate(BaseModel):
  # user_id는 선택값(회원 기능 붙일 때 사용)
  user_id: int | None = Field(default=None, ge=1) # 1 이상의 정수 또는 None
  # 최소 1자, 최대 200자
  title: str = Field(min_length=1, max_length=200) 
  # 최소 1자
  content: str = Field(min_length=1)

# 회원가입 요청 바디 검증용 스키마
class SignupCreate(BaseModel):
  username: str = Field(min_length=1, max_length=50) # 최소 1자, 최대 50자
  password: str = Field(min_length=1, max_length=255) # 최소 1자, 최대 255자


# 로그인 요청 바디 검증용 스키마
class LoginRequest(BaseModel):
  username: str = Field(min_length=1, max_length=50)
  password: str = Field(min_length=1, max_length=255)


# 로그인 응답 스키마
class LoginResponse(BaseModel):
  user_id: int
  username: str
  message: str


# API 응답 형식 정의용 스키마
class PostOut(BaseModel):
  # SQLAlchemy 모델 객체를 바로 변환 가능하게 설정
  model_config = ConfigDict(from_attributes=True)

  id: int
  user_id: int | None
  title: str
  content: str
  created_at: datetime
  updated_at: datetime


# 댓글 생성 요청 스키마
class CommentCreate(BaseModel):
  post_id: int = Field(ge=1)
  user_id: int = Field(ge=1)
  content: str = Field(min_length=1)


# 댓글 응답 스키마
class CommentOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  post_id: int
  user_id: int
  content: str
  created_at: datetime
