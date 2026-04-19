# 전체 요청 흐름 노트

이 문서는

- 프론트에서 어떤 코드가 실행되는지
- 그때 데이터가 어떤 값으로 들어 있는지
- 백엔드에서 그 값을 어떻게 받는지
- DB에는 어떤 식으로 저장되는지
- 다시 프론트에는 어떤 형태로 돌아오는지

를 한 번에 이해하기 위한 노트입니다.

목표는 단순 설명이 아니라,

```text
아, 이 코드가 그래서 필요한 거구나
아, 값이 이렇게 바뀌는구나
아, 그래서 프론트와 백엔드가 연결되는구나
```

를 바로 느낄 수 있게 하는 것입니다.

---

## 1) 먼저 전체를 한 줄로 보기

글 저장 버튼을 누르면 전체 흐름은 이렇게 움직입니다.

```text
사용자 입력
-> React 상태 저장
-> createPost 호출
-> apiRequest 호출
-> fetch로 HTTP 요청 전송
-> FastAPI 라우트가 요청 받음
-> Pydantic으로 검증
-> SQLAlchemy ORM 객체 생성
-> PostgreSQL 저장
-> FastAPI가 JSON 응답 생성
-> 프론트가 응답을 JavaScript 객체로 받음
-> 다시 목록 조회
-> 화면 갱신
```

이제 이걸 코드와 실제 값으로 하나씩 보겠습니다.

---

## 2) 예시 데이터 정하기

예시로 사용자가 이런 값을 입력했다고 가정합니다.

- 제목: `오늘의 기록`
- 내용: `FastAPI와 React 연결 흐름을 공부했다.`

이 값이 끝까지 어떻게 바뀌는지 추적합니다.

---

## 3) STEP 1. 사용자가 입력하면 React 상태에 저장됨

파일: `src/App.jsx`

```js
const [title, setTitle] = useState("");
const [content, setContent] = useState("");

<input
  id="title"
  value={title}
  onChange={(event) => setTitle(event.target.value)}
/>

<textarea
  id="content"
  value={content}
  onChange={(event) => setContent(event.target.value)}
/>
```

### 이 코드가 하는 일

- `useState("")`는 빈 문자열 상태를 만듭니다.
- 사용자가 입력하면 `onChange`가 실행됩니다.
- `event.target.value`에 현재 입력값이 들어 있습니다.
- `setTitle(...)`, `setContent(...)`가 상태를 바꿉니다.

### 이 시점의 실제 값

```js
title = "오늘의 기록"
content = "FastAPI와 React 연결 흐름을 공부했다."
```

### 중요한 점

- 아직 백엔드로 안 갔습니다.
- 아직 JSON도 아닙니다.
- 그냥 브라우저 메모리 안에 있는 JavaScript 문자열입니다.

---

## 4) STEP 2. 저장 버튼을 누르면 handleSubmit 실행

파일: `src/App.jsx`

```js
const handleSubmit = async (event) => {
  event.preventDefault();

  if (!title.trim() || !content.trim()) {
    setError("제목과 내용을 입력해 주세요.");
    return;
  }

  setSubmitting(true);
  setError("");

  try {
    await createPost({ title, content });
    setTitle("");
    setContent("");
    await loadPosts();
  } catch (e) {
    setError(e.message);
  } finally {
    setSubmitting(false);
  }
};
```

### 이 코드가 하는 일

- `event.preventDefault()`로 form 기본 새로고침을 막습니다.
- `title.trim()`, `content.trim()`로 빈 입력을 막습니다.
- `await createPost({ title, content })`로 글 저장 요청을 보냅니다.
- 저장 성공 후 입력창을 비웁니다.
- 다시 목록을 읽어와 화면을 최신 상태로 만듭니다.

### 이 시점에 createPost로 넘기는 값

```js
{
  title: "오늘의 기록",
  content: "FastAPI와 React 연결 흐름을 공부했다."
}
```

