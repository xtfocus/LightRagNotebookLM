## Kibana Quick Guide: Finding RAG Logs

Use this guide to locate Retrieval-Augmented Generation (RAG) logs emitted by the notebook agent in Kibana.

### 1) Open Discover
- Navigate to Kibana → Discover
- Select data view: `logs-*` (create it in Stack Management → Data Views if missing)
- Set time range to “Last 2 hours” (or expand as needed)

### 2) Basic RAG Filters
- Agent container only:
`container.name:"nextjs-fastapi-template-agent-1" and json.log:*[RAG-*`

- Check both fields (some messages land in `message` instead of `json.log`):
`container.name:"nextjs-fastapi-template-agent-1" and (json.log:*[RAG-* or message:*[RAG-*)`

- If the analyzer blocks wildcard on the analyzed field, use the keyword subfield:
`container.name:"nextjs-fastapi-template-agent-1" and json.log.keyword:*[RAG-*`

- Broad search (no container filter):
`json.log:*[RAG-* or message:*[RAG-*`

### 3) CLI Quick Check (Script)
Use the helper script to query Elasticsearch directly for recent RAG logs. It searches `logs-*` and matches both `message` and `json.log`.

```bash
ELASTIC_PASSWORD="changeme" \
python3 ./scripts/rag_logs_monitor.py \
  --elasticsearch-url http://localhost:9200 \
  --username elastic \
  --index 'logs-*' \
  --time-range 2 \
  --limit 50
```

Notes:
- Increase `--time-range` if needed (value is in hours).
- Omit `--index` to use the default `logs-*`.
- The script prints readable entries and a short RAG flow summary (counts of TOOL/QDRANT lines).

### 3) Helpful Columns
Add the following fields to the table for easier scanning:
- `@timestamp`
- `json.log`
- `message`
- `container.name`
- `log.file.path`

### 4) Field Reference: `json.log` vs `message`
- `json.log`: Raw line from the Docker container JSON log (as ingested by Filebeat). In this stack, structured RAG lines (e.g., `[RAG-TOOL]`, `[RAG-QDRANT]`, `[RAG-STATE-BUILDER]`) typically appear here. Use this field for precise wildcard searches like `json.log:*[RAG-*`.
- `message`: Normalized/log-level message that some Beats integrations populate. Depending on the source, it may be empty or contain unstructured text. Some entries may use `message`, so queries should often check both fields.

Practical guidance:
- Prefer `json.log:*[RAG-*` for RAG-tagged lines
- Fall back to `message:*[RAG-*` if you don’t see expected results

### 5) Common Targets
- State builder propagation: `json.log:"[RAG-STATE-BUILDER]"`
- Tool invocation & query: `json.log:"[RAG-TOOL]"`
- Vector search results: `json.log:"[RAG-QDRANT]"`

### 6) Troubleshooting
- Widen the time picker if nothing appears
- Verify Filebeat is shipping events (acked increases):
  - `curl -s http://localhost:${FILEBEAT_HTTP_PORT:-5066}/stats | grep -E "acked|open_files"`
- Temporarily remove the container filter to confirm any RAG logs:
  - `json.log:*[RAG-* or message:*[RAG-*`

### Notes
- In this stack, container JSON logs are ingested under `json.log`. Many structured RAG lines appear there rather than in the `message` field.

