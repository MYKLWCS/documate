# Documate — progress

Updated 2026-10-23 11:35 UTC.

## Works right now

| What | Proof (run 2026-10-23) |
|---|---|
| Live at https://documate.dontgetbroke.com on `dgb-n8n-prod`, image `ghcr.io/myklwcs/documate@sha256:36460d9d…5d7a` (Documenso v2.21.1 + rebrand, commit f172562, deployed 11:21 UTC) | `curl https://documate.dontgetbroke.com/api/health` → `{"status":"ok",…"database":{"status":"ok"},"certificate":{"status":"ok"}}` |
| No Documenso text in the shipped UI | CI `build.sh`: `client bundle Documenso mentions: 0`; live sign page HTML: 0 mentions, title "Sign Document - Documate" |
| Teal colour scheme, Documate logo, icons, manifest, social image, sign-in background | `curl …/site.webmanifest` → `"name": "Documate"`, `theme_color #0D9488`; `/static/logo.png`, `/apple-touch-icon.png`, `/opengraph-image.jpg` are the Documate artwork |
| Customer signing end to end (no account) | Synthetic contract from template 1 created via API, signed in a headless browser, sealed: PDF 2 pages incl. signing certificate, `pdfsig` → "Signature is Valid" (Dollar Loans LLC certificate); webhooks to n8n E02 returned 200; test document deleted |
| Staff sign-in accepts the Cloudflare Access login (which sends no name) | `bash test/oidc-no-name.sh ghcr.io/myklwcs/documate@sha256:36460d9d…` → `PASS` (also runs in CI before every publish): throwaway copy of this exact image + a mock provider that sends Access's claims (email + sub, no name): new user created as "Pat Lee" from the email, second sign-in reuses the same account, an existing account is linked by email instead of duplicated; the previous image `040527d5…` gives the reported `{"code":"INVALID_REQUEST","message":"Missing name"}` in the same test |
| Service accounts match the new address | `documate-db`: `serviceaccount@` and `deleted-account@documate.dontgetbroke.com` (were `@sign.…`, so account deletion could not find its owner) |
| Staff pages behind Cloudflare Access; one sign-in | `/signin`, `/admin`, `/settings` → 302 to Access; the sign-in page sends staff straight to the Access OIDC login (email/password sign-in off) — authorize URL carries `redirect_uri=https://documate.dontgetbroke.com/api/auth/callback/oidc` |
| Old address keeps working | `https://sign.dontgetbroke.com/<path>?<query>` → 301 to the same path on documate |
| Hourly encrypted backup of the signing database | `dl-backup` 10:03 UTC: `signing-db-20261023-1003.sql.gz.age` from `documate-db`, uploaded to Garage |
| Data carried over | 16 tables compared row for row between the old and new database before the switch (all equal) |

## In flight

- dlv2 PR #53 (signing origin → documate): typecheck and build pass; the security check is queued behind the website's
  Playwright run on the shared self-hosted runner; merges when green.

## Needs Michael

1. Sign in again at documate.dontgetbroke.com (the "Missing name" error is fixed in the running image): the Dollar Loanz login should land you on your existing account and documents (I can't complete your passkey step). Break-glass if it doesn't: set `NEXT_PUBLIC_DISABLE_EMAIL_PASSWORD_SIGNIN=false` in `/opt/dollar-loans/documate/.env` and restart `documate`. The two staff invitations to the Dollar Loanz organisation are waiting on their dashboards after their first sign-in.
2. Old signing database volume `sign_sign-db-storage` and `/opt/dollar-loans/.retired-sign-20261023T100324Z` are kept for rollback; say when they can go.
3. The Documenso-era OIDC client secret was shown once in a session transcript on 2026-10-23; rotate it (new Access SaaS secret into `.env`) when convenient.

## Known broken

- Email still cannot send from Documate (no SMTP / mailbox yet), same as before.
- Signing certificate is self-signed (Adobe shows "validity unknown"); an AATL certificate is a paid upgrade.
- Kept on purpose, not user-visible: `X-Documenso-*` webhook/email headers, the `documenso` supplier/provider keys and audit actor in the Dollar Loans DB, the `DOCUMENSO_DISABLE_TELEMETRY` env name, `@documenso/*` package names inside the image.
