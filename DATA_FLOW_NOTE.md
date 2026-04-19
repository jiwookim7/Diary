# 데이터 흐름 노트

이 문서는

- 프론트에서 어떤 데이터가 만들어지는지
- 그 데이터가 어떤 형태로 바뀌는지
- 어떻게 백엔드로 가는지
- 백엔드가 어떤 로직으로 받아서 저장하고
- 어떤 형태로 다시 반환하는지

를 아주 기초부터 설명합니다.

---

## 1) 먼저 핵심부터

지금 프로젝트에서 글 저장은 아래 순서로 진행됩니다.

```text
사용자 입력
-> React 상태
-> JavaScript 객체
-> JSON 문자열
-> HTTP 요청 body
-> FastAPI가 Python 데이터로 파싱
-> Pydantic 검증
-> SQLAlchemy ORM 객체 생성
-> PostgreSQL 저장
-> Python 객체 반환
-> JSON 응답
-> 브라우저가 다시 JavaScript 객체로 파싱
-> React 화면 갱신
```

핵심은 데이터가 한 번에 DB로 가는 것이 아니라,
중간에 형태가 계속 바뀐다는 점입니다.

---

## 2) 예시 데이터 하나 정해놓고 끝까지 따라가기

사용자가 화면에 이렇게 입력했다고 가정합니다.

- 제목: `오늘의 기록`
- 내용: `FastAPI 흐름을 공부했다.`

이 데이터가 끝까지 가는 과정을 추적해보겠습니다.

---

## 3) STEP 1. 사용자가 입력하면 React 상태에 저장됨

프론트의 입력 처리는 `src/App.jsx`에서 시작됩니다.

```js
const [title, setTitle] = useState("");
const [content, setContent] = useState("");

<input value={title} onChange={(event) => setTitle(event.target.value)} />
<textarea value={content} onChange={(event) => setContent(event.target.value)} />
```

사용자가 타이핑하면 `onChange`가 실행되고, React 상태가 바뀝니다.

이 시점의 데이터 형태:

```js
title = "오늘의 기록";
content = "FastAPI 흐름을 공부했다.";
```

이건 아직 네트워크로 나간 데이터가 아닙니다.
그냥 브라우저 메모리 안에 들어 있는 JavaScript 문자열입니다.

---

## 4) STEP 2. 저장 버튼 클릭 시 JavaScript 객체 생성

사용자가 저장 버튼을 누르면 `handleSubmit()`가 실행됩니다.

```js
await createPost({ title, content });
```

여기서 `{ title, content }`는 JavaScript 객체입니다.

실제 형태:

```js
{
  title: "오늘의 기록",
  content: "FastAPI 흐름을 공부했다."
}
```

이 단계는 중요합니다.

- 이건 DB row가 아닙니다.
- JSON도 아닙니다.
- 그냥 JavaScript 객체입니다.

즉 프론트는 먼저 자기 언어(JavaScript)의 데이터 형태로 값을 들고 있습니다.

---

## 5) STEP 3. postApi.js에서 JSON 문자열로 변환

이 객체는 `src/api/postApi.js`로 넘어갑니다.

```js
export const createPost = (payload) =>
  apiRequest("/posts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
```

여기서 `payload`는 방금 만든 JS 객체입니다.

```js
payload = {
  title: "오늘의 기록",
  content: "FastAPI 흐름을 공부했다.",
};
```

그리고 `JSON.stringify(payload)`를 하면 이렇게 바뀝니다.

```json
"{\"title\":\"오늘의 기록\",\"content\":\"FastAPI 흐름을 공부했다.\"}"
```

사람이 읽기 쉽게 풀면 실제 body 내용은 이겁니다.

```json
{
  "title": "오늘의 기록",
  "content": "FastAPI 흐름을 공부했다."
}
```

왜 문자열로 바꾸는가:

- HTTP 요청 body는 네트워크로 전송되는 데이터입니다.
- 브라우저는 JavaScript 객체를 그대로 전송하지 않습니다.
- 문자열 형태로 직렬화해서 보내야 합니다.

즉:

```text
JavaScript 객체 -> JSON 문자열
```

---

## 6) STEP 4. client.js가 실제로 백엔드로 전송

`postApi.js`는 직접 네트워크를 보내는 파일이 아니라,
요청 내용을 정리해서 `client.js`에 넘깁니다.

```js
export const apiRequest = async (path, options = {}) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });
```

여기서 많이 헷갈리는 부분이 있습니다.

`method`, `body`, `headers`는 모두 `fetch()`의 두 번째 인자로 들어가는 **옵션 객체의 속성**입니다.

