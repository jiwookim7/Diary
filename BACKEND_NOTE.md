# 백엔드 집중 노트

이 문서는 백엔드만 따로 집중해서 설명합니다.

특히 아래 내용을 기초부터 다룹니다.

- 프론트가 보낸 데이터가 백엔드에 어떻게 들어오는지
- 백엔드가 그 데이터를 어떤 순서로 받는지
- 검증은 어디서 하는지
- DB는 어떤 식으로 연결되는지
- 저장은 어떤 코드가 하는지
- 백엔드가 어떤 데이터를 다시 프론트에 돌려주는지

즉 이 문서는
"백엔드 입장에서 요청을 받았을 때 무슨 일이 일어나는가"
를 이해하기 위한 노트입니다.

---

## 1) 먼저 아주 크게 보기

프론트에서 글 저장 요청을 보내면 백엔드에서는 아래 순서가 일어납니다.

```text
1. HTTP 요청이 들어옴
2. FastAPI가 URL과 method를 보고 어떤 함수가 처리할지 찾음
3. 요청 body(JSON)를 읽음
4. Pydantic schema로 데이터 검증
5. DB 세션을 준비함
6. ORM 모델 객체를 만듦
7. DB에 저장(commit)
8. 저장된 결과를 다시 읽음(refresh)
9. 응답 schema에 맞춰 JSON으로 변환
10. 프론트로 응답 반환
```

즉 백엔드는 단순히 "받아서 저장"만 하는 것이 아닙니다.

- 요청 분기
- 데이터 검증
- DB 연결 관리
- 저장
- 응답 직렬화

이 과정을 다 담당합니다.

---

## 2) 백엔드 파일 맵

지금 백엔드 핵심 파일은 4개입니다.

```text
backend/app/main.py
backend/app/schemas.py
backend/app/database.py
backend/app/models.py
```

각 역할은 이렇습니다.

### main.py

- FastAPI 앱 생성
- 어떤 URL 요청을 어떤 함수가 처리할지 등록
- 실제 요청 처리 함수 작성

즉:

```text
백엔드의 진입점 + 관제실
```

### schemas.py

- 요청 데이터 검증
- 응답 데이터 형식 정의

즉:

```text
백엔드의 입력/출력 규칙서
```

### database.py

- PostgreSQL 연결 설정
- 세션 생성
- 요청마다 세션 열고 닫기

즉:

```text
백엔드의 DB 연결 관리자
```

### models.py

- posts 테이블을 Python 클래스로 매핑
- SQLAlchemy가 DB를 객체처럼 다룰 수 있게 함

즉:

```text
백엔드와 DB를 이어주는 번역기
```

---

## 3) 프론트에서 백엔드로 요청이 오는 시작점

프론트에서는 결국 이런 요청을 보냅니다.

```js
apiRequest("/posts", {
  method: "POST",
  body: JSON.stringify({
    title: "오늘의 기록",
    content: "백엔드 흐름을 공부했다."
  })
})
```

이 요청은 실제로는 이런 HTTP 요청이 됩니다.

```http
POST /api/posts HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{"title":"오늘의 기록","content":"백엔드 흐름을 공부했다."}
```

중요:

- 프론트는 DB에 직접 접근하지 않습니다.
- 프론트는 백엔드 API로 요청을 보냅니다.
- DB는 백엔드만 접근합니다.

즉 구조는 항상 이겁니다.

```text
프론트 -> 백엔드 -> DB
```

절대로

```text
프론트 -> DB
```

가 아닙니다.

---

## 4) STEP 1. FastAPI가 요청을 받아서 함수에 연결함

`main.py`의 핵심 코드는 이 부분입니다.

```py
@app.post('/api/posts', response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
```

이 한 줄을 아주 기초부터 해석하면:

### `@app.post('/api/posts')`

- `POST /api/posts` 요청이 오면
- 아래의 `create_post()` 함수를 실행하라는 뜻입니다.

즉 URL과 method를 보고 함수가 정해집니다.

예:

- `GET /api/posts` -> `read_posts()`
- `POST /api/posts` -> `create_post()`
- `DELETE /api/posts/{post_id}` -> `remove_post()`

이걸 라우팅이라고 봐도 됩니다.

---

