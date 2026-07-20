# Apollo Outreach CRM workflow

`apollo_outreach` is review-first. Each run scores Apollo prospects and creates
at most five CRM drafts. It does not send recipient email through SMTP.

Run it with:

```bash
PYTHONPATH=. python3 jobs/run_service.py apollo_outreach
```

## CRM Send button contract

The CRM receives everything required to render and send a draft:

- recipient: `contact.email` (also copied to `metadata.email_to`)
- subject: `metadata.email_subject`
- body: `metadata.email_body`
- initial status: `lead.status = drafted`
- outreach status: `metadata.outreach_status = drafted`

When the user clicks **Send**, the CRM should:

1. Validate that the outreach is still `drafted` and has not already been sent.
2. Send the message immediately using the CRM's configured email provider.
3. Only after the provider reports success, set the lead/outreach status to
   `sent` and store `sent_at` plus the provider message ID.
4. On provider failure, leave it as `drafted`, show the error, and allow retry.
5. Make the action idempotent so double-clicking cannot send the same draft twice.

The legacy bot polling endpoints (`/api/bot/approved-outreach` and
`/api/bot/outreach-sent`) are not used by the Apollo job anymore. The CRM Send
button should not wait for another Apollo run.
