---
title: Ingest API
description: Push rows into a workbook from scripts, the Chrome extension or n8n with a per-workbook token.
sidebar:
  order: 10
---

The ingest API accepts rows for a workbook without a user session. It is
feature-flagged: set `INGEST_API_ENABLED=1`.

## Create a token

```bash
curl -X POST $OPENGTM/api/v2/workbooks/$WB/ingest-token -H "$AUTH"
```

Requires the editor or admin role. The response contains the plaintext token
(`wbi_…`) **once**; only its hash is stored. Calling the endpoint again
rotates the token and revokes the previous one in the same transaction, so
exactly one token is live per workbook.

## Push rows

```bash
curl -X POST $OPENGTM/api/v2/workbooks/$WB/rows/ingest \
  -H "Authorization: Bearer wbi_…" \
  -H "Idempotency-Key: capture-2026-09-03-001" \
  -H 'Content-Type: application/json' -d '{
    "rows": [
      { "Company": "Acme", "Website": "acme.com", "Work Email": "jane@acme.com" }
    ],
    "dedupe": true
  }'
```

- The token can also be sent as `X-Ingest-Token`. A normal user session with
  `X-Workspace-Id` works too.
- Keys are matched case-insensitively to the workbook's `lead_field`
  columns; unknown keys are kept and listed in `unmapped_keys`.
- At most 500 rows per request (`413` beyond that).
- `dedupe` merges on normalised website domain, else normalised company name.
- With an `Idempotency-Key`, the first response is stored per workbook and
  replayed verbatim for 7 days with the header `Idempotent-Replay: true`.

The [Chrome extension](/integrations/chrome-extension/) and the
[n8n node](/integrations/n8n/) are clients of this endpoint.

## 2GIS → Opportunity Hunter

The repository ships a bridge for `Eroloft/parser-2gis-new`. It converts the
parser's nested JSON into workbook rows with canonical `company`, `website`,
`phone`, `email`, `address`, `city`, `specialization`, and `source=2gis` fields
while retaining useful 2GIS metadata such as rating, review count, rubrics,
WhatsApp and Telegram.

```bash
python scripts/2gis_to_opengtm.py data/2gis/quick.json \
  --city moscow \
  --output data/2gis/quick-opengtm.json
```

To push the normalized rows straight into an instantiated
`manual-ops-arbitrage` workbook:

```bash
export OPENGTM_URL=https://gtm.example.com
export OPENGTM_2GIS_WORKBOOK_ID=<workbook-id>
export OPENGTM_2GIS_INGEST_TOKEN=<wbi-token>
python scripts/2gis_to_opengtm.py data/2gis/quick.json --city moscow --ingest
```

The bridge batches at the API's 500-row limit and sends a stable
`Idempotency-Key` derived from the parser artifact, so retrying the same
artifact is replay-safe in addition to normal workbook deduplication.

The repository workflows `2gis-quick.yml` and `2gis-leads.yml` use the same
bridge. To enable automatic delivery from GitHub Actions, add these repository
Actions secrets:

- `OPENGTM_URL`
- `OPENGTM_2GIS_WORKBOOK_ID`
- `OPENGTM_2GIS_INGEST_TOKEN`

Without all three secrets the workflows stay in artifact-only mode, so public
forks and local tests do not attempt to send data anywhere.