## 5) STEP 2. 요청 body를 payload로 받음

함수 선언을 다시 보면:

```py
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
```

여기서 `payload: PostCreate`가 중요합니다.

프론트에서 body로 보낸 JSON:

```json
{
  "title": "오늘의 기록",
  "content": "백엔드 흐름을 공부했다."
}
```

FastAPI는 이것을 읽어서 `payload`라는 Python 객체처럼 넘깁니다.

즉 백엔드 안에서는 이런 식으로 쓸 수 있습니다.

```py
payload.title
payload.content
```

이 말은:

```text
JSON 문자열을 Python 코드가 다룰 수 있는 객체로 바꿨다
```

라는 뜻입니다.

---

## 6) STEP 3. schemas.py가 요청 데이터를 검증함

`payload`가 그냥 아무 객체가 아니라 `PostCreate`라는 규칙을 따릅니다.

코드는 이렇습니다.

```py
class PostCreate(BaseModel):
  user_id: int | None = Field(default=None, ge=1)
  title: str = Field(min_length=1, max_length=200)
  content: str = Field(min_length=1)
```

이 코드가 하는 일:

- `title`이 문자열인지 확인
- `title` 길이가 1 이상 200 이하인지 확인
- `content`가 비어 있지 않은지 확인
- `user_id`가 있으면 정수인지, 1 이상인지 확인

예를 들어 프론트가 이런 잘못된 요청을 보내면:

```json
{
  "title": "",
  "content": "본문"
}
```

백엔드는 DB 저장 단계로 가지 않고 여기서 막습니다.

즉 schemas.py의 역할은:

```text
입구에서 이상한 데이터를 걸러내는 것
```

입니다.

---

## 7) STEP 4. DB 세션을 자동으로 준비함

함수 선언의 두 번째 중요한 부분은 이것입니다.

```py
db: Session = Depends(get_db)
```

이건 FastAPI에게 이런 뜻으로 말하는 것입니다.

```text
이 함수가 실행될 때 DB 세션 하나 준비해서 db에 넣어줘
```

실제로 `database.py`에는 이렇게 되어 있습니다.

```py
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
```

한 줄씩 보면:

### `engine`

- PostgreSQL과 연결할 큰 설정 객체입니다.
- 실제 DB 연결의 기반이 됩니다.

### `SessionLocal`

- 요청마다 사용할 세션을 만드는 공장입니다.

### `get_db()`

- 요청이 시작되면 세션을 하나 열고
- API 함수가 그 세션을 사용하게 하고
- 함수가 끝나면 세션을 닫습니다.

즉 DB 연결을 손으로 매번 열고 닫지 않도록
FastAPI가 자동으로 관리하게 만든 구조입니다.

---

## 8) STEP 5. create_post()가 ORM 객체를 만듦

검증이 끝났고 세션도 준비되었으면,
이제 실제 저장용 객체를 만듭니다.

```py
post = Post(
  user_id=payload.user_id,
  title=payload.title.strip(),
  content=payload.content.strip(),
)
```

여기서 `Post`는 `models.py`에 있는 클래스입니다.

