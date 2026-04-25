"""
로컬 DB 데이터를 Render PostgreSQL로 복사하는 스크립트
"""
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# 로컬 DB 연결
LOCAL_DB = "postgresql+psycopg2://diary_user:011643030@localhost:5432/diary_db"
local_engine = create_engine(LOCAL_DB)
LocalSession = sessionmaker(bind=local_engine)

# Render DB 연결 (Render 대시보드에서 Internal Database URL 복사)
RENDER_DB = input("Render PostgreSQL Internal Database URL을 입력하세요: ")
render_engine = create_engine(RENDER_DB)
RenderSession = sessionmaker(bind=render_engine)

# 모델 import
import sys
sys.path.insert(0, os.path.dirname(__file__))
from app.models import Post, Signup, Comment
from app.database import Base

# Render DB에 테이블 생성
Base.metadata.create_all(bind=render_engine)

def migrate_data():
    local_session = LocalSession()
    render_session = RenderSession()
    
    try:
        print("🔄 데이터 마이그레이션 시작...")
        
        # 1. 사용자 데이터 복사
        print("\n1️⃣ 사용자 데이터 복사 중...")
        users = local_session.execute(select(Signup)).scalars().all()
        user_count = 0
        for user in users:
            try:
                # 이미 존재하는 사용자인지 확인
                existing = render_session.execute(
                    select(Signup).where(Signup.username == user.username)
                ).scalar_one_or_none()
                
                if existing:
                    print(f"  ⏭️  사용자 '{user.username}' 이미 존재 (건너뜀)")
                    continue
                
                new_user = Signup(
                    username=user.username,
                    email=user.email,
                    password_hash=user.password_hash,
                    created_at=user.created_at
                )
                render_session.add(new_user)
                render_session.commit()
                user_count += 1
                print(f"  ✅ 사용자 '{user.username}' 추가 완료")
            except Exception as e:
                print(f"  ⚠️  사용자 '{user.username}' 추가 실패: {e}")
                render_session.rollback()
        
        print(f"✅ {user_count}명의 사용자 복사 완료")
        
        # 2. 게시글 데이터 복사
        print("\n2️⃣ 게시글 데이터 복사 중...")
        posts = local_session.execute(select(Post)).scalars().all()
        post_count = 0
        for post in posts:
            try:
                # 이미 존재하는 게시글인지 확인
                existing = render_session.execute(
                    select(Post).where(
                        Post.title == post.title,
                        Post.content == post.content,
                        Post.created_at == post.created_at
                    )
                ).scalar_one_or_none()
                
                if existing:
                    print(f"  ⏭️  게시글 '{post.title[:20]}...' 이미 존재 (건너뜀)")
                    continue
                
                new_post = Post(
                    user_id=post.user_id,
                    title=post.title,
                    content=post.content,
                    created_at=post.created_at,
                    updated_at=post.updated_at
                )
                render_session.add(new_post)
                render_session.commit()
                post_count += 1
                print(f"  ✅ 게시글 '{post.title[:20]}...' 추가 완료")
            except Exception as e:
                print(f"  ⚠️  게시글 추가 실패: {e}")
                render_session.rollback()
        
        print(f"✅ {post_count}개의 게시글 복사 완료")
        
        # 3. 댓글 데이터 복사 (있는 경우)
        print("\n3️⃣ 댓글 데이터 복사 중...")
        try:
            comments = local_session.execute(select(Comment)).scalars().all()
            comment_count = 0
            for comment in comments:
                try:
                    existing = render_session.execute(
                        select(Comment).where(
                            Comment.post_id == comment.post_id,
                            Comment.content == comment.content,
                            Comment.created_at == comment.created_at
                        )
                    ).scalar_one_or_none()
                    
                    if existing:
                        print(f"  ⏭️  댓글 이미 존재 (건너뜀)")
                        continue
                    
                    new_comment = Comment(
                        post_id=comment.post_id,
                        user_id=comment.user_id,
                        content=comment.content,
                        created_at=comment.created_at
                    )
                    render_session.add(new_comment)
                    render_session.commit()
                    comment_count += 1
                    print(f"  ✅ 댓글 추가 완료")
                except Exception as e:
                    print(f"  ⚠️  댓글 추가 실패: {e}")
                    render_session.rollback()
            
            print(f"✅ {comment_count}개의 댓글 복사 완료")
        except Exception as e:
            print(f"⚠️ 댓글 테이블이 없거나 댓글이 없습니다: {e}")
        
        print("\n🎉 모든 데이터 마이그레이션 완료!")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        render_session.rollback()
    finally:
        local_session.close()
        render_session.close()

if __name__ == "__main__":
    print("=" * 50)
    print("로컬 DB → Render PostgreSQL 데이터 마이그레이션")
    print("=" * 50)
    migrate_data()