즉 구조는 이렇게 생겼습니다.

```js
fetch("http://localhost:8080/api/posts", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: '{"title":"오늘의 기록","content":"FastAPI 흐름을 공부했다."}',
});
```

중요:

- `method`는 `headers` 안에 들어가지 않습니다.
- `body`도 `headers` 안에 들어가지 않습니다.
- `headers`는 헤더끼리만 들어가는 별도 객체입니다.

즉 모양을 다시 나누면 이렇습니다.

```text
fetch(URL, {
  method: "POST",     <- 요청 방식
  headers: {           <- 요청에 대한 부가 정보
    "Content-Type": "application/json"
  },
  body: "...JSON..."  <- 실제로 보내는 데이터 본문
})
```

각각의 역할:

- `method`
  어떤 동작을 할지 정합니다.
  예: GET 조회, POST 생성, DELETE 삭제
- `headers`
  요청에 대한 설명 정보를 보냅니다.
  예: body가 JSON 형식이라는 정보
- `body`
  실제 데이터가 들어가는 자리입니다.
  예: 제목, 내용 같은 값

쉽게 말하면:

- `method` = 이 요청으로 뭘 할 건지
- `headers` = 이 요청 데이터가 어떤 성격인지
- `body` = 실제 내용물

택배 비유로 보면:

- `method` = 보내는 목적표시(새로 등록, 조회, 삭제)
- `headers` = 포장 상자 바깥 라벨
- `body` = 상자 안에 들어 있는 실제 물건

그래서 `Content-Type: application/json`은
"상자 안의 내용물이 JSON 형식이다"라고 알려주는 정보일 뿐이고,
실제 JSON 데이터 자체는 `body`에 들어갑니다.

현재 코드 흐름을 실제 값으로 풀면 대략 이렇게 됩니다.

### postApi.js에서 만든 options

```js
options = {
  method: "POST",
  body: '{"title":"오늘의 기록","content":"FastAPI 흐름을 공부했다."}',
};
```

### client.js에서 fetch에 들어가는 최종 옵션

```js
{
  headers: {
    "Content-Type": "application/json"
  },
  method: "POST",
  body: '{"title":"오늘의 기록","content":"FastAPI 흐름을 공부했다."}'
}
```

즉 최종적으로는:

- `headers` 안에는 `Content-Type`만 들어가고
- `method`는 바깥에 따로 있고
- `body`도 바깥에 따로 있습니다.

예를 들어 현재 값이면 실제 요청은 개념적으로 이렇게 됩니다.

```http
POST /api/posts HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{"title":"오늘의 기록","content":"FastAPI 흐름을 공부했다."}
```

여기서 중요한 포인트:

- `method: "POST"` = 새 데이터를 생성하겠다는 뜻
- `Content-Type: application/json` = body가 JSON 형식이라는 뜻
- `fetch()` = 실제 네트워크 요청을 백엔드로 보냄

즉, 진짜 백엔드로 가는 순간은 `fetch()`가 실행될 때입니다.

---

## 7) STEP 5. 백엔드 main.py가 요청을 받음

요청은 FastAPI의 `main.py`로 들어갑니다.

```py
@app.post('/api/posts', response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
```

이 선언 하나에 중요한 뜻이 많이 들어 있습니다.

### `@app.post('/api/posts')`

- `POST /api/posts` 요청이 오면 이 함수를 실행하라는 뜻입니다.

### `payload: PostCreate`

- 요청 body의 JSON을 읽어서 `PostCreate` 형식으로 바꾸라는 뜻입니다.
- 즉 FastAPI가 JSON을 Python 데이터로 해석합니다.

### `db: Session = Depends(get_db)`

- DB 작업용 세션을 자동으로 준비해달라는 뜻입니다.

즉 여기서부터는 브라우저 세계가 아니라 Python/FastAPI 세계입니다.

---

## 8) STEP 6. JSON이 Python 데이터로 바뀜

프론트에서 보낸 JSON:

```json
{
  "title": "오늘의 기록",
  "content": "FastAPI 흐름을 공부했다."
}
```

FastAPI가 이것을 읽어서 Python 쪽에서는 대략 이런 느낌으로 다룹니다.

```py
payload.title == "오늘의 기록"
payload.content == "FastAPI 흐름을 공부했다."
```

즉 데이터 형태가 다시 바뀝니다.

```text
JSON 문자열 -> Python 객체(PostCreate)
```

---

## 9) STEP 7. schemas.py가 이 데이터를 검증함

`schemas.py`에는 이런 규칙이 있습니다.

