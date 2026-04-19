# 이해 중심 노트

## 1) 연결 흐름(왜 이어지는지)

1. 사용자가 화면에서 버튼 클릭
2. src/App.jsx에서 이벤트 함수 실행
3. src/api/postApi.js 호출
   이유: 화면 코드와 API 코드를 분리해서 읽기 쉽게 유지
4. src/api/client.js에서 fetch 실행
   이유: 공통 주소(base URL), 공통 에러 처리를 한 곳에서 처리
5. backend/app/main.py의 /api/posts 라우트가 요청 수신
6. backend/app/schemas.py가 요청 데이터 검증
   이유: 잘못된 입력을 서버 입구에서 차단
7. backend/app/database.py의 세션으로 DB 접근
8. backend/app/models.py 기준으로 posts 테이블 저장/조회
9. FastAPI가 JSON 응답 반환
10. src/App.jsx가 상태 갱신 후 화면 다시 렌더링

한 줄 플로우:
UI(App.jsx) -> postApi.js -> client.js(fetch) -> FastAPI(main.py) -> DB(session/model) -> JSON -> UI 갱신

## 2) 라이브러리 용도(핵심만)

- React: 화면 컴포넌트와 상태 관리
- react-dom: React를 브라우저 DOM에 붙임
- fetch(브라우저 내장): HTTP 요청 전송
- FastAPI: Python API 서버 프레임워크
- Uvicorn: FastAPI 실행 서버(ASGI)
- SQLAlchemy: Python ORM(DB를 클래스처럼 다룸)
- psycopg2-binary: PostgreSQL 드라이버
- Pydantic: 요청/응답 데이터 검증
- python-dotenv: .env 환경변수 로드

## 3) 파일별로 왜 필요한지 + 이 코드가 하는 일

### A. src/main.jsx

- 왜 필요함: React 앱 시작점이기 때문
- 이 코드가 하는 일:
  - root DOM을 찾음
  - App 컴포넌트를 브라우저에 렌더링

### B. src/App.jsx

- 왜 필요함: 사용자와 직접 만나는 화면 파일이기 때문
- 이 코드가 하는 일:
  - 제목, 내용 입력 상태를 저장
  - 저장 버튼 클릭 시 createPost 호출
  - 삭제 버튼 클릭 시 deletePost 호출
  - 처음 열릴 때 목록을 자동 조회
  - 조회 결과를 화면 리스트로 그림

### C. src/api/postApi.js

- 왜 필요함: posts API 호출 코드를 한 곳에 모으기 위해
- 이 코드가 하는 일:
  - getPostList: 목록 조회 요청
  - createPost: 글 작성 요청
  - deletePost: 글 삭제 요청

### D. src/api/client.js

- 왜 필요함: 모든 fetch에서 반복되는 로직을 공통 처리하기 위해
- 이 코드가 하는 일:
  - API 기본 주소를 합쳐서 요청
  - Content-Type 헤더 처리
  - 실패 응답이면 에러 메시지 추출 후 throw
  - 204 응답이면 null 반환
  - 기본 응답은 JSON으로 파싱

### E. backend/app/main.py

- 왜 필요함: FastAPI 라우트와 서버 로직의 중심 파일이기 때문
- 이 코드가 하는 일:
  - 앱 생성 및 CORS 허용
  - 서버 시작 시 테이블 생성 시도
  - GET /api/posts: 목록 조회
  - POST /api/posts: 글 저장
  - DELETE /api/posts/{post_id}: 글 삭제

### F. backend/app/schemas.py

- 왜 필요함: 요청/응답 형태를 고정하고 검증하기 위해
- 이 코드가 하는 일:
  - PostCreate: 입력값(user_id, title, content) 규칙 체크
  - PostOut: 응답 필드(id, user_id, title, content, created_at, updated_at) 정의

### G. backend/app/database.py

- 왜 필요함: DB 연결 정보를 한 곳에서 관리하기 위해
- 이 코드가 하는 일:
  - .env에서 DATABASE_URL 읽기
  - SQLAlchemy engine 생성
  - SessionLocal 생성
  - get_db로 요청 단위 세션 제공/정리

