# FastAPI Backend (PostgreSQL)

## 1) Environment

Copy `.env.example` to `.env` and adjust if needed.

```bash
cp .env.example .env
```

Default DB is set to:

- `postgresql+psycopg2://diary_user:011643030@localhost:5432/diary_db`

## 2) Install

```bash
pip install -r requirements.txt
```

## 3) Run server

```bash
python -m uvicorn app.main:app --app-dir /Users/ymd20.12.13/Documents/diary/backend --port 8080
```

## 4) API

- `GET /api/posts`
- `POST /api/posts`
- `DELETE /api/posts/{post_id}`
