# 구조/매핑 기초 노트

이 문서는 "이 파일이 왜 있는지", "무엇과 무엇이 연결되는지", "DB가 이미 있는데 왜 models.py가 또 필요한지"를 기초부터 설명하는 노트입니다.

---

## 1) 이 프로젝트를 한 문장으로 보면

브라우저 화면에서 입력한 글을
React가 받아서
FastAPI 서버로 보내고
서버가 PostgreSQL에 저장한 뒤
다시 JSON으로 돌려주고
화면이 그 결과를 다시 그려주는 구조입니다.

즉:

화면 -> API 요청 -> 서버 로직 -> DB 저장/조회 -> JSON 응답 -> 화면 갱신

---

## 2) 전체 구성도 맵

```text
[사용자]
   |
   v
[src/App.jsx]
  화면, 입력, 버튼 클릭 처리
   |
   v
[src/api/postApi.js]
  글 목록/작성/삭제 API 이름 정리
   |
   v
[src/api/client.js]
  공통 fetch 처리, base URL, 에러 처리
   |
   v
HTTP 요청
   |
   v
[backend/app/main.py]
  FastAPI 라우트, 요청 진입점
   |
   +--> [backend/app/schemas.py]
   |     요청/응답 데이터 규칙 검사
   |
   +--> [backend/app/database.py]
   |     DB 연결, 세션 생성/정리
   |
   +--> [backend/app/models.py]
         posts 테이블을 Python 클래스로 매핑
   |
   v
[PostgreSQL posts 테이블]
   |
   v
JSON 응답 반환
   |
   v
[src/App.jsx]
  상태 갱신 후 화면 다시 렌더링
```

핵심은 각 파일이 하나의 역할만 맡고 있다는 점입니다.

---

## 3) 폴더 레이아웃 의미

### 루트

- `src/`
  프론트엔드 React 코드가 들어있습니다.
- `backend/app/`
  FastAPI 서버 코드가 들어있습니다.
- `.env.local`
  프론트에서 쓸 환경변수입니다.
- `backend/.env`
  백엔드에서 쓸 환경변수입니다.

즉 루트 기준으로는:

- `src` = 브라우저 쪽 코드
- `backend/app` = 서버 쪽 코드

---

## 4) 프론트엔드 파일은 왜 이렇게 나뉘는가

### 4-1) src/main.jsx

역할:

- React 앱 시작점
- App 컴포넌트를 실제 브라우저 DOM에 붙임

왜 필요함:

- React 앱은 아무 파일에서나 시작하지 않습니다.
- "제일 먼저 실행되는 입구"가 하나 필요합니다.

쉽게 말하면:

- `main.jsx`는 앱 전원 켜는 버튼입니다.

---

### 4-2) src/App.jsx

역할:

- 사용자가 직접 보는 화면
- 입력값 상태 관리
- 저장/삭제 버튼 클릭 처리
- 목록 렌더링

왜 필요함:

- 사용자의 행동은 여기서 시작됩니다.
- title, content, items 같은 상태도 여기서 관리합니다.

쉽게 말하면:

- `App.jsx`는 프론트의 메인 작업대입니다.

여기서 하는 일:

- 제목 입력 받기
- 내용 입력 받기
- 저장 버튼 클릭 시 createPost 호출
- 삭제 버튼 클릭 시 deletePost 호출
- 첫 화면에서 목록 조회
- items를 화면에 그리기

---

### 4-3) src/api/postApi.js

역할:

- 글 관련 API 함수만 모아둔 파일

왜 필요함:

- 화면 코드 안에 fetch를 직접 다 써버리면 코드가 금방 지저분해집니다.
- 글 관련 API를 한 군데로 모아야 읽기 쉽고 재사용하기 쉽습니다.

쉽게 말하면:

- `postApi.js`는 "글 기능 전용 전화번호부"입니다.

이 파일이 없으면:

- App.jsx 안에 URL, method, body 작성이 다 들어와서 화면 코드와 네트워크 코드가 섞입니다.

---

### 4-4) src/api/client.js

역할:

- 모든 API 요청에서 공통으로 쓰는 fetch 규칙 관리

왜 필요함:

- base URL
- JSON 헤더
- 에러 처리
- 204 응답 처리

이런 건 모든 API에서 반복됩니다.

쉽게 말하면:

- `client.js`는 공용 택배 접수 창구입니다.
- 어디로 보내는지, 실패했을 때 어떻게 처리할지, 응답을 어떻게 읽을지 한 곳에서 관리합니다.

이 파일이 없으면:

- API마다 fetch 코드 복붙
- 어떤 API는 에러 처리 있고 어떤 API는 없음
- 유지보수가 어려워짐

---

## 5) 백엔드 파일은 왜 이렇게 나뉘는가

### 5-1) backend/app/main.py

역할:

- FastAPI 앱 생성
- CORS 설정
- URL별 API 함수 등록
- 프론트 요청을 받아 처리 시작

