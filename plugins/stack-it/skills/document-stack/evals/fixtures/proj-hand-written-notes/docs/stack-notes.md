# Why we picked these

Maintained by hand. This is the argument, not a generated reference; ping @platform-team
before rewriting any of it.

## FastAPI over Litestar

We ran both for a sprint in the 2025 review. FastAPI won on ecosystem, not on speed. The
write-up with the numbers is in Notion.

## SQLModel over plain SQLAlchemy

One model class for the table and the response body. We accept that SQLModel is thin and
occasionally lags SQLAlchemy releases; the duplication it removes is worth it here.

## No migration tool

The lifespan handler creates the tables. When this service grows a second writer, that
decision gets revisited and Alembic goes in.