```py
class PostCreate(BaseModel):
  user_id: int | None = Field(default=None, ge=1)
  title: str = Field(min_length=1, max_length=200)
  content: str = Field(min_length=1)
```

이 규칙으로 아래를 검사합니다.

- title이 문자열인지
- title 길이가 1 이상 200 이하인지
- content가 비어 있지 않은지
- user_id가 있으면 1 이상의 정수인지

예를 들어 이런 요청이면:

```json
{
  "title": "",
  "content": "본문"
}
```

백엔드는 저장 단계로 가지 않고 바로 에러를 반환합니다.

즉 schemas.py의 역할은:

```text
DB에 들어가기 전에 잘못된 데이터를 입구에서 차단
```

---

## 10) STEP 8. create_post()가 ORM 객체를 만듦

검증이 끝나면 `main.py`의 함수 본문이 실행됩니다.

```py
post = Post(
  user_id=payload.user_id,
  title=payload.title.strip(),
  content=payload.content.strip(),
)
```

여기서 `Post(...)`는 `models.py`의 ORM 클래스입니다.

이 시점의 데이터는 DB row가 아니라 Python 객체입니다.

개념적으로는 이런 상태입니다.

```py
post = Post(
  user_id=None,
  title="오늘의 기록",
  content="FastAPI 흐름을 공부했다."
)
```

중요:

- 아직 DB에 저장되지 않았습니다.
- 메모리 안에만 있는 Python 객체입니다.

즉 여기서 데이터 형태가 또 바뀝니다.

```text
PostCreate(Pydantic 객체) -> Post(SQLAlchemy ORM 객체)
```

---

## 11) STEP 9. ORM 객체가 실제 DB row로 저장됨

그 다음 코드가 실행됩니다.

```py
db.add(post)
db.commit()
```

각 줄의 의미:

### `db.add(post)`

- 이 객체를 저장 대상으로 세션에 등록합니다.
- 아직 INSERT가 확정된 것은 아닙니다.

### `db.commit()`

- 이 순간 실제 SQL이 실행됩니다.
- PostgreSQL에 진짜 저장됩니다.

개념적으로는 이런 SQL이 실행됩니다.

```sql
INSERT INTO posts (user_id, title, content)
VALUES (NULL, '오늘의 기록', 'FastAPI 흐름을 공부했다.');
```

즉 여기서 처음으로 DB row가 생깁니다.

---

## 12) STEP 10. DB가 만든 값을 다시 읽어옴

저장 후 이 코드가 실행됩니다.

```py
db.refresh(post)
```

왜 필요한가:

- DB가 자동으로 만든 값이 있기 때문입니다.
- 예: `id`, `created_at`, `updated_at`

즉 저장 전에는 이런 값이 없을 수 있습니다.

```py
post.id = 없음
```

저장 후 refresh를 하면 이런 값이 들어옵니다.

```py
post.id = 12
post.created_at = 2026-04-11T...
post.updated_at = 2026-04-11T...
```

즉 DB 저장 결과를 Python 객체에 다시 반영하는 단계입니다.

---

## 13) STEP 11. 백엔드가 Python 객체를 JSON 응답으로 반환

마지막 줄은 이겁니다.

```py
return post
```

그런데 그냥 Python 객체를 브라우저가 이해할 수는 없습니다.

그래서 FastAPI가 `response_model=PostOut`을 이용해 JSON으로 변환합니다.

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

이 결과 브라우저로 가는 응답은 대략 이렇게 됩니다.

```json
{
  "id": 12,
  "user_id": null,
  "title": "오늘의 기록",
  "content": "FastAPI 흐름을 공부했다.",
  "created_at": "2026-04-11T12:30:00+09:00",
  "updated_at": "2026-04-11T12:30:00+09:00"
}
```

즉 데이터 형태가 또 바뀝니다.

```text
Python ORM 객체 -> JSON 응답
```

---

## 14) STEP 12. client.js가 응답을 다시 JavaScript 객체로 바꿈

프론트에서는 이 코드를 통해 응답을 받습니다.

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

`response.json()`은 응답 body의 JSON 문자열을 다시 JavaScript 객체로 바꿉니다.

즉:

```text
JSON 응답 -> JavaScript 객체
```

프론트에서 받는 실제 값은 이런 모습입니다.

```js
{
  id: 12,
  user_id: null,
  title: "오늘의 기록",
  content: "FastAPI 흐름을 공부했다.",
  created_at: "2026-04-11T12:30:00+09:00",
  updated_at: "2026-04-11T12:30:00+09:00"
}
```

---

## 15) STEP 13. App.jsx가 저장 후 다시 목록을 불러옴