### 중요한 점

이 값은 JavaScript 객체입니다.

즉:

```text
프론트 상태 -> JavaScript 객체
```

가 된 상태입니다.

---

## 5) STEP 3. postApi.js가 요청 내용을 정리함

파일: `src/api/postApi.js`

```js
export const createPost = (payload) =>
  apiRequest("/posts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
```

### 이 코드가 하는 일

- `payload`를 받아서
- 어느 URL로 보낼지 정하고
- 어떤 method로 보낼지 정하고
- body를 JSON 문자열로 바꿉니다.

### createPost에 들어온 값

```js
payload = {
  title: "오늘의 기록",
  content: "FastAPI와 React 연결 흐름을 공부했다."
}
```

### JSON.stringify 후 값

```js
'{"title":"오늘의 기록","content":"FastAPI와 React 연결 흐름을 공부했다."}'
```

### 최종적으로 apiRequest에 넘기는 값

```js
path = "/posts"

options = {
  method: "POST",
  body: '{"title":"오늘의 기록","content":"FastAPI와 React 연결 흐름을 공부했다."}'
}
```

### 왜 이렇게 하는가

- 프론트는 JavaScript 객체를 그대로 네트워크로 보내지 않습니다.
- HTTP 요청 body에 넣을 수 있는 문자열 형태로 바꿔야 합니다.

즉:

```text
JavaScript 객체 -> JSON 문자열
```

---

## 6) STEP 4. client.js가 실제 HTTP 요청을 보냄

파일: `src/api/client.js`

```js
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
    return null;
  }

  return response.json();
};
```

### 여기서 최종 fetch 옵션은 어떻게 생기나

```js
fetch("http://localhost:8080/api/posts", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: '{"title":"오늘의 기록","content":"FastAPI와 React 연결 흐름을 공부했다."}'
})
```

### 이 코드가 하는 일

- base URL과 path를 합쳐 최종 주소를 만듭니다.
- `Content-Type: application/json` 헤더를 붙입니다.
- `fetch()`로 실제 네트워크 요청을 보냅니다.
- 응답이 돌아올 때까지 `await`로 기다립니다.

### 여기서 각각의 의미

- `method`
  어떤 동작인지
  예: POST = 새 글 생성
- `headers`
  body가 어떤 형식인지 설명
  예: JSON 형식
- `body`
  실제로 보내는 데이터 내용

### 실제 네트워크 요청 모양

```http
POST /api/posts HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{"title":"오늘의 기록","content":"FastAPI와 React 연결 흐름을 공부했다."}
```

### 여기서 왜 await를 쓰는가

- 백엔드 응답은 시간이 걸립니다.
- 네트워크 요청은 즉시 끝나지 않습니다.
- 그래서 `fetch()`는 Promise를 돌려주고, 프론트는 `await`로 기다립니다.

---

## 7) STEP 5. 백엔드 FastAPI가 요청을 받음

파일: `backend/app/main.py`

```py
@app.post('/api/posts', response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
  post = Post(
    user_id=payload.user_id,
    title=payload.title.strip(),
    content=payload.content.strip(),
  )
  db.add(post)
  db.commit()
  db.refresh(post)
  return post
```

### 이 코드가 하는 일

- `POST /api/posts` 요청을 이 함수에 연결합니다.
- 요청 body를 `payload`로 받습니다.
- DB 세션을 `db`로 받습니다.
- `Post(...)` 객체를 만들고 저장합니다.
- 저장된 객체를 다시 반환합니다.

### 여기서 payload에 들어오는 값

프론트에서 보낸 JSON:

```json
{
  "title": "오늘의 기록",
  "content": "FastAPI와 React 연결 흐름을 공부했다."
}
```

백엔드 안에서는 이런 식으로 접근할 수 있습니다.

```py
payload.title == "오늘의 기록"
payload.content == "FastAPI와 React 연결 흐름을 공부했다."
```

