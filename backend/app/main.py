import os

from dotenv import load_dotenv #.env 파일에서 환경변수 로드
from fastapi import Depends, FastAPI, HTTPException, Response, status #FastAPI 관련 모듈
from fastapi.middleware.cors import CORSMiddleware #CORS 설정을 위한 미들웨어
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Comment, Post, Signup
from .schemas import CommentCreate, CommentOut, LoginRequest, LoginResponse, PostCreate, PostOut, SignupCreate

# .env 로드(DB 주소, CORS 주소 등)
load_dotenv()

# FastAPI 애플리케이션 생성
app = FastAPI(title='Post API', version='1.0.0')

# 프론트(React)에서 요청할 수 있도록 허용할 출처 목록
allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
app.add_middleware(
  CORSMiddleware,
  allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)


# 서버 시작 시 테이블이 없으면 자동 생성
@app.on_event('startup')
def on_startup():
  Base.metadata.create_all(bind=engine)


# 글 목록 조회 API
@app.get('/api/posts', response_model=list[PostOut])
def read_posts(db: Session = Depends(get_db)):
  # created_at 내림차순(최신 글 먼저)
  posts = db.execute(select(Post).order_by(Post.created_at.desc())).scalars().all()
  return posts


# 글 작성 API
@app.post('/api/posts', response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
  # 요청 바디에서 받은 user_id/제목/내용으로 ORM 객체 생성
  post = Post(
    user_id=payload.user_id,
    title=payload.title.strip(),
    content=payload.content.strip(),
  )
  db.add(post)
  db.commit()
  # DB에 저장된 최신 값(id, created_at) 반영
  db.refresh(post)
  return post

# 회원가입 API
@app.post('/api/signup', response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupCreate, db: Session = Depends(get_db)):
  # 이미 존재하는 사용자명인지 확인
  existing_user = db.execute(select(Signup).where(Signup.username == payload.username)).scalar_one_or_none()
  if existing_user:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username already exists')

  # 새로운 사용자 생성
  user = Signup(username=payload.username.strip(), password_hash=payload.password.strip())
  db.add(user)
  db.commit()
  db.refresh(user)
  return LoginResponse(user_id=user.id, username=user.username, message='Signup successful')


# 로그인 API
@app.post('/api/login', response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
  # 사용자 존재 여부 확인
  user = db.execute(
    select(Signup).where(
      Signup.username == payload.username,
      Signup.password_hash == payload.password
    )
  ).scalar_one_or_none()
  
  if not user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')
  
  return LoginResponse(user_id=user.id, username=user.username, message='Login successful') 


# 글 삭제 API
@app.delete('/api/posts/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_post(post_id: int, db: Session = Depends(get_db)):
  # PK로 대상 글 조회
  post = db.get(Post, post_id)
  if post is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Post not found')

  db.delete(post)
  db.commit()
  # 204: 성공했지만 바디 없음
  return Response(status_code=status.HTTP_204_NO_CONTENT)


# 특정 글의 댓글 목록 조회 API
@app.get('/api/posts/{post_id}/comments', response_model=list[CommentOut])
def read_comments(post_id: int, db: Session = Depends(get_db)):
  # 글이 존재하는지 확인
  post = db.get(Post, post_id)
  if post is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Post not found')
  
  # 해당 글의 댓글 조회 (오래된 순)
  comments = db.execute(
    select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc())
  ).scalars().all()
  return comments


# 댓글 작성 API
@app.post('/api/comments', response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db)):
  # 글이 존재하는지 확인
  post = db.get(Post, payload.post_id)
  if post is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Post not found')
  
  # 댓글 생성
  comment = Comment(
    post_id=payload.post_id,
    user_id=payload.user_id,
    content=payload.content.strip(),
  )
  db.add(comment)
  db.commit()
  db.refresh(comment)
  return comment


# 댓글 삭제 API
@app.delete('/api/comments/{comment_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_comment(comment_id: int, db: Session = Depends(get_db)):
  comment = db.get(Comment, comment_id)
  if comment is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Comment not found')
  
  db.delete(comment)
  db.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)