현재 코드는 저장 응답 하나를 바로 리스트에 붙이지 않고,
다시 목록 전체를 불러오는 방식을 씁니다.

```js
await createPost({ title, content });
setTitle("");
setContent("");
await loadPosts();
```

이 말은:

1. 저장 요청 보내고
2. 저장 성공 확인한 뒤
3. `GET /posts`를 다시 호출해서
4. 최신 목록으로 화면을 다시 그린다는 뜻입니다.

초보자가 이해하기엔 이 방식이 더 단순합니다.

---

## 16) 조회(GET)에서는 데이터가 어떻게 오가나

조회도 거의 같은데 더 단순합니다.

### 프론트

```js
const data = await apiRequest("/posts", { method: "GET" });
```

### 백엔드

```py
@app.get('/api/posts', response_model=list[PostOut])
def read_posts(db: Session = Depends(get_db)):
  posts = db.execute(select(Post).order_by(Post.created_at.desc())).scalars().all()
  return posts
```

흐름:

```text
GET 요청
-> 백엔드가 DB에서 posts 목록 조회
-> Post 객체 리스트 생성
-> PostOut 리스트로 JSON 응답
-> 프론트가 response.json()으로 배열 받음
-> setItems(list)로 화면 갱신
```

응답 예시:

```json
[
  {
    "id": 12,
    "user_id": null,
    "title": "오늘의 기록",
    "content": "FastAPI 흐름을 공부했다.",
    "created_at": "2026-04-11T12:30:00+09:00",
    "updated_at": "2026-04-11T12:30:00+09:00"
  },
  {
    "id": 11,
    "user_id": null,
    "title": "어제 기록",
    "content": "복습했다.",
    "created_at": "2026-04-10T20:00:00+09:00",
    "updated_at": "2026-04-10T20:00:00+09:00"
  }
]
```

---

## 17) 데이터 형태 변화만 따로 압축해서 보기

글 작성 시 데이터는 이렇게 변합니다.

```text
1. React 상태
   title = "오늘의 기록"
   content = "FastAPI 흐름을 공부했다."

2. JavaScript 객체
   { title: "오늘의 기록", content: "FastAPI 흐름을 공부했다." }

3. JSON 문자열
   '{"title":"오늘의 기록","content":"FastAPI 흐름을 공부했다."}'

4. HTTP 요청 body
   네트워크를 통해 백엔드로 전송

5. Python Pydantic 객체
   PostCreate(title="오늘의 기록", content="FastAPI 흐름을 공부했다.")

6. Python ORM 객체
   Post(title="오늘의 기록", content="FastAPI 흐름을 공부했다.")

7. DB row
   posts 테이블의 한 줄로 저장

8. Python ORM 객체(저장 후)
   Post(id=12, title="오늘의 기록", ...)

9. JSON 응답
   {"id":12,"title":"오늘의 기록",...}

10. JavaScript 객체
   { id: 12, title: "오늘의 기록", ... }

11. React 상태
   items 배열 갱신
```

---

## 18) 자주 헷갈리는 포인트 정리

### Q1. postApi.js가 DB로 직접 보내는가?

아니요.

- `postApi.js`는 요청 내용을 정리합니다.
- 실제 전송은 `client.js`의 `fetch()`가 합니다.
- DB와 직접 연결되는 것은 백엔드입니다.

즉:

```text
App.jsx -> postApi.js -> client.js -> 백엔드 -> DB
```

---

### Q2. JSON으로 바꾸는 이유는 DB 때문인가?

정확히는 DB 때문이 아니라 HTTP 요청 때문입니다.

- 프론트는 백엔드로 JSON 형식의 요청을 보냅니다.
- 백엔드가 그 JSON을 받아서 Python 객체로 바꾸고
- 그 다음 DB에 저장합니다.

즉:

```text
JSON은 프론트 <-> 백엔드 사이의 전달 형식
DB row는 백엔드 <-> PostgreSQL 사이의 저장 형식
```

---

### Q3. 백엔드는 받은 JSON을 바로 DB에 넣는가?

아니요.

중간 과정이 있습니다.

```text
JSON 수신
-> Pydantic 검증
-> ORM 객체 생성
-> commit
-> DB 저장
```

즉 검증과 변환 과정을 거친 뒤 저장합니다.

---

## 19) 한 문장 최종 요약

프론트는 JavaScript 객체를 JSON으로 바꿔 백엔드에 보내고,
백엔드는 그 JSON을 Python 객체로 받아 검증한 뒤 ORM 객체로 바꿔 DB에 저장하고,
저장된 결과를 다시 JSON으로 바꿔 프론트에 돌려줍니다.
