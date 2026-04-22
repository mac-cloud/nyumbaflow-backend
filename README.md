# NyumbaFlow Backend (FastAPI + Postgres)

Standalone Python API. No Supabase, no external auth — JWT-based auth
backed by your own Postgres database.

## Quick start

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set DATABASE_URL + JWT_SECRET

uvicorn app.main:app --reload
```


psql -U nyumba_user -d nyumbaflow

API will be available at http://localhost:8000
Interactive docs: http://localhost:8000/docs

## Database

Tables are auto-created on first startup via `Base.metadata.create_all`.

If you'd rather create them manually, run `Backend/sql/schema.sql`
against your Postgres database.

## Auth

- `POST /auth/signup` — create account (first user becomes `admin`)
- `POST /auth/login` — returns `{ access_token }`
- `GET /auth/me` — current user + roles + profile

Send the JWT as `Authorization: Bearer <token>` on every protected request.

## Roles

`admin`, `manager`, `caretaker`, `accountant`, `tenant`. Admin can assign
roles via `POST /users/{user_id}/roles`.
