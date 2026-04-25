# 📚 일기 앱 개발 학습 노트

> 오늘 배운 것들 - 댓글 기능부터 배포까지

---

## 🎯 전체 흐름 요약

```
1. 댓글 기능 추가 (백엔드 → 프론트엔드)
2. 반응형 대시보드 UI 개선
3. 일기 상세보기 모달 구현
4. Vercel 프론트엔드 배포
5. Render 백엔드 + DB 배포
6. 로컬 데이터 마이그레이션
```

---

## 1️⃣ 댓글 기능 구현

### 📌 핵심 개념
- **관계형 데이터베이스**: 댓글은 게시글과 사용자에 연결됨
- **Foreign Key (외래키)**: 댓글 → 게시글, 댓글 → 사용자 연결

### A. 백엔드 (FastAPI + PostgreSQL)

#### ① 데이터베이스 모델 정의 (`models.py`)
```python
class Comment(Base):
    __tablename__ = 'comments'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey('posts.id'))  # 어떤 글의 댓글인지
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))  # 누가 썼는지
    content: Mapped[str] = mapped_column(Text)  # 댓글 내용
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())  # 작성 시간
```

**핵심 포인트:**
- `ForeignKey`: 다른 테이블의 데이터와 연결
- `post_id`: 이 댓글이 어떤 글에 달렸는지
- `user_id`: 누가 작성했는지

#### ② API 스키마 정의 (`schemas.py`)
```python
# 요청 (Request): 클라이언트 → 서버
class CommentCreate(BaseModel):
    post_id: int  # 필수
    user_id: int  # 필수
    content: str  # 필수

# 응답 (Response): 서버 → 클라이언트
class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime
```

**핵심 포인트:**
- Request: 클라이언트가 보내는 데이터 형식
- Response: 서버가 돌려주는 데이터 형식

#### ③ API 엔드포인트 구현 (`main.py`)
```python
# 특정 글의 댓글 목록 조회
@app.get('/api/posts/{post_id}/comments')
def read_comments(post_id: int, db: Session):
    comments = db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
    ).scalars().all()
    return comments

# 댓글 작성
@app.post('/api/comments')
def create_comment(payload: CommentCreate, db: Session):
    comment = Comment(
        post_id=payload.post_id,
        user_id=payload.user_id,
        content=payload.content
    )
    db.add(comment)
    db.commit()
    return comment

# 댓글 삭제
@app.delete('/api/comments/{comment_id}')
def remove_comment(comment_id: int, db: Session):
    comment = db.get(Comment, comment_id)
    db.delete(comment)
    db.commit()
```

**핵심 포인트:**
- GET: 데이터 조회
- POST: 데이터 생성
- DELETE: 데이터 삭제

### B. 프론트엔드 (React + Vite)

#### ① API 클라이언트 (`commentApi.js`)
```javascript
import { apiRequest } from './client.js';

// 댓글 목록 가져오기
export const getComments = async (postId) => {
  return apiRequest(`/posts/${postId}/comments`, { method: 'GET' });
};

// 댓글 작성
export const createComment = async (commentData) => {
  return apiRequest('/comments', {
    method: 'POST',
    body: JSON.stringify(commentData)
  });
};

// 댓글 삭제
export const deleteComment = async (commentId) => {
  return apiRequest(`/comments/${commentId}`, { method: 'DELETE' });
};
```

**핵심 포인트:**
- `apiRequest`: 공통 HTTP 요청 함수 (fetch를 감싼 것)
- URL 구조: `/posts/{id}/comments` (RESTful 설계)

#### ② 상세보기 컴포넌트 (`PostDetail.jsx`)
```javascript
function PostDetail({ post, onClose, currentUserId }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  
  // 댓글 목록 불러오기
  const loadComments = async () => {
    const data = await getComments(post.id);
    setComments(data);
  };
  
  // 댓글 작성
  const handleSubmitComment = async (e) => {
    e.preventDefault();
    await createComment({
      post_id: post.id,
      user_id: currentUserId,
      content: newComment
    });
    setNewComment('');
    await loadComments();  // 새로고침
  };
  
  // 컴포넌트 로딩 시 댓글 불러오기
  useEffect(() => {
    loadComments();
  }, [post.id]);
}
```

**핵심 포인트:**
- `useState`: 상태 관리 (댓글 목록, 입력값)
- `useEffect`: 컴포넌트 로딩 시 자동 실행
- `async/await`: 비동기 처리

---

## 2️⃣ 반응형 대시보드 UI