왜 필요함:

- 서버에는 "어떤 URL이 어떤 함수를 실행할지"를 정하는 중심 파일이 필요합니다.

쉽게 말하면:

- `main.py`는 백엔드 관제실입니다.

예:

- `GET /api/posts` -> 목록 조회
- `POST /api/posts` -> 글 저장
- `DELETE /api/posts/{post_id}` -> 글 삭제

---

### 5-2) backend/app/schemas.py

역할:

- 요청 데이터 검증
- 응답 데이터 형식 정의

왜 필요함:

- 서버는 아무 데이터나 받으면 안 됩니다.
- 제목이 비어 있거나 타입이 이상하면 입구에서 막아야 합니다.

쉽게 말하면:

- `schemas.py`는 데이터 검문소입니다.

예:

- `PostCreate`는 클라이언트가 서버에 보내는 데이터 규칙
- `PostOut`은 서버가 클라이언트에 돌려주는 데이터 규칙

중요:

- `schemas.py`는 DB 테이블 정의가 아닙니다.
- "API로 오가는 데이터 형식" 정의입니다.

---

### 5-3) backend/app/database.py

역할:

- DB 연결 엔진 생성
- 세션 팩토리 생성
- 요청마다 DB 세션 열고 닫기

왜 필요함:

- DB 연결을 아무 파일에서나 직접 열고 닫으면 구조가 금방 무너집니다.
- 연결 관리 규칙은 한 곳에 모여 있어야 합니다.

쉽게 말하면:

- `database.py`는 DB 연결 관리자입니다.

중요 개념:

- `engine`: PostgreSQL과 연결하는 큰 설정 객체
- `SessionLocal`: 요청마다 사용할 작업 단위 세션 생성기
- `get_db()`: FastAPI가 요청마다 세션을 주고, 끝나면 자동 정리하게 하는 함수

---

### 5-4) backend/app/models.py

역할:

- DB 테이블을 Python 클래스와 연결
- 컬럼 구조를 코드로 표현

쉽게 말하면:

- `models.py`는 DB 번역기입니다.

여기가 가장 중요한 포인트입니다.

많이 하는 질문:

"이미 PostgreSQL에 posts 테이블이 있는데 왜 models.py가 또 필요하지?"

정답:

- DB에 테이블이 존재하는 것과
- Python 코드가 그 테이블 구조를 이해하는 것은
- 완전히 다른 문제입니다.

PostgreSQL은 `posts` 테이블을 알고 있습니다.
하지만 Python은 자동으로 아래를 알지 못합니다.

- `posts`라는 테이블이 있는지
- `id`, `title`, `content` 컬럼이 있는지
- `title`이 문자열인지
- `created_at`이 날짜인지
- 어떤 컬럼이 null 허용인지

그래서 Python 코드 쪽에도 그 구조를 알려줘야 합니다.
그 역할이 `models.py`입니다.

즉:

- DB 세계: 테이블, 컬럼, row
- Python 세계: 클래스, 속성, 객체

`models.py`는 이 둘을 연결합니다.

```text
DB 테이블 posts        <->        Python 클래스 Post
컬럼 title             <->        속성 post.title
한 줄(row)             <->        객체 1개(Post 인스턴스)
```

그래서 서버 코드에서 이런 식으로 쓸 수 있습니다.

```py
post = Post(title="제목", content="내용")
db.add(post)
db.commit()
```

이건 사람이 보기엔 Python 코드지만,
SQLAlchemy는 이걸 보고 실제 SQL로 바꿉니다.

예:

```sql
INSERT INTO posts (title, content) VALUES ('제목', '내용');
```

즉 models.py가 있어야:

1. Python 코드에서 테이블을 객체처럼 다룰 수 있고
2. SQLAlchemy가 SQL을 생성할 수 있고
3. `select(Post)` 같은 ORM 쿼리가 가능하고
4. `Base.metadata.create_all()` 도 동작할 수 있습니다.

결론:

- DB가 이미 있어도 `models.py`는 필요합니다.
- 중복 파일이 아니라, 서버 코드와 DB를 이어주는 연결 다리입니다.

---

## 6) schemas.py 와 models.py 는 뭐가 다른가

둘 다 비슷해 보여서 많이 헷갈립니다.

### schemas.py

대상:

- 클라이언트 <-> 서버

목적:

- 어떤 데이터를 받을지
- 어떤 데이터를 돌려줄지

예:

- `PostCreate`
- `PostOut`

즉:

- API 입출력 규칙서

### models.py

대상:

- 서버 코드 <-> DB

목적:

- 어떤 테이블인지
- 어떤 컬럼인지
- ORM으로 어떻게 다룰지

예:

- `Post`

즉:

- DB 매핑 정의서

한 줄 비교:

```text
schemas.py = API 데이터 규칙
models.py  = DB 테이블 매핑
```

---

## 7) database.py 와 models.py 는 뭐가 다른가

