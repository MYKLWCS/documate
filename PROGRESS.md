# Documate — progress

Updated 2026-10-23 10:30 UTC.

## Works right now

| What | Proof (run 2026-10-23) |
|---|---|
| Live at https://documate.dontgetbroke.com on `dgb-n8n-prod`, image `ghcr.io/myklwcs/documate@sha256:040527d5…6c0d` (Documenso v2.21.1 + rebrand, commit e202347) | `curl https://documate.dontgetbroke.com/api/health` → `{"status":"ok",…"database":{"status":"ok"},"certificate":{"status":"ok"}}` |
| No Documenso text in the shipped UI | CI `build.sh`: `client bundle Documenso mentions: 0`; live sign page HTML: 0 mentions, title "Sign Document - Documate" |
| Teal colour scheme, Documate logo, icons, manifest, social image, sign-in background | `curl …/site.webmanifest` → `"name": "Documate"`, `theme_color #0D9488`; `/static/logo.png`, `/apple-touch-icon.png`, `/opengraph-image.jpg` are the Documate artwork |
| Customer signing end to end (no account) | Synthetic contract from template 1 created via API, signed in a headless browser, sealed: PDF 2 pages incl. signing certificate, `pdfsig` → "Signature is Valid" (Dollar Loans LLC certificate); webhooks to n8n E02 returned 200; test document deleted |
| Staff pages behind Cloudflare Access; one sign-in | `/signin`, `/admin`, `/settings` → 302 to Access; the sign-in page sends staff straight to the Access OIDC login (email/password sign-in off) — authorize URL carries `redirect_uri=https://documate.dontgetbroke.com/api/auth/callback/oidc` |
| Old address keeps working | `https://sign.dontgetbroke.com/<path>?<query>` → 301 to the same path on documate |
| Hourly encrypted backup of the signing database | `dl-backup` 10:03 UTC: `signing-db-20261023-1003.sql.gz.age` from `documate-db`, uploaded to Garage |
| Data carried over | 16 tables compared row for row between the old and new database before the switch (all equal) |

## In flight

- dlv2 PR #53 (signing origin → documate) waiting for its required checks, then merge.
- Repo/doc sweep of the remaining "Documenso"/sign.dontgetbroke.com mentions in n8n-flows-for-dollar-loans, n8n-workflows and lendmate runbooks.

## Needs Michael

1. First staff sign-in on documate.dontgetbroke.com: confirm the Dollar Loanz login lands you in Documate without a second screen (I can't complete your passkey step). Break-glass if it doesn't: set `NEXT_PUBLIC_DISABLE_EMAIL_PASSWORD_SIGNIN=false` in `/opt/dollar-loans/documate/.env` and restart `documate`.
2. Old signing database volume `sign_sign-db-storage` and `/opt/dollar-loans/.retired-sign-20261023T100324Z` are kept for rollback; say when they can go.
3. The Documenso-era OIDC client secret was shown once in a session transcript on 2026-10-23; rotate it (new Access SaaS secret into `.env`) when convenient.

## Known broken

- Email still cannot send from Documate (no SMTP / mailbox yet), same as before.
- Signing certificate is self-signed (Adobe shows "validity unknown"); an AATL certificate is a paid upgrade.
- Kept on purpose, not user-visible: `X-Documenso-*` webhook/email headers, the `documenso` supplier/provider keys and audit actor in the Dollar Loans DB, the `DOCUMENSO_DISABLE_TELEMETRY` env name, `@documenso/*` package names inside the image.
