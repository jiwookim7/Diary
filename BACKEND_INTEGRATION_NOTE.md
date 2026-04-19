# 백엔드 연동 완전 가이드 (기초부터 실전까지)

## 📋 목차
1. [전체 아키텍처 흐름도](#1-전체-아키텍처-흐름도)
2. [왜 payload 객체가 아닌 개별 파라미터인가?](#2-왜-payload-객체가-아닌-개별-파라미터인가)
3. [백엔드 구조 상세 설명](#3-백엔드-구조-상세-설명)
4. [프론트엔드 API 클라이언트 구조](#4-프론트엔드-api-클라이언트-구조)
5. [데이터 흐름 추적](#5-데이터-흐름-추적)

---

## 1. 전체 아키텍처 흐름도

```
┌─────────────────────────────────────────────────────────────────┐
│                         사용자 브라우저                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  React 컴포넌트 (Signup.jsx / Login.jsx)                  │   │
│  │  ↓                                                        │   │
│  │  signup(username, password) ← 개별 파라미터 전달          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  authApi.js                                               │   │
│  │  { username, password } 객체로 조합                       │   │
│  │  ↓                                                        │   │
│  │  JSON.stringify({ username, password })                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  client.js (공통 HTTP 클라이언트)                          │   │
│  │  fetch("http://localhost:8080/api/signup", {              │   │
│  │    method: "POST",                                        │   │
│  │    headers: { "Content-Type": "application/json" },       │   │
│  │    body: '{"username":"myuser","password":"pass123"}'     │   │
│  │  })                                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                           ↓ HTTP 요청
                    네트워크 (localhost)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI 백엔드 서버                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  CORS Middleware (main.py)                                │   │
│  │  - 출처 검증: http://localhost:5173 허용                  │   │
│  │  - OPTIONS 요청 처리 (Preflight)                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  라우터: @app.post('/api/signup')                         │   │
│  │  payload: SignupCreate ← Pydantic 자동 검증               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Pydantic 스키마 (schemas.py)                             │   │
│  │  class SignupCreate(BaseModel):                           │   │
│  │    username: str = Field(min_length=1, max_length=50)     │   │
│  │    password: str = Field(min_length=1, max_length=255)    │   │
│  │  → 검증 실패 시 422 에러 자동 반환                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  비즈니스 로직 (main.py)                                  │   │
│  │  1. 중복 확인: select(Signup).where(...)                  │   │
│  │  2. 신규 생성: Signup(username=..., password_hash=...)    │   │
│  │  3. DB 저장: db.add(user) → db.commit()                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SQLAlchemy ORM (models.py)                               │   │
│  │  class Signup(Base):                                      │   │
│  │    __tablename__ = 'users'                                │   │
│  │    → SQL 생성: INSERT INTO users ...                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL 데이터베이스                                   │   │
│  │  users 테이블에 데이터 저장                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  응답 생성 (schemas.py)                                   │   │
│  │  LoginResponse(user_id=3, username="myuser", ...)         │   │
│  │  → JSON: {"user_id":3,"username":"myuser","message":...}  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                           ↓ HTTP 응답
┌─────────────────────────────────────────────────────────────────┐
│                         사용자 브라우저                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  client.js → response.json() 파싱                         │   │
│  │  ↓                                                        │   │
│  │  authApi.js → return 데이터                               │   │
│  │  ↓                                                        │   │
│  │  Login.jsx → localStorage.setItem('userId', ...)          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 왜 payload 객체가 아닌 개별 파라미터인가?

### ❓ 질문
```javascript
// 왜 이렇게 하나요?
export async function signup(username, password) {
  return apiRequest('/signup', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

// 이렇게 하면 안되나요?
export async function signup(payload) {
  return apiRequest('/signup', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
```

### ✅ 답변: API 설계의 명확성과 타입 안전성

#### 1️⃣ **함수 인터페이스의 명확성**
```javascript
// ❌ 나쁜 예: 어떤 데이터가 필요한지 불명확
signup({ username: 'user', password: 'pass' })  
signup({ user: 'user', pwd: 'pass' })  // 실수 가능
signup({ name: 'user', password: 'pass' })  // 필드명 오타

// ✅ 좋은 예: 필요한 파라미터가 명확
signup('user', 'pass')  // 순서와 의미가 명확
```

#### 2️⃣ **IDE 자동완성과 에러 검출**
```javascript
// 개별 파라미터: IDE가 정확히 알려줌
signup(
  'myuser',    // ← IDE: "첫 번째 파라미터: username (string)"
  'mypass123'  // ← IDE: "두 번째 파라미터: password (string)"
)

// 객체 파라미터: 내부 구조를 문서나 코드를 봐야 앎
signup({ username: 'myuser', password: 'mypass123' })
```

#### 3️⃣ **실제 사용 예시 비교**

**Signup.jsx에서 호출:**
```javascript
// 현재 방식 (개별 파라미터)
const handleSubmit = async (e) => {
  e.preventDefault();
  const response = await signup(username, password);
  // ↑ username, password는 state 변수로 이미 존재
  // ↑ 별도의 객체 생성 없이 바로 전달
}

// 객체 방식이라면
const handleSubmit = async (e) => {
  e.preventDefault();
  // 객체를 따로 만들어야 함
  const payload = { username, password };
  const response = await signup(payload);
  // ↑ 추가 단계 필요
}
```

#### 4️⃣ **확장성과 유연성**
```javascript
// 개별 파라미터 방식: 선택적 파라미터 추가 용이
export async function signup(username, password, email = null) {
  return apiRequest('/signup', {
    method: 'POST',
    body: JSON.stringify({ username, password, email }),
  });
}

// 호출
signup('user', 'pass')           // email 없이
signup('user', 'pass', 'a@b.c')  // email 포함
```

#### 5️⃣ **보안: 의도하지 않은 데이터 전송 방지**
```javascript
// ❌ 객체 방식: 불필요한 데이터가 함께 전송될 수 있음
const formData = {
  username: 'myuser',
  password: 'mypass',
  creditCard: '1234-5678-9012-3456',  // 실수로 포함됨
  ssn: '123-45-6789'
};
signup(formData);  // 모든 데이터가 서버로 전송됨!

// ✅ 개별 파라미터: 필요한 것만 정확히 전송
signup(formData.username, formData.password);  // 안전
```

### 🔄 데이터 변환 과정

```javascript
// 1단계: 컴포넌트에서 개별 값으로 함수 호출
signup('testuser', 'testpass123')

// 2단계: authApi.js에서 객체로 조합
function signup(username, password) {
  // { username: 'testuser', password: 'testpass123' }
  return apiRequest('/signup', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    //    ↑ '{"username":"testuser","password":"testpass123"}'
  });
}

// 3단계: client.js에서 HTTP 요청
fetch('http://localhost:8080/api/signup', {
  headers: { 'Content-Type': 'application/json' },
  body: '{"username":"testuser","password":"testpass123"}'
  //    ↑ 네트워크로 전송되는 JSON 문자열
})

// 4단계: FastAPI에서 자동 파싱
@app.post('/api/signup')
def signup(payload: SignupCreate, ...):
    # payload.username = 'testuser'
    # payload.password = 'testpass123'
```

---

## 3. 백엔드 구조 상세 설명

### 🗂️ 파일 구조와 역할

```
backend/
├── app/
│   ├── __init__.py       # 패키지 선언
│   ├── main.py           # ⭐ FastAPI 앱, 라우터, 엔드포인트
│   ├── database.py       # 데이터베이스 연결 설정
│   ├── models.py         # SQLAlchemy ORM 모델
│   └── schemas.py        # Pydantic 검증 스키마
├── .env                  # 환경 변수 (DB 주소, CORS)
└── requirements.txt      # Python 패키지 목록
```

---

### 📦 1. Pydantic 스키마 (schemas.py)

**역할:** API 요청/응답 데이터의 검증 및 직렬화

```python
from pydantic import BaseModel, Field

class SignupCreate(BaseModel):
  username: str = Field(min_length=1, max_length=50)
  password: str = Field(min_length=1, max_length=255)
```

**왜 필요한가?**
- **자동 검증**: 클라이언트가 보낸 JSON이 올바른지 자동 확인
- **에러 처리**: 검증 실패 시 422 에러를 자동으로 반환
- **문서화**: FastAPI가 자동으로 OpenAPI 문서 생성

**작동 원리:**
```python
# 클라이언트가 보낸 JSON
{
  "username": "a",       # ✅ 1자 이상 50자 이하 OK
  "password": "test123"  # ✅ 1자 이상 255자 이하 OK
}

# 검증 실패 예시
{
  "username": "",        # ❌ min_length=1 위반
  "password": "test"
}
# → 자동으로 422 에러 반환:
# { "detail": [{"loc": ["body", "username"], "msg": "ensure this value has at least 1 characters"}] }
```

---

### 🗄️ 2. SQLAlchemy ORM 모델 (models.py)

**역할:** Python 클래스를 PostgreSQL 테이블과 매핑

```python
from sqlalchemy.orm import Mapped, mapped_column

class Signup(Base):
  __tablename__ = 'users'  # ← 실제 DB 테이블명
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
  email: Mapped[str | None] = mapped_column(String(100), nullable=True)
  password_hash: Mapped[str] = mapped_column(Text, nullable=False)
  created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
```

**왜 ORM을 사용하는가?**

#### ❌ ORM 없이 SQL 직접 작성
```python
# 복잡하고 에러 발생 가능성 높음
cursor.execute(
  "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
  (username, password)
)
result = cursor.fetchone()
user_id = result[0]

# SQL 인젝션 위험
query = f"SELECT * FROM users WHERE username = '{username}'"  # 위험!
```

#### ✅ ORM 사용
```python
# Python 코드로 간결하게 작성
user = Signup(username="myuser", password_hash="hashed_pw")
db.add(user)
db.commit()
db.refresh(user)  # DB가 생성한 id, created_at 자동 반영
user_id = user.id  # 타입 안전
```

**ORM의 장점:**
1. **SQL 인젝션 방지** (자동 파라미터 바인딩)
2. **타입 안전성** (IDE 자동완성)
3. **데이터베이스 독립성** (PostgreSQL ↔ MySQL 전환 용이)
4. **자동 관계 관리** (외래키, JOIN 등)

---

### 🔍 SQLAlchemy 쿼리 문법: 외우는 게 아니라 패턴이다!

**질문: `db.execute(select(Signup).where(...))` 같은 코드를 어떻게 알아요? 외워야 하나요?**

**답변:** 외우는 게 아니라 **패턴**입니다! SQL과 거의 1:1 매칭됩니다.

#### 📚 기본 패턴 비교: SQL ↔ SQLAlchemy

| SQL | SQLAlchemy ORM | 설명 |
|-----|----------------|------|
| `SELECT * FROM users` | `select(Signup)` | 전체 조회 |
| `WHERE username = 'test'` | `.where(Signup.username == 'test')` | 조건 필터 |
| `WHERE age > 18` | `.where(Signup.age > 18)` | 비교 연산 |
| `WHERE email LIKE '%@gmail.com'` | `.where(Signup.email.like('%@gmail.com'))` | LIKE 검색 |
| `ORDER BY created_at DESC` | `.order_by(Signup.created_at.desc())` | 정렬 |
| `LIMIT 10` | `.limit(10)` | 개수 제한 |
| `INSERT INTO users ...` | `db.add(Signup(...))` | 삽입 |
| `UPDATE users SET ...` | `user.username = 'new'` | 수정 |
| `DELETE FROM users WHERE ...` | `db.delete(user)` | 삭제 |

#### 📖 실전 예제: SQL → SQLAlchemy 변환

##### 예제 1: 단일 사용자 조회
```python
# SQL
SELECT * FROM users WHERE username = 'myuser'

# SQLAlchemy (단계별)
from sqlalchemy import select

# 1단계: select() 함수로 모델 선택
query = select(Signup)
# → SELECT users.id, users.username, users.email, users.password_hash, users.created_at FROM users

# 2단계: where() 메서드로 조건 추가
query = query.where(Signup.username == 'myuser')
# → SELECT ... FROM users WHERE users.username = 'myuser'

# 3단계: 실행 및 결과 가져오기
result = db.execute(query)
# → SQL 실행

user = result.scalar_one_or_none()
# → 결과 1개 또는 None 반환

# 한 줄로 작성
user = db.execute(
  select(Signup).where(Signup.username == 'myuser')
).scalar_one_or_none()
```

##### 예제 2: 여러 조건 조합
```python
# SQL
SELECT * FROM users 
WHERE username = 'myuser' AND password_hash = 'hashed123'

# SQLAlchemy
user = db.execute(
  select(Signup).where(
    Signup.username == 'myuser',      # 콤마로 구분 = AND
    Signup.password_hash == 'hashed123'
  )
).scalar_one_or_none()

# 또는 명시적으로
from sqlalchemy import and_
user = db.execute(
  select(Signup).where(
    and_(
      Signup.username == 'myuser',
      Signup.password_hash == 'hashed123'
    )
  )
).scalar_one_or_none()
```

##### 예제 3: 전체 목록 조회 (정렬)
```python
# SQL
SELECT * FROM posts ORDER BY created_at DESC

# SQLAlchemy
posts = db.execute(
  select(Post).order_by(Post.created_at.desc())
).scalars().all()
# ↑ .scalars() = 객체만 추출 (Row 래퍼 제거)
# ↑ .all() = 리스트로 반환
```

##### 예제 4: 데이터 삽입
```python
# SQL
INSERT INTO users (username, password_hash) 
VALUES ('testuser', 'hashed123')
RETURNING id, created_at

# SQLAlchemy
user = Signup(username='testuser', password_hash='hashed123')
db.add(user)        # 트랜잭션에 추가 (아직 DB에 안 들어감)
db.commit()         # 실제 INSERT 실행
db.refresh(user)    # RETURNING 값 가져오기 (id, created_at)
print(user.id)      # DB가 생성한 ID 출력
```

##### 예제 5: 데이터 수정
```python
# SQL
UPDATE users 
SET username = 'newname' 
WHERE id = 3

# SQLAlchemy
user = db.get(Signup, 3)  # id=3인 사용자 조회
user.username = 'newname'  # 속성 변경
db.commit()                # UPDATE 실행
```

##### 예제 6: 데이터 삭제
```python
# SQL
DELETE FROM users WHERE id = 3

# SQLAlchemy
user = db.get(Signup, 3)  # id=3인 사용자 조회
db.delete(user)           # 삭제 예약
db.commit()               # DELETE 실행
```

#### 🔑 핵심 메서드 정리

##### 1️⃣ **쿼리 빌더**
```python
select(Model)           # SELECT 시작
.where(조건)            # WHERE 절
.order_by(컬럼)         # ORDER BY 절
.limit(개수)            # LIMIT 절
.offset(시작위치)       # OFFSET 절
```

##### 2️⃣ **실행 메서드**
```python
db.execute(query)       # 쿼리 실행

# 결과 가져오기
.scalar_one_or_none()   # 단일 값 또는 None (0개 OK, 2개 이상 에러)
.scalar_one()           # 단일 값 (0개 또는 2개 이상이면 에러)
.scalars().all()        # 리스트 반환 [obj1, obj2, ...]
.scalars().first()      # 첫 번째 객체 또는 None
```

##### 3️⃣ **비교 연산자**
```python
Model.column == 'value'    # 같음 (=)
Model.column != 'value'    # 다름 (!=)
Model.column > 10          # 크다 (>)
Model.column >= 10         # 크거나 같다 (>=)
Model.column < 10          # 작다 (<)
Model.column <= 10         # 작거나 같다 (<=)
Model.column.like('%test%') # LIKE
Model.column.in_([1,2,3])  # IN
Model.column.is_(None)     # IS NULL
Model.column.isnot(None)   # IS NOT NULL
```

##### 4️⃣ **트랜잭션 메서드**
```python
db.add(obj)      # INSERT 예약
db.delete(obj)   # DELETE 예약
db.commit()      # 실제 SQL 실행 (INSERT/UPDATE/DELETE)
db.rollback()    # 변경 사항 취소
db.refresh(obj)  # DB에서 최신 값 다시 읽기
```

#### 🎯 어떻게 배우나?

##### ❌ 외우려고 하지 마세요
```python
# 이런 식으로 외우면 힘듭니다
"select는 조회할 때 쓰고, where는 조건이고..."
```

##### ✅ SQL과 비교하면서 패턴 익히기
```python
# 1. SQL부터 작성
SELECT * FROM users WHERE username = 'test'

# 2. 패턴 매칭
# SELECT * FROM users → select(Signup)
# WHERE username = 'test' → .where(Signup.username == 'test')

# 3. 완성
db.execute(
  select(Signup).where(Signup.username == 'test')
).scalar_one_or_none()
```

#### 📝 자주 사용하는 패턴 치트시트

```python
# ========== 조회 (SELECT) ==========

# 전체 조회
posts = db.execute(select(Post)).scalars().all()

# 조건 조회 (단일)
user = db.execute(
  select(Signup).where(Signup.id == 1)
).scalar_one_or_none()

# 조건 조회 (여러 개)
posts = db.execute(
  select(Post).where(Post.user_id == 3)
).scalars().all()

# 정렬된 조회
posts = db.execute(
  select(Post).order_by(Post.created_at.desc())
).scalars().all()

# 개수 제한
recent_posts = db.execute(
  select(Post).order_by(Post.created_at.desc()).limit(10)
).scalars().all()

# ========== 삽입 (INSERT) ==========

user = Signup(username='test', password_hash='hash')
db.add(user)
db.commit()
db.refresh(user)  # id 등 DB 생성 값 가져오기

# ========== 수정 (UPDATE) ==========

user = db.get(Signup, 1)  # PK로 조회
user.username = 'newname'
db.commit()

# ========== 삭제 (DELETE) ==========

post = db.get(Post, 5)  # PK로 조회
db.delete(post)
db.commit()

# ========== 존재 확인 ==========

exists = db.execute(
  select(Signup).where(Signup.username == 'test')
).scalar_one_or_none() is not None
```

#### 💡 IDE 자동완성 활용

```python
# 1. 모델 타입이 명확하면 IDE가 자동완성 제공
user = db.execute(
  select(Signup).where(Signup.username == 'test')
  #              ↑ Signup. 까지 입력하면
  #                id, username, email, password_hash 등 자동완성
).scalar_one_or_none()

# 2. 메서드 체이닝도 자동완성
select(Post).where(...).order_by(...).limit(...)
#           ↑ . 입력하면 where, order_by, limit 등 제안
```

#### 🔗 공식 문서 참고

- **SQLAlchemy 2.0 튜토리얼**: https://docs.sqlalchemy.org/en/20/tutorial/
- **ORM 쿼리 가이드**: https://docs.sqlalchemy.org/en/20/orm/queryguide/
- **자주 쓰는 연산자**: https://docs.sqlalchemy.org/en/20/core/operators.html

**결론:** 
- ✅ 외우지 않아도 됩니다
- ✅ SQL 패턴을 Python으로 옮긴 것
- ✅ IDE 자동완성 + 공식 문서 활용
- ✅ 자주 쓰다 보면 자연스럽게 익숙해집니다

---

### 🛣️ 3. FastAPI 라우터 (main.py)

**역할:** HTTP 요청을 처리하고 비즈니스 로직 실행

```python
@app.post('/api/signup', response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupCreate, db: Session = Depends(get_db)):
  # 1️⃣ 중복 확인
  existing_user = db.execute(
    select(Signup).where(Signup.username == payload.username)
  ).scalar_one_or_none()
  
  if existing_user:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST, 
      detail='Username already exists'
    )
  
  # 2️⃣ 새 사용자 생성
  user = Signup(
    username=payload.username.strip(),
    password_hash=payload.password.strip()
  )
  
  # 3️⃣ 데이터베이스 저장
  db.add(user)
  db.commit()
  db.refresh(user)  # DB에서 생성된 id, created_at 가져오기
  
  # 4️⃣ 응답 반환
  return LoginResponse(
    user_id=user.id,
    username=user.username,
    message='Signup successful'
  )
```

**단계별 설명:**

#### 1️⃣ 중복 확인
```python
select(Signup).where(Signup.username == payload.username)
# ↓ SQL로 변환
# SELECT users.id, users.username, ... 
# FROM users 
# WHERE users.username = 'myuser'

scalar_one_or_none()
# → 결과가 1개면 반환, 0개면 None, 2개 이상이면 에러
```

#### 2️⃣ ORM 객체 생성
```python
user = Signup(username="myuser", password_hash="hashed_pw")
# 아직 DB에 저장 안 됨 (메모리에만 존재)
# user.id = None (아직 할당 안 됨)
```

#### 3️⃣ 데이터베이스 저장
```python
db.add(user)      # 트랜잭션에 추가
db.commit()       # 실제 DB에 INSERT 실행
db.refresh(user)  # DB에서 생성된 값 (id, created_at) 다시 읽기
# user.id = 3 (DB가 자동 생성한 값)
```

#### 4️⃣ 응답 생성
```python
LoginResponse(user_id=3, username="myuser", message="...")
# Pydantic이 자동으로 JSON 직렬화
# ↓
# {"user_id": 3, "username": "myuser", "message": "Signup successful"}
```

---

### 🔐 4. CORS 설정 (main.py)

**역할:** 다른 도메인(프론트엔드)에서의 API 호출 허용

```python
allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

app.add_middleware(
  CORSMiddleware,
  allow_origins=[origin.strip() for origin in allowed_origins],
  allow_credentials=True,
  allow_methods=['*'],    # GET, POST, DELETE 등 모든 메서드 허용
  allow_headers=['*'],    # Content-Type 등 모든 헤더 허용
)
```

**왜 CORS가 필요한가?**

```
프론트엔드: http://localhost:5173
백엔드:     http://localhost:8080

→ 도메인이 다름 (Same-Origin Policy 위반)
→ 브라우저가 기본적으로 차단
→ CORS 설정으로 명시적 허용 필요
```

**CORS 작동 과정:**

```
1. 브라우저가 Preflight 요청 전송 (OPTIONS 메서드)
   OPTIONS /api/signup HTTP/1.1
   Origin: http://localhost:5173
   Access-Control-Request-Method: POST

2. 서버가 허용 여부 응답
   Access-Control-Allow-Origin: http://localhost:5173
   Access-Control-Allow-Methods: POST, GET, DELETE
   
3. 브라우저가 실제 요청 전송
   POST /api/signup HTTP/1.1
   Origin: http://localhost:5173
```

---

## 4. 프론트엔드 API 클라이언트 구조

### 🏗️ 3계층 구조

```
컴포넌트 (Signup.jsx)
    ↓ signup(username, password)
authApi.js (인증 API)
    ↓ apiRequest(path, options)
client.js (공통 HTTP 클라이언트)
    ↓ fetch()
서버
```

---

### 📁 1. client.js - 공통 HTTP 클라이언트

**역할:** 모든 API 요청의 공통 로직 처리

```javascript
const API_BASE_URL = 
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api";

export const apiRequest = async (path, options = {}) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const message = await parseErrorMessage(response);
    throw new Error(`[${response.status}] ${message}`);
  }

  if (response.status === 204) {
    return null;  // DELETE 요청 등
  }

  return response.json();
};
```

**왜 이렇게 설계했는가?**

#### ✅ DRY 원칙 (Don't Repeat Yourself)
```javascript
// ❌ client.js 없이 매번 반복
fetch('http://localhost:8080/api/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})
.then(res => {
  if (!res.ok) throw new Error('...');
  return res.json();
})

// ✅ client.js로 한 줄에
apiRequest('/signup', { method: 'POST', body: JSON.stringify(data) })
```

#### ✅ 중앙 집중식 에러 처리
```javascript
// 모든 API 요청의 에러를 한 곳에서 처리
if (!response.ok) {
  const message = await parseErrorMessage(response);
  throw new Error(`[${response.status}] ${message}`);
}
```

#### ✅ 환경별 설정 관리
```javascript
// 개발: http://localhost:8080/api
// 운영: https://api.production.com/api
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api";
```

---

### 📁 2. authApi.js - 인증 API

**역할:** 회원가입/로그인 관련 API 호출

```javascript
export async function signup(username, password) {
  return apiRequest('/signup', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function login(username, password) {
  return apiRequest('/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}
```

**왜 authApi.js를 분리했는가?**

#### ✅ 관심사의 분리 (Separation of Concerns)
```
authApi.js   → 인증 관련 (signup, login, logout)
postApi.js   → 게시글 관련 (getPostList, createPost, deletePost)
userApi.js   → 사용자 관련 (getProfile, updateProfile)
```

#### ✅ 테스트 용이성
```javascript
// authApi만 모킹하여 테스트
jest.mock('./api/authApi', () => ({
  signup: jest.fn(() => Promise.resolve({ user_id: 1 }))
}));
```

---

### 🧩 3. 컴포넌트 (Signup.jsx)

```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  
  try {
    await signup(username, password);  // ← authApi.js 호출
    alert('회원가입 완료');
    window.location.hash = '';
  } catch (err) {
    setError(err.message);  // ← client.js에서 생성한 에러 메시지
  }
};
```

---

## 5. 데이터 흐름 추적

### 🔄 회원가입 전체 흐름

```javascript
// ========== 프론트엔드 ==========

// 1️⃣ Signup.jsx
<form onSubmit={handleSubmit}>
  <input value={username} />  // "myuser"
  <input value={password} />  // "pass123"
</form>

const handleSubmit = async (e) => {
  await signup(username, password);
  //           ↓         ↓
}

// 2️⃣ authApi.js
export async function signup(username, password) {
  //                          "myuser"   "pass123"
  
  return apiRequest('/signup', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    //    ↓
    //    '{"username":"myuser","password":"pass123"}'
  });
}

// 3️⃣ client.js
export const apiRequest = async (path, options) => {
  //                             "/signup"
  
  const response = await fetch(`${API_BASE_URL}${path}`, {
    //                           "http://localhost:8080/api" + "/signup"
    //                           = "http://localhost:8080/api/signup"
    
    headers: {
      "Content-Type": "application/json",
    },
    ...options,  // method: "POST", body: '{"username":"myuser",...}'
  });
  
  // HTTP 요청 전송:
  // POST /api/signup HTTP/1.1
  // Host: localhost:8080
  // Content-Type: application/json
  // 
  // {"username":"myuser","password":"pass123"}
}
```

```python
# ========== 백엔드 (FastAPI) ==========

# 4️⃣ CORS Middleware
# - Origin 확인: http://localhost:5173
# - 허용 여부 체크
# - OPTIONS (Preflight) 처리

# 5️⃣ 라우터 매칭
@app.post('/api/signup', ...)
def signup(payload: SignupCreate, ...):
    #      ↑
    #      Pydantic이 자동으로 JSON 파싱 및 검증
    #      payload.username = "myuser"
    #      payload.password = "pass123"

# 6️⃣ 중복 확인 (SQLAlchemy)
existing_user = db.execute(
  select(Signup).where(Signup.username == "myuser")
).scalar_one_or_none()
# ↓ SQL 실행
# SELECT users.id, users.username, ... 
# FROM users 
# WHERE users.username = 'myuser'
# ↓ 결과: None (존재하지 않음)

# 7️⃣ 신규 사용자 생성
user = Signup(username="myuser", password_hash="pass123")
db.add(user)
db.commit()
# ↓ SQL 실행
# INSERT INTO users (username, password_hash, email) 
# VALUES ('myuser', 'pass123', NULL) 
# RETURNING users.id, users.created_at
# ↓ 결과: id=3, created_at='2026-04-11 15:30:00'

db.refresh(user)
# user.id = 3
# user.created_at = datetime(2026, 4, 11, 15, 30, 0)

# 8️⃣ 응답 생성 (Pydantic)
return LoginResponse(
  user_id=3,
  username="myuser",
  message="Signup successful"
)
# ↓ Pydantic이 자동으로 JSON 직렬화
# {"user_id": 3, "username": "myuser", "message": "Signup successful"}
```

```javascript
# ========== 프론트엔드 응답 처리 ==========

# 9️⃣ client.js
const response = await fetch(...);
// response.status = 201
// response.ok = true

return response.json();
// ↓
// { user_id: 3, username: "myuser", message: "Signup successful" }

# 🔟 authApi.js
export async function signup(username, password) {
  return apiRequest('/signup', ...);
  // ↓
  // { user_id: 3, username: "myuser", message: "Signup successful" }
}

# 1️⃣1️⃣ Signup.jsx
const handleSubmit = async (e) => {
  const response = await signup(username, password);
  // response = { user_id: 3, username: "myuser", ... }
  
  alert('회원가입 완료');
  window.location.hash = '';  // 로그인 페이지로 이동
};
```

---

## 📊 핵심 개념 정리

### 1. 왜 개별 파라미터인가?
- ✅ **명확성**: 함수 시그니처만 봐도 필요한 데이터 파악
- ✅ **안전성**: 불필요한 데이터 전송 방지
- ✅ **IDE 지원**: 자동완성, 타입 체크
- ✅ **유지보수**: 변경 사항 추적 용이

### 2. JSON.stringify의 역할
```javascript
{ username: "myuser", password: "pass123" }  // JavaScript 객체 (메모리)
        ↓ JSON.stringify()
'{"username":"myuser","password":"pass123"}'  // JSON 문자열 (네트워크 전송)
```

### 3. Pydantic의 역할
- ✅ 자동 검증 (타입, 길이, 형식)
- ✅ 자동 파싱 (JSON → Python 객체)
- ✅ 자동 직렬화 (Python 객체 → JSON)
- ✅ 자동 문서화 (OpenAPI/Swagger)

### 4. SQLAlchemy ORM의 역할
- ✅ Python 코드로 SQL 작성
- ✅ SQL 인젝션 방지
- ✅ 타입 안전성
- ✅ 데이터베이스 독립성

### 5. CORS의 역할
- ✅ 다른 도메인에서의 API 호출 허용
- ✅ 보안 (허용된 도메인만 접근)

---

## 🎯 실전 팁

### 1. API 경로 설계
```
❌ /signup           (일관성 없음)
❌ /api/api/signup   (중복)
✅ /api/signup       (명확한 접두사)
```

### 2. 에러 처리
```python
# 백엔드: 명확한 에러 메시지
raise HTTPException(
  status_code=400,
  detail='Username already exists'  # ← 프론트에서 바로 표시 가능
)

# 프론트엔드: 사용자 친화적 메시지
catch (err) {
  setError(err.message || '회원가입에 실패했습니다');
}
```

### 3. 환경 변수 활용
```bash
# .env
DATABASE_URL=postgresql://...
CORS_ORIGINS=http://localhost:5173

# .env.production
DATABASE_URL=postgresql://production...
CORS_ORIGINS=https://myapp.com
```

---

## 📖 참고 자료

- FastAPI 공식 문서: https://fastapi.tiangolo.com
- Pydantic 문서: https://docs.pydantic.dev
- SQLAlchemy ORM: https://docs.sqlalchemy.org/en/20/
- MDN CORS: https://developer.mozilla.org/ko/docs/Web/HTTP/CORS
