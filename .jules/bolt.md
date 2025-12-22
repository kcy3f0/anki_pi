## 2024-05-23 - Database Indexing Impact
**Learning:** SQLite foreign keys do not automatically create indexes for the child column. Filtering by `deck_id` (FK) causes full table scans.
**Action:** Always verify if FK columns used in WHERE clauses have indexes.