### H. backend/app/models.py

- 왜 필요함: posts 테이블 구조를 코드로 정의하기 위해
- 이 코드가 하는 일:
  - Post 모델을 posts 테이블에 매핑
  - 컬럼 id, user_id, title, content, created_at, updated_at 정의

## 4) 코드 읽는 순서(추천)

1. src/App.jsx (사용자 액션)
2. src/api/postApi.js (어떤 API를 부르는지)
3. src/api/client.js (요청/에러 공통 처리)
4. backend/app/main.py (서버 라우트)
5. backend/app/schemas.py (검증)
6. backend/app/database.py (DB 세션)
7. backend/app/models.py (테이블 구조)

## 5) 실행할 때 체크

1. PostgreSQL 실행
2. backend 실행
3. frontend 실행
4. GET /api/posts 먼저 확인 후 작성/삭제 테스트

## 6) 글 작성(CREATE) 흐름 — 깊이 있는 로직 설명

> 사용자가 제목/내용을 입력하고 "글 저장" 버튼을 누른 순간부터
> 화면에 새 글이 나타나기까지, 데이터가 어떤 형태로 어디를 거치는지 추적합니다.

---

### STEP 1. 사용자가 입력하면 React 상태에 실시간 저장

📍 src/App.jsx

```js
const [title, setTitle] = useState("");
const [content, setContent] = useState("");

<input value={title} onChange={(event) => setTitle(event.target.value)} />
<textarea value={content} onChange={(event) => setContent(event.target.value)} />
```

**내부 동작:**

- `useState("")`는 빈 문자열을 초기값으로 가진 **상태 변수**를 만든다
- 사용자가 키보드를 누를 때마다 `onChange` 이벤트가 발생한다
- `setTitle(event.target.value)`가 호출되면 React는 title 상태를 새 값으로 교체한다
- React는 상태가 바뀌면 **해당 컴포넌트를 다시 렌더링**한다
- 다시 렌더링되면 `value={title}`이 새 값을 반영하므로 input에 글자가 보인다

**이 시점 데이터 형태:**

```
title = "오늘의 일기"     ← JavaScript 문자열 (메모리에만 존재)
content = "날씨가 좋았다"  ← JavaScript 문자열 (메모리에만 존재)
```

---

### STEP 2. 폼 제출 → 브라우저 기본 동작 차단 + 유효성 검사

📍 src/App.jsx

```js
<form onSubmit={handleSubmit}>
  <button type="submit">글 저장</button>
</form>

const handleSubmit = async (event) => {
  event.preventDefault();
  if (!title.trim() || !content.trim()) {
    setError("제목과 내용을 입력해 주세요.");
    return;
  }
  setSubmitting(true);
```

**내부 동작:**

- `<form onSubmit={handleSubmit}>` — 폼 안의 submit 버튼을 누르면 handleSubmit 함수가 실행된다
- `event.preventDefault()` — **이것이 없으면** 브라우저가 페이지를 새로고침한다. form의 기본 동작이 "서버에 GET 요청 후 페이지 이동"이기 때문. React SPA에서는 페이지 이동 없이 JS로 처리하므로 반드시 막아야 한다
- `title.trim()` — 앞뒤 공백을 제거한다. `"   "` 같은 공백만 입력한 경우 빈 문자열 `""` 이 되어 falsy가 된다
- `!title.trim()` — 빈 문자열은 JavaScript에서 **falsy**이므로 `!""` = `true`. 즉 빈 입력이면 에러 메시지 표시 후 **여기서 함수가 끝난다** (return)
- `setSubmitting(true)` — 버튼을 `disabled` 상태로 바꿔서 **사용자가 중복 클릭**하는 것을 방지

**왜 async가 필요한가:**

- 이 함수 안에서 `await createPost(...)`, `await loadPosts()`를 사용한다
- await는 async 함수 안에서만 쓸 수 있다
- await는 "이 비동기 작업이 끝날 때까지 다음 줄로 넘어가지 말고 기다려"라는 뜻이다

