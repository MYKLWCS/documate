# Autonomy log — Documate

One entry per change to production, written before the change completes.

## 2026-10-23 16:45 UTC — one sign-in through Cloudflare Access (no second Documate login)

- **Directive:** Michael, 2026-10-23: "fix it so brave works and it all works and make it all work".
- **Evidence:** in Brave the App Launcher opened on the existing Access session, but Documate's OIDC step (the Access
  SaaS app) still demanded a fresh one-time PIN after the prompt fix (16:26 UTC). In Claude's in-app browser the same
  step then failed at Touch ID and Access showed "does not have access" (16:23 UTC).
- **Change:** Documate signs staff in with the identity token Access already attaches to the staff pages
  (`Cf-Access-Jwt-Assertion`): RS256 signature against the team's published keys, issuer, audience = the
  "Documate — staff admin" app, expiry and an email are all required. Existing users are matched by email; a new user
  is created only for an allowed sign-up domain; every sign-in writes the usual SIGN_IN audit row. `/signin` hands over
  to `/api/auth/cloudflare-access`; a refused token falls back to the old sign-in page (no loop). The menu's
  "Sign out" also ends the Access session (`/cdn-cgi/access/logout`), or the sign-in page would sign the user straight
  back in.
- **Tests:** `test/cloudflare-access.sh` (existing and new user signed in once; wrong key, another app's token, expired,
  domain without sign-up and missing token refused; no redirect loop) runs in CI before publish and fails on the
  current image; the verifier passed 13 hand-built token cases locally.
- **Cloudflare:** "Documate — staff admin" gains destination `documate.dontgetbroke.com/api/auth/cloudflare-access`
  (that path was covered by the customer bypass; now only reachable through Access, which adds the token).
- **Server `.env`:** `DOCUMATE_CF_ACCESS_TEAM_DOMAIN=https://dontgetbroke.cloudflareaccess.com`,
  `DOCUMATE_CF_ACCESS_AUD=<staff admin app AUD tag>` (public identifiers, not secrets).
- **Rollback:** remove the two `.env` lines (or redeploy `0e8e9889…`): sign-in falls back to the OIDC step.
- **Done:** Access path added before the deploy (31 destinations, policies unchanged); deployed 19:52 UTC,
  `ghcr.io/myklwcs/documate@sha256:b555794fd55d36f47e2ba23f1450183a190c0e6421885256a62e4b911b38a6d7` (commit c12acd5, both CI
  tests PASS). Live check in Brave 19:54 UTC: `/api/auth/cloudflare-access` verified the real Access token and opened
  Documents (new SIGN_IN audit row, no code asked). `.env` backup `.env.bak-20261023T195124Z`.

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
- **Deployed:** 12:21 UTC, `ghcr.io/myklwcs/documate@sha256:0e8e988928bc0b6dd2e0e180b1d622be14e860ffa99316705b7a282c68afafac`
  (commit 61b7c7f, CI test PASS). `documate-db` restarted with it because it reads the same `.env` (data on its volume,
  healthy again in seconds). Live authorize request carries no `prompt`. Backups `compose.yml.bak-20261023T122039Z`,
  `.env.bak-20261023T122039Z`.

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
