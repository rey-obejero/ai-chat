# ADR-0007: One Postgres holds relational, vector, and keyword data

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Postgres serves relational data, embeddings (pgvector), and keyword search
(`tsvector`), with hybrid fusion performed in the application.

## Context

Document retrieval needs both semantic similarity and keyword matching. The
conventional answer is a dedicated vector database alongside the relational
store, which means a second engine to deploy, back up, secure, and keep in sync
with the rows it references.

## Decision

- Postgres carries everything: users, conversations, messages, documents,
  chunks, and embeddings.
- `pgvector` supplies vector similarity; Postgres full-text (`tsvector`)
  supplies keyword search.
- Hybrid fusion (reciprocal rank fusion) runs in the application over the two
  result sets.
- The dev image is `pgvector/pgvector:pg16`, and the `vector` extension is
  created in the first migration.
- Index type, chunking strategy, and fusion weights are empirical decisions made
  against real documents once retrieval is built.
- ParadeDB `pg_search` (true BM25 in Postgres) is noted but not adopted.

## Consequences

- **Easier:** one backup, migration, and connection story; vectors can join
  relational filters in a single query; local development needs one service.
- **Harder:** fusion correctness and ranking quality are our responsibility;
  vector performance tuning is on us.
- **We now live with:** a Postgres deployment whose shape must be chosen when
  retrieval lands, not before.

## Alternatives considered

- **Separate vector database (Qdrant, Weaviate, Pinecone)** — extra operations
  and no relational joins.
- **Elasticsearch / OpenSearch** — capable but a second heavyweight engine.
- **`pg_search`** — closer to true BM25, deferred as a future upgrade.