---

### STEP 3. API 호출 계층 ① — postApi.js가 요청을 조립

📍 src/api/postApi.js

```js
export const createPost = (payload) =>
  apiRequest("/posts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
```

**내부 동작:**

- App.jsx에서 `await createPost({ title, content })`를 호출했다
- 이때 `payload`는 `{ title: "오늘의 일기", content: "날씨가 좋았다" }` 라는 JS 객체이다
- `JSON.stringify(payload)` — JS 객체를 **JSON 문자열**로 변환한다
- 변환 결과: `'{"title":"오늘의 일기","content":"날씨가 좋았다"}'`
- HTTP 요청의 body에는 문자열만 담을 수 있기 때문에 stringify가 필요하다
- `method: "POST"` — HTTP 메서드를 POST로 지정 (데이터를 "생성"하겠다는 의미)

**왜 이 파일이 분리되어 있는가:**

- App.jsx에 fetch 로직을 직접 쓰면, 같은 API를 다른 화면에서도 쓸 때 코드를 복붙해야 한다
- `postApi.js`에 모아두면 어디서든 `import { createPost }` 한 줄로 사용 가능

**이 시점 데이터 형태:**

```
path = "/posts"
options = {
  method: "POST",
  body: '{"title":"오늘의 일기","content":"날씨가 좋았다"}'  ← JSON 문자열
}
```

---

### STEP 4. API 호출 계층 ② — client.js가 실제 HTTP 요청을 보냄

📍 src/api/client.js

```js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api";

export const apiRequest = async (path, options = {}) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
```

**내부 동작 (한 줄씩):**

1. **URL 조합:** `${API_BASE_URL}${path}` = `"http://localhost:8080/api"` + `"/posts"` = `"http://localhost:8080/api/posts"`
2. **`import.meta.env.VITE_API_BASE_URL`** — Vite가 빌드할 때 `.env.local` 파일의 `VITE_API_BASE_URL` 값을 여기에 주입한다. 없으면 `||` 뒤의 기본값 사용
3. **headers 병합:** `{ "Content-Type": "application/json", ...options.headers }` — Content-Type을 기본으로 넣되, options에 추가 헤더가 있으면 덮어쓴다
4. **`...options`** (스프레드 연산자) — options 객체의 모든 속성(method, body 등)을 풀어서 fetch 옵션에 합친다
5. **`fetch()`** — 브라우저 내장 함수. 실제로 **HTTP 요청을 네트워크로 보낸다.** 이 순간 데이터가 브라우저를 떠나 서버로 향한다
6. **`await`** — fetch는 Promise를 반환한다. 서버 응답이 올 때까지 이 줄에서 대기한다

**이 시점 네트워크에 날아가는 실제 HTTP 요청:**

```
POST /api/posts HTTP/1.1
Host: localhost:8080
Content-Type: application/json
Origin: http://localhost:5173

{"title":"오늘의 일기","content":"날씨가 좋았다"}
```

---

### STEP 5. CORS 검사 — 서버가 요청을 허용하는지 확인

📍 backend/app/main.py

```py
allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
app.add_middleware(
  CORSMiddleware,
  allow_origins=[origin.strip() for origin in allowed_origins],
  allow_methods=['*'],
  allow_headers=['*'],
)
```

**내부 동작:**

- 브라우저는 `localhost:5173`(프론트) → `localhost:8080`(백엔드)으로 요청할 때, **출처(origin)가 다르므로** CORS 정책을 적용한다
- 브라우저가 먼저 **OPTIONS 요청**(preflight)을 보내서 "이 origin에서 POST 해도 됩니까?"라고 묻는다
- FastAPI의 CORSMiddleware가 `allow_origins`에 `http://localhost:5173`이 포함되어 있으므로 "허용"이라고 응답한다
- 그 후에 실제 POST 요청이 전달된다
- **CORS가 없으면:** 브라우저가 응답을 차단한다. 서버는 정상 처리했지만 브라우저가 결과를 JS에게 전달하지 않는다

---

### STEP 6. FastAPI가 요청을 라우트에 매칭