### 📌 핵심 개념
- **CSS Grid**: 카드 레이아웃 자동 배치
- **Media Query**: 화면 크기별 다른 스타일
- **반응형 디자인**: 모바일/태블릿/데스크톱 대응

### CSS 핵심 코드
```css
/* 그리드 레이아웃 - 자동으로 카드 배치 */
.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

/* 태블릿 (768px 이하) */
@media (max-width: 768px) {
  .posts-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

/* 모바일 (480px 이하) */
@media (max-width: 480px) {
  .posts-grid {
    grid-template-columns: 1fr;  /* 1열로 변경 */
  }
}
```

**핵심 포인트:**
- `auto-fill`: 공간에 맞게 자동으로 열 개수 조정
- `minmax(300px, 1fr)`: 최소 300px, 최대 가능한 크기
- `@media`: 화면 크기에 따라 다른 스타일 적용

---

## 3️⃣ 배포 (Deployment)

### 📌 핵심 개념
- **프론트엔드**: 정적 파일 (HTML, CSS, JS) → Vercel
- **백엔드**: 서버 프로그램 (Python) → Render
- **데이터베이스**: PostgreSQL → Render

### A. 프론트엔드 배포 (Vercel)

#### ① 배포 흐름
```
로컬 코드 → GitHub → Vercel → 자동 빌드 → 배포 완료
```

#### ② 핵심 파일들

**`.env.production`**: 프로덕션 환경 변수
```bash
VITE_API_BASE_URL=https://diary-lux2.onrender.com/api
```

**`vercel.json`**: Vercel 설정
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

#### ③ 배포 명령어
```bash
vercel --prod
```

**핵심 포인트:**
- GitHub에 push하면 자동 재배포
- 환경 변수는 Vercel 대시보드에서도 설정 가능
- SPA(Single Page Application) 라우팅 처리

### B. 백엔드 배포 (Render)

#### ① 배포 흐름
```
GitHub 저장소 연결 → Render 자동 빌드 → 배포 완료
```

#### ② 핵심 설정

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Python 버전 고정:**
```
runtime.txt: python-3.10.14
```

**환경 변수:**
```
DATABASE_URL=postgresql://...
CORS_ORIGINS=https://diary-rouge.vercel.app
```

**핵심 포인트:**
- `$PORT`: Render가 자동으로 할당하는 포트
- Python 버전 명시 중요 (호환성 문제)
- DATABASE_URL은 Render PostgreSQL에서 복사

### C. 데이터베이스 설정 (Render PostgreSQL)

#### ① 연결 정보
```
Internal Database URL: 
postgresql://user:password@host.render.com/dbname
```

**핵심 포인트:**
- Internal URL: 같은 Render 내부에서 사용
- External URL: 외부에서 연결할 때 사용
- 백엔드는 Internal URL 사용 (더 빠름)

---

## 4️⃣ 데이터 마이그레이션

### 📌 핵심 개념
로컬 PostgreSQL → Render PostgreSQL로 데이터 복사

### 마이그레이션 스크립트 핵심
```python
# 로컬 DB 연결
local_engine = create_engine("postgresql://localhost...")
# Render DB 연결
render_engine = create_engine("postgresql://dpg-xxxx.render.com...")

# 데이터 복사
for user in local_users:
    render_session.add(user)
render_session.commit()
```

**핵심 포인트:**
- 중복 체크: 같은 데이터 두 번 추가 방지
- Foreign Key: 참조하는 데이터가 먼저 있어야 함
- Rollback: 에러 발생 시 이전 상태로 복구

---

## 💰 배포 비용 안내

### Vercel (프론트엔드)
```
✅ 무료:
- Hobby 플랜 (개인 프로젝트)
- 무제한 배포
- 자동 HTTPS
- 글로벌 CDN

💰 유료:
- Pro 플랜: $20/월 (팀 협업 시)
```

### Render (백엔드 + DB)

#### 무료 플랜 (Free Tier)
```
✅ Web Service (백엔드):
- 무료 (750시간/월)
- ⚠️ 15분 미사용 시 슬립 모드
- 슬립 해제: 50초 이상 소요
- 대역폭: 100GB/월

✅ PostgreSQL:
- 무료 (90일간)
- 용량: 1GB
- ⚠️ 90일 후 만료 (데이터 삭제됨)
```

#### 유료 플랜
```
💰 Web Service:
- Starter: $7/월
- Standard: $25/월
- 24시간 작동 (슬립 없음)

💰 PostgreSQL:
- Starter: $7/월
- 영구 사용 가능
- 용량: 1GB → 10GB (플랜별 차이)
```

### 🎯 추천 조합

