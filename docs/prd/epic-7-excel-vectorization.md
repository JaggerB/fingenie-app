# Epic 7: Excel-first Document Vectorization & Docs Q&A

## Summary
Enable executives to upload multi-tab Excel workbooks (P&L, Balance Sheet, Cash Flow, schedules), index them locally using embeddings, and ask natural-language questions with grounded answers and citations. Default runs fully offline (no external API). Optional LLM polish is enabled only when `OPENAI_API_KEY` is set.

## Goals
- Excel-first ingestion that handles multiple tabs, headers, merged cells, and units
- Multi-representation indexing: text chunks (notes/headers), table chunks (row/time windows), and row-level facts
- Local vector store with metadata filters (doc, sheet, account, period)
- Deterministic numeric answers using pandas with clear citations to sheet ranges
- Optional AI wording polish; never required for core correctness

## Out of Scope (for MVP)
- PDF ingestion (separate epic), enterprise auth/ACLs, cloud vector stores, reranking models

## Success Metrics
- Correctness: ≥95% numeric correctness on a small eval set
- Groundedness: ≥90% answers include 2–5 citations referencing sheet and ranges
- Latency: < 2.5s for typical queries on a 5–8 sheet workbook (local embeddings cached)

## Architecture
- Ingestion: pandas + openpyxl to normalize tables to long-form facts: {doc_id, sheet, account, period, amount, currency}
- Embeddings: sentence-transformers bge-small-en by default (local); optional OpenAI embeddings
- Vector store: Chroma (local disk) with metadata filters
- Retrieval: hybrid (vector + keyword) with strong metadata narrowing (account/sheet/period)
- Answering: deterministic pandas compute + citations; optional LLM polish

## Risks & Mitigations
- Messy spreadsheets: implement resilient table detection, skip totals/blank sections; add unit tests over fixtures
- Cost: default to local embeddings; external APIs are opt-in only
- Performance: chunk by account/time windows; cache embeddings per doc version

## Milestones
- Story 7.1: Excel ingestion & normalization
- Story 7.2: Local vector store + embeddings
- Story 7.3: Docs Q&A tab with grounded answers and citations


