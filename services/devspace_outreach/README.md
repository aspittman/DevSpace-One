# Devspace Outreach

`devspace_outreach` finds local business websites, audits them against niche YAML pain points, drafts review-ready outreach emails, and sends the drafts to the CRM through `/api/ingest`.

## Search provider configuration

Set one provider in `.env` or service config:

```env
DEVSPACE_SEARCH_PROVIDER=bing
BING_SEARCH_API_KEY=...
```

Supported providers:

- `bing`: `BING_SEARCH_API_KEY`
- `google_cse`: `GOOGLE_SEARCH_API_KEY` and `GOOGLE_CSE_ID`
- `serpapi`: `SERPAPI_API_KEY`

## CRM service config example

```json
{
  "auto_discover": true,
  "audit_websites": true,
  "locations": ["Salt Lake City UT", "Provo UT"],
  "results_per_query": 5,
  "max_prospects": 25,
  "max_ingests": 10,
  "min_score_to_save": 60,
  "dry_run": true
}
```

Set `dry_run` to `false` after reviewing the console output from a test run.