**개인 학습/포트폴리오:**
```
프론트엔드: Vercel 무료
백엔드: Render 무료 (슬립 모드 감수)
DB: Render 무료 → 90일 후 데이터 백업 후 재생성
```

**실제 서비스:**
```
프론트엔드: Vercel 무료
백엔드: Render Starter ($7/월)
DB: Render Starter ($7/월)
→ 총 $14/월
```

**절약 팁:**
- DB 90일 만료 전 데이터 백업
- 새 DB 생성 후 데이터 복원
- 무료로 계속 사용 가능 (데이터만 옮기면 됨)

---

## 📋 전체 아키텍처 요약

```
[사용자 브라우저]
      ↓
[Vercel 프론트엔드]
      ↓ (HTTPS API 호출)
[Render 백엔드]
      ↓ (데이터 요청)
[Render PostgreSQL]
```

### 데이터 흐름
```
1. 일기 작성 클릭
   → 프론트엔드: 입력 폼 표시
   
2. 저장 버튼 클릭
   → 프론트엔드: POST /api/posts (제목, 내용)
   → 백엔드: DB에 저장
   → 백엔드: 저장된 데이터 반환
   → 프론트엔드: 화면 업데이트

3. 일기 카드 클릭
   → 프론트엔드: 모달 열기
   → 프론트엔드: GET /api/posts/{id}/comments
   → 백엔드: 댓글 목록 조회
   → 프론트엔드: 댓글 표시

4. 댓글 작성
   → 프론트엔드: POST /api/comments
   → 백엔드: DB에 저장
```

---

## 🔑 핵심 용어 정리

### 백엔드 관련
- **API**: 프론트엔드와 백엔드가 소통하는 규칙
- **Endpoint**: API 주소 (예: `/api/posts`)
- **HTTP Method**: GET(조회), POST(생성), DELETE(삭제), PUT(수정)
- **Database**: 데이터를 저장하는 곳
- **Foreign Key**: 다른 테이블과의 연결 고리
- **ORM**: Python 코드로 DB 다루기 (SQLAlchemy)

### 프론트엔드 관련
- **State**: 화면에 표시되는 데이터
- **Props**: 부모 → 자식 컴포넌트로 전달하는 데이터
- **useEffect**: 컴포넌트 로딩 시 실행
- **async/await**: 서버 응답 기다리기
- **Modal**: 팝업 창

### 배포 관련
- **Environment Variable**: 환경별로 다른 설정값
- **Production**: 실제 서비스 환경
- **Development**: 개발 환경 (로컬)
- **Build**: 소스코드 → 배포용 파일 변환
- **Domain**: 웹사이트 주소 (예: diary-rouge.vercel.app)

---

## 📝 다음에 개선할 점

### 보안
- [ ] 비밀번호 해싱 (bcrypt)
- [ ] JWT 토큰 인증
- [ ] HTTPS 적용 (자동 됨)

### 기능
- [ ] 일기 수정 기능
- [ ] 이미지 업로드
- [ ] 검색 기능
- [ ] 태그/카테고리

### 성능
- [ ] 무한 스크롤 (Infinite Scroll)
- [ ] 이미지 최적화
- [ ] 캐싱

---

## 🎓 학습 리소스

### 공식 문서
- **FastAPI**: https://fastapi.tiangolo.com
- **React**: https://react.dev
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Vercel**: https://vercel.com/docs
- **Render**: https://render.com/docs

### 추천 학습 순서
1. JavaScript 기초
2. React 기초 (State, Props, useEffect)
3. HTTP/API 기본 개념
4. Python 기초
5. FastAPI 기본
6. SQL/데이터베이스 기초
7. 배포 개념

---

## ✅ 오늘 배운 것 체크리스트

- [x] 백엔드 모델 정의 (Comment)
- [x] API 엔드포인트 구현 (GET, POST, DELETE)
- [x] 프론트엔드 API 연동
- [x] React 상태 관리 (useState, useEffect)
- [x] 반응형 CSS (Grid, Media Query)
- [x] Vercel 배포
- [x] Render 배포
- [x] PostgreSQL 설정
- [x] 데이터 마이그레이션
- [x] 환경 변수 관리

---

## 🚀 최종 배포 URL

**프론트엔드**: https://diary-rouge.vercel.app
**백엔드 API**: https://diary-lux2.onrender.com/api
**API 문서**: https://diary-lux2.onrender.com/docs

---

**작성일**: 2026년 4월 19일
**프로젝트**: Diary App (일기 앱)
**기술 스택**: React + FastAPI + PostgreSQL
**배포**: Vercel + Render
