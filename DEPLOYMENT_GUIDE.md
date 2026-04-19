# 배포 가이드

## 🚀 추천 배포 방법

### 1. **Vercel (추천 - 가장 쉬움)**

#### 프론트엔드 (Vite/React)
- ✅ 무료 호스팅
- ✅ 자동 HTTPS
- ✅ Git 연동 시 자동 배포
- ✅ 글로벌 CDN

**배포 방법:**
```bash
# Vercel CLI 설치
npm i -g vercel

# 프론트엔드 배포
cd /Users/ymd20.12.13/Documents/diary
vercel
```

**설정:**
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

#### 백엔드 (FastAPI + PostgreSQL)
⚠️ **주의**: Vercel은 서버리스 함수만 지원하므로 PostgreSQL과 함께 사용 불가

**대안:**
- **Render** (추천)
- **Railway**
- **Fly.io**

---

### 2. **Render (추천 - 풀스택)**

#### 장점:
- ✅ 무료 PostgreSQL 데이터베이스 제공
- ✅ 프론트/백엔드 모두 배포 가능
- ✅ 자동 HTTPS
- ✅ Git 연동 자동 배포

#### 백엔드 배포:

1. **Render 계정 생성**: https://render.com

2. **PostgreSQL 데이터베이스 생성:**
   - Dashboard → New → PostgreSQL
   - Name: `diary-db`
   - Region: Singapore (가장 가까운 지역)
   - 무료 플랜 선택

3. **백엔드 Web Service 생성:**
   - Dashboard → New → Web Service
   - Connect GitHub 저장소
   - 설정:
     ```
     Name: diary-backend
     Region: Singapore
     Branch: main
     Root Directory: backend
     Runtime: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

4. **환경 변수 설정:**
   - Environment Variables 추가:
     ```
     DATABASE_URL=<PostgreSQL Internal Database URL 복사>
     CORS_ORIGINS=https://your-frontend.vercel.app
     ```

#### 프론트엔드 배포:

**옵션 A - Vercel:**
```bash
vercel
```

**옵션 B - Render Static Site:**
- Dashboard → New → Static Site
- 설정:
  ```
  Build Command: npm run build
  Publish Directory: dist
  ```

5. **프론트엔드 환경 변수:**
   - `.env.production` 파일 생성:
     ```
     VITE_API_BASE_URL=https://diary-backend.onrender.com/api
     ```

---

### 3. **Railway (간편함)**

#### 장점:
- ✅ 매우 간단한 배포
- ✅ PostgreSQL 자동 설정
- ✅ 한 플랫폼에서 프론트/백엔드 모두 관리
- ✅ $5/월 무료 크레딧

**배포 방법:**
```bash
# Railway CLI 설치
npm i -g @railway/cli

# 로그인
railway login

# 프로젝트 생성
railway init

# PostgreSQL 추가
railway add

# 배포
railway up
```

---

### 4. **Fly.io (고급 사용자)**

#### 장점:
- ✅ 무료 PostgreSQL
- ✅ 여러 지역 배포 가능
- ✅ Docker 기반

**배포 방법:**
```bash
# Fly CLI 설치
curl -L https://fly.io/install.sh | sh

# 로그인
flyctl auth login

# 앱 생성 및 배포
flyctl launch
```

---

## 📋 배포 전 체크리스트

### 백엔드:
- [x] `requirements.txt` 최신화
- [ ] 환경 변수 설정 (.env → 배포 플랫폼)
- [ ] CORS 설정 확인
- [ ] 데이터베이스 마이그레이션

### 프론트엔드:
- [ ] API 엔드포인트 변경 (로컬 → 배포 URL)
- [ ] 빌드 테스트 (`npm run build`)
- [ ] 환경 변수 설정

---

## 🎯 가장 쉬운 조합

### 초보자 추천:
1. **백엔드**: Render (무료 PostgreSQL + Python)
2. **프론트엔드**: Vercel (무료 정적 호스팅)

### 시간이 많지 않을 때:
1. **전체**: Railway (한 곳에서 모두 관리)

### 무료로 계속 사용:
1. **백엔드**: Render Free (슬립 모드 있음)
2. **프론트엔드**: Vercel

---

## 필요한 파일들

### 1. `backend/requirements.txt` (이미 존재)
```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
python-dotenv==1.0.1
```

### 2. `.env.production` (프론트엔드 루트)
```bash
VITE_API_BASE_URL=https://your-backend-url.com/api
```

### 3. `vercel.json` (프론트엔드 루트, 옵션)
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

---

배포 중 문제가 생기면 언제든 질문하세요! 🚀