### 중요한 점

프론트는 JSON 문자열을 보냈지만,
백엔드는 그것을 그대로 문자열로 쓰지 않습니다.

FastAPI가 먼저 읽어서 Python 객체처럼 다룰 수 있게 바꿉니다.

즉:

```text
JSON 요청 -> Python 객체(payload)
```

---

## 8) STEP 6. schemas.py가 요청값을 검증함

파일: `backend/app/schemas.py`

```py
class PostCreate(BaseModel):
  user_id: int | None = Field(default=None, ge=1)
  title: str = Field(min_length=1, max_length=200)
  content: str = Field(min_length=1)
```

### 이 코드가 하는 일

- `title`이 문자열인지 확인
- 길이가 1 이상 200 이하인지 확인
- `content`가 비어 있지 않은지 확인
- `user_id`가 있으면 정수인지 확인

### 이 검증이 왜 필요한가

예를 들어 이런 값이 오면:

```json
{
  "title": "",
  "content": "본문"
}
```

백엔드는 저장하지 않고 에러를 반환합니다.

즉 `schemas.py`는

```text
잘못된 데이터를 DB에 보내기 전에 막는 역할
```

을 합니다.

---

## 9) STEP 7. database.py가 DB 세션을 준비함

파일: `backend/app/database.py`

```py
DATABASE_URL = os.getenv(
  'DATABASE_URL',
  'postgresql+psycopg2://diary_user:011643030@localhost:5432/diary_db',
)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
```

### 이 코드가 하는 일

- 어떤 PostgreSQL에 연결할지 정합니다.
- 연결 엔진을 만듭니다.
- 요청마다 세션을 하나 열어줍니다.
- 요청이 끝나면 세션을 닫습니다.

### 왜 필요한가

DB 연결을 아무 데서나 직접 열고 닫으면 코드가 금방 복잡해집니다.
그래서 한 곳에서 관리합니다.

즉:

```text
database.py = DB 연결 관리자
```

---

## 10) STEP 8. models.py가 DB row를 Python 객체로 연결함

파일: `backend/app/models.py`

```py
class Post(Base):
  __tablename__ = 'posts'

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
  title: Mapped[str] = mapped_column(String(200), nullable=False)
  content: Mapped[str] = mapped_column(Text, nullable=False)
  created_at: Mapped[DateTime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
  )
  updated_at: Mapped[DateTime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now(),
    nullable=False,
  )
```

### 이 코드가 하는 일

- `posts` 테이블을 Python 클래스 `Post`와 연결합니다.
- `title`은 `posts.title` 컬럼에 대응합니다.
- `content`는 `posts.content` 컬럼에 대응합니다.

### 왜 필요한가

DB에 테이블이 있어도,
Python 코드가 그 구조를 자동으로 이해하는 것은 아닙니다.

그래서 models.py가 있어야 이런 코드가 가능합니다.

```py
post = Post(title="오늘의 기록", content="내용")
```

즉:

```text
DB 테이블 구조를 Python 코드가 이해하게 만드는 파일
```

입니다.

---

## 11) STEP 9. create_post()가 실제 저장용 객체를 만들고 DB에 저장함

다시 `main.py`의 본문을 보면:

```py
post = Post(
  user_id=payload.user_id,
  title=payload.title.strip(),
  content=payload.content.strip(),
)

db.add(post)
db.commit()
db.refresh(post)
return post
```

### 1. Post(...) 생성 시 값

```py
post = Post(
  user_id=None,
  title="오늘의 기록",
  content="FastAPI와 React 연결 흐름을 공부했다."
)
```

이건 아직 DB row가 아닙니다.
그냥 Python ORM 객체입니다.

### 2. db.add(post)

- 이 객체를 저장 대상으로 세션에 등록합니다.

### 3. db.commit()

- 실제로 PostgreSQL에 INSERT가 실행됩니다.