```py
class Post(Base):
  __tablename__ = 'posts'

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
  title: Mapped[str] = mapped_column(String(200), nullable=False)
  content: Mapped[str] = mapped_column(Text, nullable=False)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

이 코드의 의미:

- `Post` 클래스는 DB의 `posts` 테이블과 연결되어 있음
- `title` 속성은 `posts.title` 컬럼과 연결됨
- `content` 속성은 `posts.content` 컬럼과 연결됨

즉 `Post(...)`를 만들었다는 것은
DB에 들어갈 한 줄(row)을 Python 객체로 표현한 것입니다.

중요:

- 아직 이 순간은 DB 저장 전입니다.
- 그냥 Python 객체만 메모리에 만들어진 상태입니다.

---

## 9) STEP 6. DB에 실제로 저장함

그 다음 코드가 실행됩니다.

```py
db.add(post)
db.commit()
```

각 줄의 차이를 정확히 알아야 합니다.

### `db.add(post)`

- 이 객체를 세션에 등록합니다.
- "이 객체는 저장 대상이다"라고 표시하는 단계입니다.
- 아직 DB에 완전히 반영된 것은 아닙니다.

### `db.commit()`

- 트랜잭션을 확정합니다.
- 이 순간 실제 SQL이 PostgreSQL에 실행됩니다.

개념적으로는 이런 SQL과 비슷한 일이 일어납니다.

```sql
INSERT INTO posts (user_id, title, content)
VALUES (NULL, '오늘의 기록', '백엔드 흐름을 공부했다.');
```

즉 실제 DB row는 commit 시점에 생깁니다.

---

## 10) STEP 7. 저장된 결과를 다시 읽어옴

저장 후 이 코드가 있습니다.

```py
db.refresh(post)
```

왜 필요한가:

- DB가 자동으로 만들어주는 값이 있기 때문입니다.
- 예: `id`, `created_at`, `updated_at`

예를 들어 저장 전에는 `post.id`가 없을 수 있지만,
저장 후에는 DB가 자동으로 값을 줍니다.

```py
post.id = 15
post.created_at = ...
post.updated_at = ...
```

즉 refresh는

```text
DB에 실제 저장된 최신 값을 Python 객체에 다시 반영하는 단계
```

입니다.

---

## 11) STEP 8. 백엔드가 프론트에 무엇을 반환하는가

마지막 줄은 이것입니다.

```py
return post
```

그런데 브라우저는 Python 객체를 이해하지 못합니다.

그래서 FastAPI는 `response_model=PostOut`을 보고
이 객체를 JSON으로 바꿔서 응답합니다.

여기서 아주 중요한 포인트가 있습니다.

프론트로 실제 값이 나가는 출발점은 바로 이 줄입니다.

```py
return post
```

즉:

- `create_post()` 함수 안에서 최종적으로 `post`를 반환하고
- FastAPI가 그 반환값을 받아서
- `response_model=PostOut` 규칙에 맞게 JSON 응답으로 바꾼 뒤
- HTTP 응답 body에 담아 프론트로 보냅니다.

한 줄로 쓰면:

```text
return post -> FastAPI가 PostOut 형식으로 변환 -> JSON 응답 -> 프론트로 전송
```

즉 프론트로 가는 값은 `main.py`의 `return post`에서 시작한다고 보면 됩니다.

---

## 11-1) 프론트로 가기 전, 백엔드 안에서는 어떤 값인가

`return post` 직전의 `post`는 이런 느낌의 Python 객체입니다.

```py
post.id = 15
post.user_id = None
post.title = "오늘의 기록"
post.content = "백엔드 흐름을 공부했다."
post.created_at = datetime(...)
post.updated_at = datetime(...)
```

중요:

- 이건 아직 JSON이 아닙니다.
- Python 객체입니다.
- 정확히는 SQLAlchemy ORM 객체입니다.

즉 백엔드 메모리 안에서는 이런 식으로 속성 접근이 가능한 객체입니다.

```py
post.title
post.content
```

---

## 11-2) 왜 PostOut이 필요한가

`main.py`의 라우트 선언을 다시 보면:

```py
@app.post('/api/posts', response_model=PostOut, status_code=status.HTTP_201_CREATED)
```

여기서 `response_model=PostOut`은
"이 API 응답은 PostOut 모양으로 내보내라"는 뜻입니다.

즉 FastAPI는 `return post`를 받으면 아래 필드만 꺼내서 응답으로 만듭니다.

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

이 코드가 뜻하는 것:

- 응답에는 `id`가 나간다
- 응답에는 `title`이 나간다
- 응답에는 `content`가 나간다
- 응답에는 `created_at`, `updated_at`이 나간다
- 그 외에 Post 객체 안에 다른 값이 있어도 PostOut에 없으면 응답에서 제외된다

즉 `PostOut`은 프론트로 나가는 응답의 틀입니다.

---

## 11-3) 프론트로 가는 실제 JSON 모양

백엔드가 최종적으로 보내는 응답은 이런 JSON입니다.

```json
{
  "id": 15,
  "user_id": null,
  "title": "오늘의 기록",
  "content": "백엔드 흐름을 공부했다.",
  "created_at": "2026-04-11T14:00:00+09:00",
  "updated_at": "2026-04-11T14:00:00+09:00"
}
```

중요:

- 프론트는 Python 객체를 받는 게 아닙니다.
- 프론트는 JSON 응답 문자열을 받습니다.
- 브라우저가 그 JSON을 다시 JavaScript 객체로 바꿉니다.

즉 데이터 형태는 이렇게 바뀝니다.

```text
Post ORM 객체
-> PostOut 기준으로 정리
-> JSON 응답 문자열
-> 프론트에서 JavaScript 객체
```

---

## 11-4) 프론트에서는 결국 어떤 값으로 받는가

프론트의 `client.js`에서는 마지막에 이 코드가 실행됩니다.

```js
return response.json();
```

그러면 프론트 쪽에서는 이런 JavaScript 객체를 받게 됩니다.

```js
{
  id: 15,
  user_id: null,
  title: "오늘의 기록",
  content: "백엔드 흐름을 공부했다.",
  created_at: "2026-04-11T14:00:00+09:00",
  updated_at: "2026-04-11T14:00:00+09:00"
}
```

즉 백엔드가 보낸 JSON이 프론트에서는 다시 JavaScript 객체가 되는 것입니다.

프론트 기준으로 보면 결국 이런 값을 받는 셈입니다.

```js
const savedPost = await createPost({ title, content });
```

지금 프로젝트에서는 이 값을 직접 화면에 꽂지는 않고,
저장 성공 후 다시 목록을 불러오는 방식을 사용하고 있습니다.

그래도 반환값 자체는 분명히 존재합니다.

---

## 11-5) 어디서 프론트로 가는지 한 줄로 다시 정리

아주 단순하게 압축하면 이렇습니다.

```text
1. main.py의 create_post()가 return post 실행
2. FastAPI가 PostOut 형식으로 변환
3. JSON 응답 body 생성
4. HTTP 응답으로 브라우저에 전달
5. 프론트의 response.json()이 JavaScript 객체로 변환
```

---

## 11-6) 그런데 왜 백엔드는 await 없이 return 하고, 프론트는 await로 받는가

이 부분은 초보자가 가장 많이 헷갈리는 지점입니다.

현재 백엔드 코드는 이렇게 되어 있습니다.

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

여기에는 `async def`도 없고 `await`도 없습니다.

그런데 프론트는 이렇게 씁니다.

```js
await createPost({ title, content });
```

왜 이런 차이가 생기느냐 하면,
백엔드와 프론트가 "기다리는 대상"이 다르기 때문입니다.

### 백엔드 쪽

- `create_post()`는 서버 안에서 실행되는 Python 함수입니다.
- 이 함수는 자기 작업을 끝내고 `return post`를 합니다.
- 즉 백엔드 함수 입장에서는 그냥 값을 반환한 것입니다.

즉 서버 코드 내부에서는:

```text
함수 실행 -> 값 반환
```

입니다.

### 프론트 쪽

- 프론트는 서버 함수 자체를 직접 호출하는 게 아닙니다.
- 프론트는 네트워크 요청을 보냅니다.
- 네트워크 응답은 시간이 걸립니다.
- 그래서 `fetch()`는 Promise를 반환합니다.
- 프론트는 그 Promise가 끝날 때까지 `await`로 기다립니다.

즉 프론트 입장에서는:

```text
HTTP 요청 보냄 -> 서버가 처리함 -> 네트워크 응답 돌아옴 -> 그때까지 기다림
```

입니다.

핵심:

- 백엔드는 함수 안에서 값을 `return`
- 프론트는 네트워크 응답을 `await`

즉 서로 다른 레벨의 이야기입니다.

```text
백엔드 return = 서버 함수가 값을 프레임워크에 넘김
프론트 await  = 브라우저가 HTTP 응답이 올 때까지 기다림
```

그래서 둘은 모순이 아닙니다.

---

## 11-7) 서버 함수 return 이후에는 누가 JSON으로 바꾸는가

이것도 중요한 포인트입니다.

백엔드 코드에서는 직접 이런 걸 쓰지 않습니다.

```py
json.dumps(post)
```

그런데도 프론트는 JSON 응답을 받습니다.

이유는 FastAPI가 중간에서 자동으로 처리하기 때문입니다.

순서를 아주 기초부터 쓰면:

1. `create_post()`가 `return post` 실행
2. FastAPI가 이 반환값을 받음
3. `response_model=PostOut`을 확인함
4. `post` 객체에서 `id`, `title`, `content` 같은 값을 꺼냄
5. 그 값을 JSON으로 직렬화 가능한 형태로 바꿈
6. HTTP 응답 body에 담아서 보냄

즉 실제 직렬화 작업은 FastAPI가 해줍니다.

---

## 11-8) Python 객체가 JSON으로 바뀌는 과정을 더 잘게 보기

백엔드 함수 안의 값은 이런 Python ORM 객체입니다.

```py
post.id = 15
post.user_id = None
post.title = "오늘의 기록"
post.content = "백엔드 흐름을 공부했다."
post.created_at = datetime(...)
post.updated_at = datetime(...)
```

이 값은 그대로는 JSON이 아닙니다.

왜냐하면 JSON은 문자열, 숫자, 불리언, 배열, 객체, null 같은 형태만 가질 수 있기 때문입니다.
특히 Python의 `datetime(...)` 객체는 그대로 JSON이 될 수 없습니다.

그래서 FastAPI는 응답 모델을 보고 JSON으로 바꿀 수 있는 형태로 정리합니다.

### 1. 먼저 PostOut 기준으로 필드를 고름

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

`from_attributes=True` 덕분에 FastAPI/Pydantic은
딕셔너리가 아닌 SQLAlchemy 객체에서도 값을 읽을 수 있습니다.

즉 이런 식으로 읽는다고 생각하면 됩니다.

```py
post.id
post.title
post.content
```

### 2. 그 다음 JSON 가능한 값으로 변환

예를 들어:

- `int` -> 그대로 숫자
- `str` -> 그대로 문자열
- `None` -> JSON의 `null`
- `datetime` -> ISO 형식 문자열

예:

```py
datetime(2026, 4, 11, 14, 0, 0)
```

는 JSON 응답에서 이렇게 됩니다.

```json
"2026-04-11T14:00:00+09:00"
```

즉 변환 흐름은 이렇습니다.

```text
Python ORM 객체
-> Pydantic PostOut
-> JSON 직렬화 가능한 값
-> HTTP 응답 body
```

---

## 11-9) 프론트가 await로 받는 실제 이유를 코드 흐름으로 보기

프론트의 핵심은 결국 이 부분입니다.

```js
export const createPost = (payload) =>
  apiRequest("/posts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
```

그리고 `client.js`에서는:

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

즉 프론트가 `await createPost(...)`를 하는 이유는,
그 안에서 결국 `await fetch(...)`가 실행되기 때문입니다.

다시 말해:

- 백엔드가 `await`를 안 쓰는 건 서버 함수 구현 방식의 문제
- 프론트가 `await`를 쓰는 건 HTTP 요청이 비동기이기 때문

입니다.

둘은 서로 다른 층의 동작입니다.

---

## 11-10) 한 줄로 최종 정리

백엔드는 Python 함수가 `return post`로 값을 FastAPI에 넘기고,
FastAPI는 그 Python 객체를 `PostOut` 기준으로 JSON 응답으로 직렬화해서 보내며,
프론트는 네트워크 응답을 기다려야 하므로 `await`로 그 JSON 응답을 받아 JavaScript 객체로 바꿔 사용합니다.

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

이 응답은 실제로는 대략 이런 JSON이 됩니다.

```json
{
  "id": 15,
  "user_id": null,
  "title": "오늘의 기록",
  "content": "백엔드 흐름을 공부했다.",
  "created_at": "2026-04-11T14:00:00+09:00",
  "updated_at": "2026-04-11T14:00:00+09:00"
}
```

즉 백엔드는 저장만 하는 게 아니라,
저장 결과를 JSON 응답으로 다시 돌려줍니다.

---

## 12) 프론트는 백엔드 응답을 어떻게 받는가

프론트의 `client.js`는 이렇게 응답을 받습니다.

```js
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
```

즉 백엔드 응답을 받은 뒤 프론트는:

1. 실패면 에러 처리
2. 204면 null 반환
3. 보통은 `response.json()`으로 JavaScript 객체로 변환

이렇게 동작합니다.

즉 백엔드가 준 JSON 응답은 다시 프론트에서 JS 객체가 됩니다.

---

## 13) 조회 API는 백엔드에서 어떻게 동작하는가

조회는 `read_posts()`가 담당합니다.

```py
@app.get('/api/posts', response_model=list[PostOut])
def read_posts(db: Session = Depends(get_db)):
  posts = db.execute(select(Post).order_by(Post.created_at.desc())).scalars().all()
  return posts
```

여기서 하는 일:

1. DB 세션 받기
2. `select(Post)`로 posts 테이블 조회
3. `created_at.desc()`로 최신 글 먼저 정렬
4. 결과를 Python 객체 리스트로 받기
5. `list[PostOut]` 형식으로 JSON 배열 응답 만들기

즉 조회 API도 결국은 같은 구조입니다.

```text
요청 수신 -> 세션 준비 -> DB 조회 -> Python 객체 -> JSON 응답
```

응답 예시:

```json
[
  {
    "id": 15,
    "user_id": null,
    "title": "오늘의 기록",
    "content": "백엔드 흐름을 공부했다.",
    "created_at": "2026-04-11T14:00:00+09:00",
    "updated_at": "2026-04-11T14:00:00+09:00"
  }
]
```

---

## 14) 삭제 API는 백엔드에서 어떻게 동작하는가

삭제는 `remove_post()`가 담당합니다.

```py
@app.delete('/api/posts/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_post(post_id: int, db: Session = Depends(get_db)):
  post = db.get(Post, post_id)
  if post is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Post not found')

  db.delete(post)
  db.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)
```

여기서 하는 일:

1. URL에서 `post_id` 추출
2. DB에서 해당 글 찾기
3. 없으면 404 에러 반환
4. 있으면 삭제 등록
5. commit으로 실제 삭제 반영
6. 204 No Content 응답 반환

즉 삭제도 결국 구조는 같습니다.

```text
요청 수신 -> 대상 찾기 -> DB 반영 -> 응답 반환
```

---

## 15) 백엔드에서 꼭 구분해야 하는 개념

### 1. 요청 body

- 프론트가 보낸 데이터
- 보통 JSON 형식

예:

```json
{
  "title": "오늘의 기록",
  "content": "백엔드 흐름을 공부했다."
}
```

### 2. schema

- 요청과 응답 규칙
- Pydantic이 검사함

예:

- `PostCreate`
- `PostOut`

### 3. session

- DB 작업 단위
- 요청마다 하나 열고 닫음

### 4. model

- DB 테이블을 Python 클래스로 표현한 것

예:

- `Post`

### 5. response

- 백엔드가 프론트에 돌려주는 값
- 보통 JSON

---

## 16) 한 번에 정리하는 전체 흐름

글 저장 기준으로 백엔드 입장에서 보면:

```text
프론트가 JSON 요청 보냄
-> FastAPI가 POST /api/posts를 create_post에 연결
-> 요청 body를 PostCreate로 파싱
-> Pydantic이 데이터 검증
-> get_db()로 세션 준비
-> Post ORM 객체 생성
-> db.add()
-> db.commit()
-> db.refresh()
-> PostOut 형식으로 JSON 응답 생성
-> 프론트로 반환
```

이 순서를 이해하면,
백엔드에서 요청이 들어왔을 때 어디서 무슨 일이 일어나는지 거의 다 잡힌 것입니다.

---

## 17) 초보자 기준으로 꼭 이해해야 하는 핵심 3개

1. 백엔드는 JSON을 바로 DB에 던지는 게 아니다
- 먼저 schema로 검증하고
- ORM 객체로 바꾸고
- 세션을 통해 commit해서 저장한다

2. main.py 하나만 있는 게 아니다
- main.py는 요청을 받는 중심 파일이고
- schemas.py, database.py, models.py가 각자 역할을 나눠 가진다

3. 백엔드는 항상 응답도 만든다
- 저장만 하는 것이 아니라
- 저장 결과를 JSON으로 다시 만들어 프론트에 돌려준다

---

## 18) 마지막 한 문장 정리

백엔드는 프론트가 보낸 JSON 요청을 받아서,
schema로 검사하고,
DB 세션과 ORM 모델을 이용해 PostgreSQL에 반영한 뒤,
그 결과를 다시 JSON 응답으로 바꿔 프론트에 돌려주는 역할을 합니다.