📍 backend/app/main.py

```py
@app.post('/api/posts', response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
```

**내부 동작 (FastAPI가 자동으로 하는 일):**

1. **라우트 매칭:** 요청이 `POST /api/posts`이므로, `@app.post('/api/posts')`가 달린 함수를 찾는다
2. **`payload: PostCreate`** — FastAPI가 요청 body의 JSON을 읽어서 PostCreate **클래스의 인스턴스를 자동 생성**한다. 이것이 의존성 주입(DI)의 한 형태다
3. **`db: Session = Depends(get_db)`** — `Depends`는 FastAPI의 의존성 주입 시스템이다:
   - FastAPI가 `get_db()` 함수를 **자동 호출**한다
   - `get_db()`는 DB 세션을 yield한다
   - 그 세션이 `db` 파라미터로 전달된다
   - 함수 실행이 끝나면 get_db의 `finally` 블록이 실행되어 세션이 닫힌다

---

### STEP 7. Pydantic이 요청 데이터를 검증

📍 backend/app/schemas.py

```py
class PostCreate(BaseModel):
  user_id: int | None = Field(default=None, ge=1)
  title: str = Field(min_length=1, max_length=200)
  content: str = Field(min_length=1)
```

**내부 동작:**

- FastAPI가 JSON body `{"title":"오늘의 일기","content":"날씨가 좋았다"}`를 파싱해서 PostCreate에 넣는다
- Pydantic이 각 필드를 검증한다:
  - `user_id`: JSON에 없으므로 `default=None`이 적용 → `None`
  - `title`: `"오늘의 일기"` — str이고 길이 5 (≥1, ≤200) → 통과
  - `content`: `"날씨가 좋았다"` — str이고 길이 6 (≥1) → 통과
- 검증이 통과하면 PostCreate 인스턴스가 생성된다
- **검증 실패 시:** Pydantic이 자동으로 422 Unprocessable Entity 응답을 반환한다. 함수 본문은 실행되지 않는다

**이 시점 데이터 형태:**

```python
payload = PostCreate(user_id=None, title="오늘의 일기", content="날씨가 좋았다")
# → Python 객체 (Pydantic 모델 인스턴스)
```

---

### STEP 8. get_db()가 DB 세션을 생성해서 넘겨줌

📍 backend/app/database.py

```py
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
  db = SessionLocal()
  try:
    yield db      # ← 여기서 세션을 API 함수에게 넘김
  finally:
    db.close()    # ← API 함수 실행이 끝나면 세션 정리
```

**내부 동작:**

- `create_engine(DATABASE_URL)` — PostgreSQL과의 **연결 풀(pool)**을 만든다. 실제 DB 연결을 미리 여러 개 만들어 놓고 재사용한다
- `pool_pre_ping=True` — 세션을 쓰기 전에 DB에 "살아있니?" 핑을 보낸다. 연결이 끊어졌으면 새 연결을 만든다
- `SessionLocal()` — 풀에서 연결을 하나 빌려와 세션 객체를 만든다
- `yield db` — **이것이 Generator 패턴이다.** yield 전까지 실행하고, db를 호출자에게 넘기고, 호출자가 다 쓰면 yield 다음줄(finally)이 실행된다
- `autoflush=False` — 쿼리 전에 자동으로 DB에 보내지 않는다 (명시적으로 commit할 때만 반영)
- `autocommit=False` — 자동 커밋하지 않는다 (실수로 반영되는 것 방지)

---

### STEP 9. ORM 모델로 Python 객체 → DB 행(row) 변환 후 저장

📍 backend/app/main.py + backend/app/models.py

```py
# main.py — 함수 본문
post = Post(
  user_id=payload.user_id,        # None
  title=payload.title.strip(),    # "오늘의 일기"
  content=payload.content.strip() # "날씨가 좋았다"
)
db.add(post)
db.commit()
db.refresh(post)
return post
```

