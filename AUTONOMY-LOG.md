# Autonomy log — Documate

One entry per change to production, written before the change completes.

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