개념적으로는 이런 SQL과 비슷합니다.

```sql
INSERT INTO posts (user_id, title, content)
VALUES (NULL, '오늘의 기록', 'FastAPI와 React 연결 흐름을 공부했다.');
```

### 4. db.refresh(post)

- DB가 자동 생성한 값을 다시 읽어옵니다.
- 예: `id`, `created_at`, `updated_at`

예를 들어 refresh 후에는 이런 느낌입니다.

```py
post.id = 21
post.user_id = None
post.title = "오늘의 기록"
post.content = "FastAPI와 React 연결 흐름을 공부했다."
post.created_at = datetime(...)
post.updated_at = datetime(...)
```

---

## 12) STEP 10. 백엔드가 Python 객체를 JSON 응답으로 바꿈

여기서 백엔드 함수는 그냥 이렇게 끝납니다.

```py
return post
```

그런데 브라우저는 Python 객체를 이해하지 못합니다.

그래서 FastAPI가 `response_model=PostOut`을 보고 응답을 정리합니다.

파일: `backend/app/schemas.py`

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

### 이 코드가 하는 일

- `post.id`를 읽음
- `post.title`을 읽음
- `post.content`를 읽음
- `post.created_at`, `post.updated_at`를 읽음
- 이 값들을 JSON 응답으로 바꿈

### 왜 from_attributes=True가 필요한가

`post`는 dict가 아니라 SQLAlchemy 객체입니다.

즉 이런 식으로 속성으로 값을 읽어야 합니다.

```py
post.id
post.title
post.content
```

그걸 허용하는 설정이 `from_attributes=True`입니다.

### 최종적으로 백엔드가 보내는 JSON 응답

```json
{
  "id": 21,
  "user_id": null,
  "title": "오늘의 기록",
  "content": "FastAPI와 React 연결 흐름을 공부했다.",
  "created_at": "2026-04-11T15:30:00+09:00",
  "updated_at": "2026-04-11T15:30:00+09:00"
}
```

### 여기서 데이터 형태 변화

```text
Python ORM 객체 -> PostOut 기준 정리 -> JSON 응답
```

---

## 13) STEP 11. 프론트는 왜 await로 받는가

백엔드는 `return post`만 했는데,
프론트는 왜 `await createPost(...)`를 할까요?

이유는 프론트가 기다리는 대상이 "서버 함수"가 아니라
"네트워크 응답"이기 때문입니다.

프론트의 실제 코드는 이렇습니다.

```js
const response = await fetch(`${API_BASE_URL}${path}`, {
  headers: {
    "Content-Type": "application/json",
    ...options.headers,
  },
  ...options,
});

return response.json();
```

즉:

- 백엔드는 서버 내부 함수 실행 후 `return`
- 프론트는 네트워크 응답이 올 때까지 `await`

입니다.

둘은 다른 층의 동작이라 모순이 아닙니다.

---

## 14) STEP 12. 프론트가 최종적으로 받는 값

프론트는 `response.json()`을 통해 최종적으로 JavaScript 객체를 받습니다.

즉 프론트 코드 기준으로는 이런 값이 들어옵니다.

```js
{
  id: 21,
  user_id: null,
  title: "오늘의 기록",
  content: "FastAPI와 React 연결 흐름을 공부했다.",
  created_at: "2026-04-11T15:30:00+09:00",
  updated_at: "2026-04-11T15:30:00+09:00"
}
```

이 값을 직접 변수에 받을 수도 있습니다.

```js
const savedPost = await createPost({ title, content });
```

그러면 `savedPost` 안에는 위와 같은 객체가 들어갑니다.

다만 현재 프로젝트는 저장 후 이 값을 직접 붙이기보다,
다시 목록을 읽어오는 구조를 사용합니다.

```js
await createPost({ title, content });
await loadPosts();
```

즉:

