# Diary Project (React + FastAPI + PostgreSQL)

## 1) Frontend start

```bash
cd /Users/ymd20.12.13/Documents/diary
npm install
npm run dev
```

Frontend URL:

- http://localhost:5173

## 2) Backend start

```bash
cd /Users/ymd20.12.13/Documents/diary/backend
cp -n .env.example .env
/Users/ymd20.12.13/Documents/diary/.venv/bin/python -m pip install -r requirements.txt
/Users/ymd20.12.13/Documents/diary/.venv/bin/python -m uvicorn app.main:app --app-dir /Users/ymd20.12.13/Documents/diary/backend --port 8080
```

Backend URL:

- http://127.0.0.1:8080

## 3) API

- `GET /api/posts`
- `POST /api/posts`
- `DELETE /api/posts/{post_id}`

## 4) Quick test with curl

```bash
curl http://127.0.0.1:8080/api/posts
```
