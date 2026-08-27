# Our stack, and why

Maintained by hand. Ping @platform-team before changing anything here.

## Runtime

We are on Python 3.14 because the async task group changes landed there. Do not
downgrade to 3.12; the scheduler in `app/tasks.py` depends on it.

## Web layer

FastAPI, behind uvicorn. We picked it over Litestar in the 2025 review, mostly
for the ecosystem. The write-up is in Notion.

## Data

SQLModel over SQLite for local work, Postgres in staging and production. The
SQLite path is not a supported deployment target.