```py
# models.py — Post 클래스 정의
class Post(Base):
  __tablename__ = 'posts'
  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
  title: Mapped[str] = mapped_column(String(200), nullable=False)
  content: Mapped[str] = mapped_column(Text, nullable=False)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**내부 동작 (한 줄씩):**

1. **`Post(...)`** — Post 클래스는 `Base`를 상속한다. Base는 SQLAlchemy의 선언적 베이스로, 이 클래스가 DB 테이블과 매핑됨을 의미한다. `Post(title="...")`처럼 생성하면 **아직 DB에 저장된 건 아니고**, 메모리에 Python 객체만 만든 것이다

2. **`db.add(post)`** — 이 객체를 세션의 **"추가 대기열"**에 넣는다. 아직 SQL이 실행되지 않는다. SQLAlchemy는 "나중에 이걸 INSERT 해야 해"라고 기억만 한다

3. **`db.commit()`** — **이 순간 실제 SQL이 실행된다:**

   ```sql
   INSERT INTO posts (user_id, title, content, created_at, updated_at)
   VALUES (NULL, '오늘의 일기', '날씨가 좋았다', NOW(), NOW());
   ```

   - `id`는 안 넣었다 → PostgreSQL이 **자동 증가(serial/sequence)**로 값을 생성한다
   - `created_at`, `updated_at`는 `server_default=func.now()` 덕분에 DB 서버 시간이 들어간다
   - commit은 **트랜잭션을 확정**하는 것이다. commit 전에 에러가 나면 아무것도 저장되지 않는다

4. **`db.refresh(post)`** — DB에서 방금 저장된 행을 다시 읽어온다:

   ```sql
   SELECT id, user_id, title, content, created_at, updated_at
   FROM posts WHERE id = 7;
   ```

   - 왜 필요한가? `id`, `created_at`, `updated_at`는 DB가 생성한 값이라 Python 메모리에는 아직 없다. refresh로 DB 값을 가져와서 post 객체에 채운다

5. **`return post`** — FastAPI가 이 Post 객체를 `response_model=PostOut`에 따라 JSON으로 변환한다

**이 시점 데이터 형태:**

```python
post.id = 7                    # DB가 생성한 PK
post.user_id = None
post.title = "오늘의 일기"
post.content = "날씨가 좋았다"
post.created_at = datetime(2026, 4, 10, 15, 30, 0, tzinfo=...)
post.updated_at = datetime(2026, 4, 10, 15, 30, 0, tzinfo=...)
```

---

### STEP 10. PostOut이 Python 객체를 JSON으로 직렬화

📍 backend/app/schemas.py

```py
class PostOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  user_id: int | None
  title: str
  content: str
  created_at: datetime
  updated_at: datetime
```

**내부 동작:**

- `response_model=PostOut`이 지정되어 있으므로, FastAPI가 return된 Post 객체를 PostOut으로 변환한다
- `from_attributes=True` — 이것이 핵심이다. 기본적으로 Pydantic은 **딕셔너리**만 받는다. 하지만 SQLAlchemy 객체는 딕셔너리가 아니라 **클래스 인스턴스**다. `from_attributes=True`를 설정하면 `post.title` 같은 속성 접근 방식으로 값을 읽을 수 있다
- datetime 필드는 Pydantic이 자동으로 ISO 8601 문자열로 변환한다

**FastAPI가 보내는 실제 HTTP 응답:**

```
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 7,
  "user_id": null,
  "title": "오늘의 일기",
  "content": "날씨가 좋았다",
  "created_at": "2026-04-10T15:30:00+09:00",
  "updated_at": "2026-04-10T15:30:00+09:00"
}
```

---

### STEP 11. client.js가 응답을 처리

📍 src/api/client.js

```js
if (!response.ok) {
  const message = await parseErrorMessage(response);
  throw new Error(`[${response.status}] ${message}`);
}

if (response.status === 204) {
  return null;
}