- 저장 성공 확인
- 목록 재조회
- 최신 목록으로 화면 갱신

방식입니다.

---

## 15) 한 번에 정리하는 전체 흐름 + 코드 + 값

### 1. 사용자가 입력

```js
setTitle("오늘의 기록");
setContent("FastAPI와 React 연결 흐름을 공부했다.");
```

값:

```js
title = "오늘의 기록"
content = "FastAPI와 React 연결 흐름을 공부했다."
```

### 2. 저장 요청 시작

```js
await createPost({ title, content });
```

값:

```js
{ title: "오늘의 기록", content: "FastAPI와 React 연결 흐름을 공부했다." }
```

### 3. JSON으로 변환

```js
body: JSON.stringify(payload)
```

값:

```js
'{"title":"오늘의 기록","content":"FastAPI와 React 연결 흐름을 공부했다."}'
```

### 4. 백엔드로 HTTP 전송

```js
fetch("http://localhost:8080/api/posts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: '{"title":"오늘의 기록","content":"FastAPI와 React 연결 흐름을 공부했다."}'
})
```

### 5. 백엔드가 payload로 받음

```py
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
```

값:

```py
payload.title == "오늘의 기록"
payload.content == "FastAPI와 React 연결 흐름을 공부했다."
```

### 6. ORM 객체 생성

```py
post = Post(
  user_id=payload.user_id,
  title=payload.title.strip(),
  content=payload.content.strip(),
)
```

값:

```py
Post(title="오늘의 기록", content="FastAPI와 React 연결 흐름을 공부했다.")
```

### 7. DB 저장

```py
db.add(post)
db.commit()
db.refresh(post)
```

값:

```py
post.id = 21
post.created_at = datetime(...)
post.updated_at = datetime(...)
```

### 8. 백엔드 응답 반환

```py
return post
```

FastAPI가 JSON으로 보냄:

```json
{
  "id": 21,
  "user_id": null,
  "title": "오늘의 기록",
  "content": "FastAPI와 React 연결 흐름을 공부했다.",
  "created_at": "2026-04-11T15:30:00+09:00",
  "updated_at": "2026-04-11T15:30:00+09:00"
}
```

### 9. 프론트가 응답 받음

```js
const savedPost = await createPost({ title, content });
```

값:

```js
savedPost = {
  id: 21,
  user_id: null,
  title: "오늘의 기록",
  content: "FastAPI와 React 연결 흐름을 공부했다.",
  created_at: "2026-04-11T15:30:00+09:00",
  updated_at: "2026-04-11T15:30:00+09:00"
}
```

---

## 16) 이 흐름을 이해하면 왜 좋은가

이 흐름을 이해하면 바로 이런 판단이 됩니다.

### 왜 postApi.js가 필요한지 이해됨

- 요청 내용을 모아두는 역할

### 왜 client.js가 필요한지 이해됨

- 실제 HTTP 요청 전송 담당

### 왜 schemas.py가 필요한지 이해됨

- 이상한 값을 저장 전에 막기 때문

### 왜 models.py가 필요한지 이해됨

- DB 테이블을 Python 코드가 이해하게 만들기 때문

### 왜 response_model이 필요한지 이해됨

- 프론트로 나가는 응답 형태를 정리하기 때문

즉 단순히 파일이 많아서 복잡한 게 아니라,
각 파일이 한 역할씩 맡아서 전체 요청을 완성하고 있는 것입니다.

---

## 17) 마지막 한 문장 정리

사용자가 입력한 값은 프론트에서 JavaScript 객체가 되고,
JSON 문자열로 바뀌어 백엔드로 전송되며,
백엔드는 그 값을 Python 객체와 ORM 객체로 바꿔 DB에 저장하고,
저장 결과를 다시 JSON으로 만들어 프론트에 돌려주며,
프론트는 그 JSON을 다시 JavaScript 객체로 받아 화면을 갱신합니다.