# Running Documate (dgb-n8n-prod)

| What | Where |
|---|---|
| Public URL | https://documate.dontgetbroke.com (customers sign at `/sign/<token>`, no account) |
| Old URL | https://sign.dontgetbroke.com → 301 to the same path on documate (Cloudflare redirect rule) |
| Server | DigitalOcean `dgb-n8n-prod`, `/opt/dollar-loans/documate` (root-only): `compose.yml`, `.env`, `cert.p12`, `DEPLOYED` |
| Containers | `documate` (app, 1 GB cap) and `documate-db` (Postgres 18, 256 MB cap, database `documate`) |
| Networks | `documate_db` internal (no egress); `documate_edge` shared with the tunnel connector `n8n-cloudflared-1` |
| Tunnel | `n8n-prod-do` ingress `documate.dontgetbroke.com → http://documate:3000` |
| Access | "Documate — staff admin" (sign-in, dashboard, settings, admin… paths); "Documate — customer signing pages (bypass)"; "Documate staff sign-in (OIDC)" for the Dollar Loanz login button |
| Backups | `dl-backup` hourly, logical name `signing-db` (container `documate-db`), encrypted with age, copied to Garage |
| Health | `curl https://documate.dontgetbroke.com/api/health` → `{"status":"ok",…}` |

## Deploy a new build

1. Push to `main` → GitHub Actions builds and publishes `ghcr.io/myklwcs/documate:<commit>`; the run summary shows the digest.
2. `bash deploy/deploy.sh sha256:<digest>` from a machine with the `n8n-prod` ssh alias. It rolls back by itself if
   the new container is not healthy within four minutes.

## Roll back by hand

`/opt/dollar-loans/documate/compose.yml.bak-*` are the previous compose files; copy one back and
`docker compose up -d documate`. Database migrations in Documate releases are additive, so an older image runs on a
newer database.