return response.json();
```

**내부 동작:**

- `response.ok` — HTTP 상태코드가 200~299 범위이면 `true`. 201 Created이므로 `true` → 에러 분기를 건너뛴다
- `response.status === 204` — 201이므로 `false` → 건너뛴다
- `response.json()` — 응답 body의 JSON 문자열을 파싱해서 **JavaScript 객체**로 변환한다
- 이 결과가 `apiRequest()`의 반환값이 되고, `postApi.js`의 `createPost()`의 반환값이 되고, `App.jsx`의 `await createPost(...)`의 결과가 된다

**이 시점 데이터 형태 (다시 JS 객체로 돌아옴):**

```js
{
  id: 7,
  user_id: null,
  title: "오늘의 일기",
  content: "날씨가 좋았다",
  created_at: "2026-04-10T15:30:00+09:00",
  updated_at: "2026-04-10T15:30:00+09:00"
}
```

---

### STEP 12. 글 저장 성공 → 입력 초기화 → 목록 다시 불러오기

📍 src/App.jsx

```js
try {
  await createPost({ title, content }); // ← STEP 3~11이 여기서 일어남
  setTitle(""); // 입력 필드 초기화
  setContent("");
  await loadPosts(); // 목록 다시 조회
} catch (e) {
  setError(e.message); // 실패 시 에러 표시
} finally {
  setSubmitting(false); // 버튼 다시 활성화
}
```

**내부 동작:**

- `await createPost(...)` — STEP 3~11 전체가 끝나야 다음 줄로 넘어간다
- `setTitle("")`, `setContent("")` — 입력값을 비운다 (다음 글 작성 준비)
- **`await loadPosts()`** — 이 한 줄이 또 하나의 전체 흐름을 시작한다 (아래 STEP 13)
- `catch (e)` — 위의 어떤 단계에서든 에러가 나면 여기로 온다. 네트워크 오류, 서버 500, 검증 422 등 모두 포함
- `finally` — 성공이든 실패든 무조건 실행. 버튼을 다시 활성화한다

---

### STEP 13. loadPosts()로 전체 목록 갱신

📍 src/App.jsx → src/api/postApi.js → client.js → backend

```js
// App.jsx
const loadPosts = async () => {
  setLoading(true);
  const list = await getPostList(); // GET 요청
  setItems(list); // 상태에 새 목록 저장
  setLoading(false);
};

// postApi.js
export const getPostList = async () => {
  const data = await apiRequest("/posts", { method: "GET" });
  return Array.isArray(data) ? data : [];
};
```

```py
# backend/app/main.py
@app.get('/api/posts', response_model=list[PostOut])
def read_posts(db: Session = Depends(get_db)):
  posts = db.execute(select(Post).order_by(Post.created_at.desc())).scalars().all()
  return posts
```

**내부 동작:**

1. **`GET /api/posts`** 요청이 서버로 간다
2. 서버에서 `select(Post).order_by(Post.created_at.desc())` 실행 → 실제 SQL:
   ```sql
   SELECT id, user_id, title, content, created_at, updated_at
   FROM posts
   ORDER BY created_at DESC;
   ```
3. `.scalars().all()` — 결과를 Post 객체 리스트로 변환
4. `response_model=list[PostOut]` — 각 Post 객체를 PostOut으로 변환해서 JSON 배열로 응답
5. 프론트에서 `setItems(list)` — React 상태가 바뀌면 **컴포넌트가 다시 렌더링**된다
6. `items.map((item) => <li>...)` — 새 목록으로 화면이 갱신된다. 방금 저장한 글이 맨 위에 보인다

---

### STEP 14. React가 화면을 다시 그림 (리렌더링)

📍 src/App.jsx

```js
{
  items.map((item) => (
    <li key={item.id}>
      <h3>{item.title}</h3>
      <p>{item.content}</p>
      <small>{item.created_at}</small>
      <button onClick={() => handleDelete(item.id)}>삭제</button>
    </li>
  ));
}
```

**내부 동작:**

- `setItems(list)`로 상태가 바뀌었으므로 React가 App 컴포넌트를 다시 실행한다
- `items.map(...)` — 새 배열의 각 요소를 순회하며 `<li>` 요소를 생성한다
- `key={item.id}` — React가 **어떤 항목이 추가/삭제/변경**되었는지 효율적으로 파악하기 위한 고유 식별자. key가 없으면 전체 리스트를 다시 그리고, key가 있으면 바뀐 부분만 업데이트한다
- React는 이전 렌더링 결과와 새 결과를 비교(diffing)해서, **실제로 바뀐 DOM 노드만 업데이트**한다 (이것이 Virtual DOM의 핵심)

---

## 7) 글 삭제(DELETE) 흐름 — 깊이 있는 로직 설명

### STEP 1. 삭제 버튼 클릭

📍 src/App.jsx

```js
<button onClick={() => handleDelete(item.id)}>삭제</button>
```

- `() => handleDelete(item.id)` — **화살표 함수로 감싼 이유:** 만약 `onClick={handleDelete(item.id)}`라고 쓰면, 렌더링 시점에 함수가 **즉시 실행**된다. 화살표 함수로 감싸야 "클릭할 때만 실행"된다
- `item.id` — 삭제할 글의 고유 ID (예: 7)

### STEP 2. deletePost API 호출

📍 src/App.jsx → src/api/postApi.js → src/api/client.js

```js
// App.jsx
const handleDelete = async (id) => {
  await deletePost(id);
  await loadPosts();
};

