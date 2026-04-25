"""
Render PostgreSQL DB 데이터 조회 스크립트
"""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from app.models import Post, Signup, Comment

# Render DB 연결
RENDER_DB = input("Render PostgreSQL URL을 입력하세요: ")
engine = create_engine(RENDER_DB)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("\n" + "=" * 60)
    print("📊 Render PostgreSQL 데이터베이스 조회")
    print("=" * 60)
    
    # 1. 사용자 조회
    print("\n👤 사용자 목록:")
    print("-" * 60)
    users = session.execute(select(Signup)).scalars().all()
    if users:
        for user in users:
            print(f"  ID: {user.id}")
            print(f"  사용자명: {user.username}")
            print(f"  이메일: {user.email or '(없음)'}")
            print(f"  가입일: {user.created_at}")
            print("-" * 60)
        print(f"✅ 총 {len(users)}명의 사용자")
    else:
        print("  ⚠️  사용자 데이터 없음")
    
    # 2. 게시글 조회
    print("\n📝 게시글 목록:")
    print("-" * 60)
    posts = session.execute(select(Post).order_by(Post.created_at.desc())).scalars().all()
    if posts:
        for post in posts:
            print(f"  ID: {post.id}")
            print(f"  작성자 ID: {post.user_id}")
            print(f"  제목: {post.title}")
            print(f"  내용: {post.content[:50]}..." if len(post.content) > 50 else f"  내용: {post.content}")
            print(f"  작성일: {post.created_at}")
            print("-" * 60)
        print(f"✅ 총 {len(posts)}개의 게시글")
    else:
        print("  ⚠️  게시글 데이터 없음")
    
    # 3. 댓글 조회
    print("\n💬 댓글 목록:")
    print("-" * 60)
    try:
        comments = session.execute(select(Comment).order_by(Comment.created_at.desc())).scalars().all()
        if comments:
            for comment in comments:
                print(f"  ID: {comment.id}")
                print(f"  게시글 ID: {comment.post_id}")
                print(f"  작성자 ID: {comment.user_id}")
                print(f"  내용: {comment.content}")
                print(f"  작성일: {comment.created_at}")
                print("-" * 60)
            print(f"✅ 총 {len(comments)}개의 댓글")
        else:
            print("  ⚠️  댓글 데이터 없음")
    except Exception as e:
        print(f"  ⚠️  댓글 테이블 조회 실패: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 조회 완료!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 에러 발생: {e}")
finally:
    session.close()
