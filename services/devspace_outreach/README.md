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

SerpAPI discovery is capped at 10 search requests to limit credit usage.
The `serpapi_credit_limit` service config may lower the cap for smaller runs, but cannot raise it above 10.

## CRM service config example

```json
{
  "auto_discover": true,
  "audit_websites": true,
  "locations": ["Salt Lake City UT", "Provo UT"],
  "serpapi_credit_limit": 10,
  "results_per_query": 5,
  "max_prospects": 25,
  "max_ingests": 10,
  "min_score_to_save": 60,
  "dry_run": true
}
```

Set `dry_run` to `false` after reviewing the console output from a test run.

## Audit findings payload

Website weaknesses are sent to the CRM as evidence-backed structured findings in
`metadata.detailed_findings`, `metadata.audit.findings`, and `lead.findings`.
Each weakness includes `category`, `label`, `location`, `evidence`,
`why_it_matters`, `recommendation`, and `business_impact`.

Checks the scanner could not verify are recorded in `metadata.audit.checks` with
`status: "not_checked"` and are not used as weaknesses or email claims.