// postApi.js
export const deletePost = (id) =>
  apiRequest(`/posts/${id}`, { method: "DELETE" });
```

- URL이 `/posts/7` 처럼 **ID가 경로에 포함**된다
- `method: "DELETE"` — "이 리소스를 삭제해달라"는 HTTP 메서드

### STEP 3. 서버에서 해당 글을 찾아 삭제

📍 backend/app/main.py

```py
@app.delete('/api/posts/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_post(post_id: int, db: Session = Depends(get_db)):
  post = db.get(Post, post_id)
  if post is None:
    raise HTTPException(status_code=404, detail='Post not found')
  db.delete(post)
  db.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)
```

**내부 동작:**

1. **`{post_id}`** — URL의 `7`을 `post_id` 파라미터로 자동 추출. FastAPI가 `int`로 형변환도 해준다
2. **`db.get(Post, post_id)`** — PK로 조회. 실제 SQL: `SELECT * FROM posts WHERE id = 7`
3. **`if post is None`** — 없는 ID면 404 에러 반환. 클라이언트의 catch에서 잡힌다
4. **`db.delete(post)`** — 삭제 대기열에 넣음. 실제 SQL: `DELETE FROM posts WHERE id = 7`
5. **`db.commit()`** — 트랜잭션 확정. 이 순간 DB에서 행이 사라진다
6. **`204 No Content`** — "성공했지만 보내줄 데이터 없음". body가 비어있다

### STEP 4. 프론트에서 204 응답 처리

📍 src/api/client.js

```js
if (response.status === 204) {
  return null;
}
```

- 204는 body가 없으므로 `response.json()` 하면 에러가 난다
- 그래서 204일 때는 `null`을 반환하고 끝낸다

### STEP 5. 목록 새로고침

- `await loadPosts()` → STEP 13과 동일한 흐름
- 삭제된 글은 DB에 없으므로 목록에서 사라진다

---

## 8) 데이터 형태 변환 요약

```
[글 작성 시 데이터가 변하는 과정]

① React 상태       → JS 문자열    title = "오늘의 일기"
② JSON.stringify   → JSON 문자열  '{"title":"오늘의 일기"}'
③ fetch            → HTTP body    네트워크를 통해 서버로 전송
④ FastAPI 파싱     → Pydantic     PostCreate(title="오늘의 일기")
⑤ ORM 변환        → SQLAlchemy   Post(title="오늘의 일기")
⑥ db.commit()     → SQL          INSERT INTO posts ... VALUES ('오늘의 일기')
⑦ db.refresh()    → SQLAlchemy   Post(id=7, title="오늘의 일기", created_at=...)
⑧ response_model  → JSON 문자열   '{"id":7,"title":"오늘의 일기",...}'
⑨ response.json() → JS 객체      { id: 7, title: "오늘의 일기", ... }
⑩ setItems(list)  → React 상태   화면에 렌더링
```
