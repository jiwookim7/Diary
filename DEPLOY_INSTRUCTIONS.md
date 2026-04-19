# 🚀 배포 가이드 (Vercel + Render)

## 순서

### 1️⃣ 백엔드 먼저 배포 (Render)

#### A. Render 계정 생성
1. https://render.com 접속
2. GitHub 계정으로 로그인

#### B. PostgreSQL 데이터베이스 생성
1. Dashboard → **New** → **PostgreSQL**
2. 설정:
   - Name: `diary-postgres`
   - Database: `diary_db`
   - User: `diary_user`
   - Region: **Singapore** (가장 가까움)
   - Plan: **Free**
3. **Create Database** 클릭
4. 생성 완료되면 **Internal Database URL** 복사 → 메모장에 저장

#### C. 백엔드 Web Service 생성
1. Dashboard → **New** → **Web Service**
2. GitHub 저장소 연결
3. 설정:
   - Name: `diary-backend`
   - Region: **Singapore**
   - Branch: `main` (또는 `master`)
   - Root Directory: `backend`
   - Runtime: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Instance Type: **Free**

4. **Environment Variables** 추가:
   ```
   DATABASE_URL=<위에서 복사한 Internal Database URL>
   CORS_ORIGINS=https://your-app.vercel.app
   ```
   (CORS_ORIGINS는 프론트엔드 배포 후 업데이트)

5. **Create Web Service** 클릭

6. 배포 완료되면 URL 복사 (예: `https://diary-backend.onrender.com`)

---

### 2️⃣ 프론트엔드 배포 (Vercel)

#### A. .env.production 업데이트
```bash
# 위에서 복사한 Render 백엔드 URL로 업데이트
VITE_API_BASE_URL=https://diary-backend.onrender.com/api
```

업데이트 후 커밋:
```bash
git add .env.production
git commit -m "Update production API URL"
git push
```

#### B. Vercel 배포
```bash
# Vercel CLI 설치 (처음 한 번만)
npm i -g vercel

# 로그인
vercel login

# 배포
vercel --prod
```

**설정 질문 답변:**
- Set up and deploy?: **Y**
- Which scope?: 본인 계정 선택
- Link to existing project?: **N**
- What's your project's name?: `diary-frontend` (원하는 이름)
- In which directory is your code located?: `./` (엔터)
- Want to override the settings?: **N**

#### C. Vercel URL 복사
배포 완료 후 표시된 URL (예: `https://diary-frontend.vercel.app`) 복사

---

### 3️⃣ CORS 설정 업데이트

#### Render 백엔드 환경 변수 수정:
1. Render Dashboard → diary-backend 서비스
2. **Environment** 탭
3. `CORS_ORIGINS` 값을 Vercel URL로 변경:
   ```
   https://diary-frontend.vercel.app
   ```
4. **Save Changes** → 자동 재배포

---

### 4️⃣ 데이터베이스 테이블 생성 확인

Render 백엔드가 처음 시작할 때 자동으로 테이블을 생성합니다.
로그에서 확인:
```
INFO:     Application startup complete.
```

---

## ✅ 배포 완료 체크리스트

- [ ] Render PostgreSQL 데이터베이스 생성 완료
- [ ] Render 백엔드 배포 완료 (녹색 상태)
- [ ] Vercel 프론트엔드 배포 완료
- [ ] CORS 설정 업데이트 완료
- [ ] 프론트엔드에서 회원가입 테스트
- [ ] 일기 작성/조회/삭제 테스트
- [ ] 댓글 작성/조회/삭제 테스트

---

## 🔧 문제 해결

### Render 백엔드가 시작하지 않는 경우:
- Logs 탭에서 에러 확인
- DATABASE_URL 환경 변수 확인
- requirements.txt 파일 존재 확인

### CORS 에러가 발생하는 경우:
- Render 환경 변수의 CORS_ORIGINS가 정확한 Vercel URL인지 확인
- 프로토콜(https://) 포함 확인
- 끝에 슬래시(/) 없이 설정

### 프론트엔드가 백엔드에 연결되지 않는 경우:
- .env.production의 VITE_API_BASE_URL 확인
- `/api` 경로가 포함되어 있는지 확인
- 브라우저 개발자 도구 → Network 탭에서 실제 요청 URL 확인

---

## 📱 접속 URL

- **프론트엔드**: https://your-app.vercel.app
- **백엔드 API**: https://diary-backend.onrender.com/api
- **API 문서**: https://diary-backend.onrender.com/docs

---

배포 중 문제가 생기면 언제든 질문하세요! 🚀