이 둘도 자주 헷갈립니다.

### database.py

하는 일:

- 어디 DB에 연결할지 정함
- 연결 엔진 만듦
- 세션을 열고 닫음

즉:

- 연결 관리

### models.py

하는 일:

- DB 안의 posts 테이블 구조를 코드로 표현

즉:

- 구조 정의

비유:

```text
database.py = 은행 창구를 여는 규칙
models.py   = 통장 양식 정의
```

---

## 8) 실제 글 작성 시 파일들이 어떻게 이어지는가

### 단계 1. 화면에서 입력

- 사용자가 App.jsx에서 제목/내용 입력
- React 상태(title, content)에 저장

### 단계 2. 저장 버튼 클릭

- App.jsx의 `handleSubmit()` 실행
- 빈 값 검사
- `createPost()` 호출

### 단계 3. API 함수 호출

- postApi.js의 `createPost(payload)` 실행
- 내부에서 `apiRequest('/posts', ...)` 호출

### 단계 4. HTTP 요청 전송

- client.js가 fetch 실행
- `http://localhost:8080/api/posts` 로 POST 요청 보냄

### 단계 5. 서버가 요청 받음

- main.py의 `create_post()`가 요청 수신

### 단계 6. 요청 데이터 검증

- schemas.py의 `PostCreate`로 body 검증
- 형식이 이상하면 여기서 에러

### 단계 7. DB 세션 준비

- database.py의 `get_db()`가 세션 제공

### 단계 8. ORM 객체 생성

- models.py의 `Post(...)` 생성

### 단계 9. DB 저장

- `db.add(post)`
- `db.commit()`

### 단계 10. 응답 반환

- `db.refresh(post)`로 DB에서 최신값 읽음
- `PostOut` 형식으로 JSON 반환

### 단계 11. 프론트 화면 갱신

- App.jsx가 다시 목록 요청
- `setItems(list)`
- 화면 다시 렌더링

---

## 9) 만약 파일이 하나라도 없으면 어떤 문제가 생기나

### App.jsx가 없으면

- 사용자 화면이 없음
- 입력/버튼/목록 표시 불가

### postApi.js가 없으면

- API 호출 코드가 화면에 직접 섞임
- 재사용성과 가독성 저하

### client.js가 없으면

- fetch 공통 처리 중복
- 에러 처리와 URL 관리가 흩어짐

### main.py가 없으면

- 서버 진입점이 없음
- 어떤 URL이 어떤 함수를 실행할지 정할 수 없음

### schemas.py가 없으면

- 잘못된 입력을 깔끔하게 검증하기 어려움
- 응답 형식 일관성 저하

### database.py가 없으면

- DB 연결 관리가 흩어짐
- 세션 정리 누락 가능성 증가

### models.py가 없으면

- ORM 방식 사용 불가
- raw SQL을 직접 문자열로 다 써야 함
- 서버 코드가 DB 구조를 안전하게 이해하기 어려움

---

## 10) 초보자가 꼭 잡아야 하는 핵심 개념 5개

1. 프론트와 백엔드는 역할이 다르다

- 프론트는 보여주고 입력받는다
- 백엔드는 처리하고 저장한다

2. API는 둘 사이의 약속이다

- 프론트는 URL과 JSON 형식에 맞춰 요청한다
- 백엔드는 그 형식에 맞춰 응답한다

3. schema와 model은 다르다

- schema는 API용
- model은 DB용

4. DB 세션은 요청마다 열고 닫는다

- 계속 하나를 공유하는 개념이 아니다

5. ORM은 SQL을 숨기는 게 아니라 SQL을 더 안전하게 다루게 해주는 도구다

- 결국 DB에는 SQL이 실행된다
- 다만 Python 코드로 더 구조적으로 표현하는 것뿐이다

---

## 11) 지금 프로젝트에서 한 줄 요약

이 프로젝트는

- `App.jsx`가 사용자 입력을 받고
- `postApi.js`가 글 API 이름을 정리하고
- `client.js`가 HTTP 요청을 보내고
- `main.py`가 요청을 받아서
- `schemas.py`로 데이터 검증하고
- `database.py`로 세션을 얻고
- `models.py`로 posts 테이블을 객체처럼 다뤄서
- PostgreSQL에 저장/조회한 뒤
- 다시 React 화면에 보여주는 구조입니다.

---

## 12) 이 노트를 어떻게 읽으면 좋은가

추천 순서:

1. 먼저 이 파일의 2번 구성도 맵을 본다
2. 그다음 5번의 backend 파일 역할을 본다
3. 특히 5-4의 models.py 설명을 다시 읽는다
4. 그다음 6번, 7번으로 schema/model/database 차이를 구분한다
5. 마지막으로 8번의 실제 글 작성 흐름을 따라간다

이 순서로 보면 파일이 따로 노는 게 아니라,
각자 한 역할씩 맡아서 하나의 요청을 완성한다는 점이 보입니다.
