-- Substring search over conversation titles and message content is `ILIKE
-- '%term%'`, backed by trigram GIN indexes (migration 0005). Creating an
-- extension needs a privilege the application's own user may not hold, so it
-- is created here, by the superuser the entrypoint starts as. The migration's
-- `CREATE EXTENSION IF NOT EXISTS pg_trgm` is then a no-op.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
