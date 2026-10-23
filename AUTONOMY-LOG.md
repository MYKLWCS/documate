# Autonomy log — Documate

One entry per change to production, written before the change completes.

## 2026-10-23 12:20 UTC — no second one-time PIN when opening Documate

- **Directive:** Michael, 2026-10-23: after signing in and opening Documate it asks for another code, then says the
  account has no access.
- **Evidence:** Access sent a fresh login code for every Documate sign-in (10:59, 11:03, 11:56, 11:58 UTC) and opened a new
  Access session each time, while Chatmate and the staff console reused the existing session without a code. The 11:58
  attempt was refused right after a second code had been mailed: two codes in two minutes, and the one entered no longer
  counted. Documate's OIDC request always carries `prompt` (upstream default "login"; ours was `select_account`), which
  makes Access sign the user in again.
- **Change:** `rebrand.py` edits `packages/auth/server/lib/utils/handle-oauth-authorize-url.ts`: with
  `NEXT_PRIVATE_OIDC_PROMPT=omit` the site-wide OIDC login sends no prompt (organisation portals unchanged).
  `test/oidc-no-name.sh` now also fails if the authorize request carries a prompt (it does on the current image).
  Server `.env`: `NEXT_PRIVATE_OIDC_PROMPT=select_account` → `omit`, deployed together with the new image by digest,
  rollback to `36460d9d…` + the old value if `/api/health` is not healthy.

## 2026-10-23 11:30 UTC — staff sign-in fix ("Missing name") and service accounts

- **Directive:** Michael, 2026-10-23: the Dollar Loanz login on Documate returned
  `{"code":"INVALID_REQUEST","message":"Missing name"}`; "go through all and fix all".
- **Cause:** Cloudflare Access (one-time PIN) sends no `name` claim in its OIDC ID token; upstream Documenso rejects
  any OIDC login without one.
- **Code:** `rebrand.py` edits `packages/auth/server/lib/utils/handle-oauth-callback-url.ts`: the name falls back to
  `preferred_username`, then given + family name, then a name made from the email's local part. Commit f172562,
  build run 39944108462; the new image replaces `040527d5…` by digest with `deploy/deploy.sh` logic (auto-rollback
  if `/api/health` is not healthy).
- **Signing database (`documate-db`):** the two seeded service accounts are renamed from `@sign.dontgetbroke.com` to
  `@documate.dontgetbroke.com`. The code derives their address from `NEXT_PUBLIC_WEBAPP_URL`; after the domain move it
  could no longer find the "deleted account" owner (account/organisation deletion would fail) and would not block those
  addresses at sign-in. Two rows, `email` column only. Rollback: the same `UPDATE` with the hosts swapped.
- **Unchanged:** the two staff invitations to the Dollar Loanz organisation already exist (pending); each person accepts
  on the dashboard after their first sign-in.

## 2026-10-23 — Documenso becomes Documate at documate.dontgetbroke.com

- **Directive:** Michael, 2026-10-23: rebrand the hosted Documenso "Documate", serve it at documate.dontgetbroke.com,
  put the logo in, remove traces of Documenso, change the colour scheme to match, rebrand everywhere, and make it
  better; asked for one sign-in through Cloudflare.
- **Licence:** Documenso is AGPL-3.0; a modified version served over the network must offer its source. This public
  repository is that source and the app links to it. `packages/ee` (commercial licence) is never modified.
- **Version:** upstream v2.20.0 → v2.21.1 (latest release; one additive migration, `EmbedSignature`).
- **Build:** GitHub Actions run 39934352965 → `ghcr.io/myklwcs/documate@sha256:040527d5bd397f5ffd2a9eeb5c34a8a4f10448c4e4ffd76c594d4b03a9c36c0d`
  (commit e202347). Built off the droplet: the upstream build needs ~8 GB RAM; the droplet has 4 GB and serves n8n and Chatmate.
- **Server (dgb-n8n-prod):**
  - new compose project `/opt/dollar-loans/documate` (`documate`, `documate-db`, networks `documate_db` internal + `documate_edge`);
  - database copied with `pg_dump -Fc` → `pg_restore` into a fresh `documate` database; 16 tables compared, all equal;
    dump kept at `/root/documate-migration/signing-20261023T100021Z.dump` (root-only);
  - `.env`: database user/name/host, `NEXT_PUBLIC_WEBAPP_URL`, certificate path, `NEXT_PUBLIC_SUPPORT_EMAIL`,
    `NEXT_PUBLIC_DISABLE_EMAIL_PASSWORD_SIGNIN=true` (Access OIDC is the only sign-in);
  - `dl-backup.sh`, `dl-maint`, `dl-restore-drill` follow the new container names (backups `*.bak-20261023T100324Z`);
  - n8n `compose.yml`: tunnel connector on `documate_edge` instead of `sign_edge` (backup kept, connector never restarted);
  - old stack stopped and removed; its database volume `sign_sign-db-storage` and config kept for rollback.
- **Cloudflare:** DNS `documate` CNAME → tunnel; tunnel `n8n-prod-do` config v8 (documate + sign → `http://documate:3000`);
  redirect rule sign.* → documate.* (301, path + query kept); Access apps renamed "Documate — staff admin",
  "Documate — customer signing pages (bypass, no account)", "Documate staff sign-in (OIDC)" with documate destinations
  and callback added (sign.* entries kept so the redirect host stays covered).
- **Dollar Loans DB:** `dl.set_setting` → `esign_api_base` = `https://documate.dontgetbroke.com/api/v2`,
  `esign_public_base` = `https://documate.dontgetbroke.com` (append-only, effective 10:15 UTC); the lendmate note text in
  `dl.lendmate_sync_work` now says "signed in Documate, documate.dontgetbroke.com". No stored link used the old host.
- **n8n:** E01/E02 renamed to Documate (E02 trigger and reply nodes too), republished; wrong-secret POST → 401.
- **Website:** dollarloanz-website `622967e` frames only `https://documate.dontgetbroke.com/sign/<token>`; dlv2 PR #53.
- **Rollback:** `cd /opt/dollar-loans/.retired-sign-*; docker compose up -d` (old volume intact), tunnel ingress back to
  `http://documenso:3000`, delete the redirect rule, settings back with `dl.set_setting`.
