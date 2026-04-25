"""
Render DB → 로컬 DB 백업 스크립트
클라우드 데이터를 내 컴퓨터에도 백업!
"""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from app.models import Post, Signup, Comment
from app.database import Base

# Render DB (클라우드)
RENDER_DB = "postgresql://diary_user:sOTdNYyoI5fTmOP9If60VXDtFBwwfUO0@dpg-d7ij40vlk1mc739v7sp0-a.singapore-postgres.render.com/diary_db_4x2d"

# 로컬 DB (내 컴퓨터)
LOCAL_DB = "postgresql+psycopg2://diary_user:011643030@localhost:5432/diary_db"

render_engine = create_engine(RENDER_DB)
local_engine = create_engine(LOCAL_DB)

RenderSession = sessionmaker(bind=render_engine)
LocalSession = sessionmaker(bind=local_engine)

# 로컬 DB 테이블 생성
Base.metadata.create_all(bind=local_engine)

def backup_to_local():
    """클라우드 → 로컬 백업"""
    render_session = RenderSession()
    local_session = LocalSession()
    
    try:
        print("\n" + "=" * 70)
        print("💾 Render DB → 로컬 DB 백업 시작")
        print("=" * 70)
        
        # 1. 사용자 백업
        print("\n👤 사용자 데이터 백업 중...")
        users = render_session.execute(select(Signup)).scalars().all()
        user_count = 0
        
        for user in users:
            existing = local_session.execute(
                select(Signup).where(Signup.username == user.username)
            ).scalar_one_or_none()
            
            if not existing:
                new_user = Signup(
                    username=user.username,
                    email=user.email,
                    password_hash=user.password_hash,
                    created_at=user.created_at
                )
                local_session.add(new_user)
                user_count += 1
                print(f"  ✅ '{user.username}' 백업 완료")
            else:
                # 업데이트
                existing.password_hash = user.password_hash
                existing.email = user.email
                print(f"  🔄 '{user.username}' 업데이트됨")
        
        local_session.commit()
        print(f"✅ {user_count}명의 새로운 사용자 백업 완료")
        
        # 2. 게시글 백업
        print("\n📝 게시글 데이터 백업 중...")
        posts = render_session.execute(select(Post)).scalars().all()
        post_count = 0
        
        for post in posts:
            existing = local_session.execute(
                select(Post).where(
                    Post.title == post.title,
                    Post.content == post.content,
                    Post.user_id == post.user_id
                )
            ).scalar_one_or_none()
            
            if not existing:
                new_post = Post(
                    user_id=post.user_id,
                    title=post.title,
                    content=post.content,
                    created_at=post.created_at,
                    updated_at=post.updated_at
                )
                local_session.add(new_post)
                post_count += 1
                print(f"  ✅ '{post.title[:30]}...' 백업 완료")
        
        local_session.commit()
        print(f"✅ {post_count}개의 새로운 게시글 백업 완료")
        
        # 3. 댓글 백업
        print("\n💬 댓글 데이터 백업 중...")
        comments = render_session.execute(select(Comment)).scalars().all()
        comment_count = 0
        
        for comment in comments:
            try:
                existing = local_session.execute(
                    select(Comment).where(
                        Comment.post_id == comment.post_id,
                        Comment.user_id == comment.user_id,
                        Comment.content == comment.content
                    )
                ).scalar_one_or_none()
                
                if not existing:
                    new_comment = Comment(
                        post_id=comment.post_id,
                        user_id=comment.user_id,
                        content=comment.content,
                        created_at=comment.created_at
                    )
                    local_session.add(new_comment)
                    comment_count += 1
                    print(f"  ✅ 댓글 백업 완료")
            except Exception as e:
                print(f"  ⚠️ 댓글 백업 실패: {e}")
                continue
        
        local_session.commit()
        print(f"✅ {comment_count}개의 새로운 댓글 백업 완료")
        
        print("\n" + "=" * 70)
        print("🎉 백업 완료!")
        print(f"총 {user_count}명 사용자, {post_count}개 게시글, {comment_count}개 댓글")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        local_session.rollback()
    finally:
        render_session.close()
        local_session.close()

if __name__ == "__main__":
    print("\n💡 이 스크립트는 Render DB를 로컬 컴퓨터에 백업합니다.")
    print("💡 정기적으로 실행하면 데이터를 안전하게 보관할 수 있습니다.\n")
    
    response = input("백업을 시작하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        backup_to_local()
    else:
        print("백업이 취소되었습니다.")
