#!/usr/bin/env bash
# Regression test: staff sign-in through an OIDC provider that sends no "name" claim (Cloudflare Access one-time PIN).
#   bash test/oidc-no-name.sh <image>
# Starts a throwaway Postgres + the image on the host network, a mock provider on 127.0.0.1:9999, and checks:
#   1. a new user signs in (302 to the app, session cookie) and gets a name made from the email ("Pat Lee");
#   2. the second sign-in reuses the same OIDC account (no duplicate);
#   3. an existing user with the same email is linked, keeps their name, and no second user is created;
#   4. with NEXT_PRIVATE_OIDC_PROMPT=omit the authorize request carries no prompt (so Access reuses its session).
# Needs docker, curl, python3. Ports 3000, 55432 and 9999 must be free. Leaves nothing running.
set -euo pipefail
IMG=${1:?usage: oidc-no-name.sh <image>}
HERE=$(cd "$(dirname "$0")" && pwd)
PG=postgres:18-alpine@sha256:77f585114c32fbca283dc835b0596f4e52b51b4c6662d7810b2f4084f60a1873
W=$(mktemp -d)
cleanup() { docker rm -f oidc-t-db oidc-t-app >/dev/null 2>&1 || true; [ -n "${MOCK:-}" ] && kill "$MOCK" 2>/dev/null || true; rm -rf "$W"; }
trap cleanup EXIT
fail() { echo "FAIL: $*" >&2; docker logs --tail 30 oidc-t-app 2>&1 | sed 's/^/  | /' >&2 || true; exit 1; }
sql() { docker exec oidc-t-db psql -p 55432 -U documate -d documate -At -c "$1"; }

docker rm -f oidc-t-db oidc-t-app >/dev/null 2>&1 || true
docker run -d --name oidc-t-db --network host -e POSTGRES_USER=documate -e POSTGRES_PASSWORD=pw -e POSTGRES_DB=documate \
  "$PG" -c port=55432 >/dev/null
for _ in $(seq 1 30); do docker exec oidc-t-db pg_isready -p 55432 -U documate >/dev/null 2>&1 && break; sleep 1; done
echo "pat.lee@example.com" > "$W/mock-email"
python3 "$HERE/mock-oidc.py" 9999 "$W/mock-email" 2>"$W/mock.log" & MOCK=$!
docker run -d --name oidc-t-app --network host \
  -e NEXT_PUBLIC_WEBAPP_URL=http://localhost:3000 -e PORT=3000 \
  -e NEXT_PRIVATE_DATABASE_URL=postgres://documate:pw@127.0.0.1:55432/documate \
  -e NEXTAUTH_SECRET=test-only-secret-0000 -e NEXT_PRIVATE_ENCRYPTION_KEY=test-only-00000000000000000000000 \
  -e NEXT_PRIVATE_ENCRYPTION_SECONDARY_KEY=test-only-11111111111111111111111 \
  -e NEXT_PRIVATE_OIDC_WELL_KNOWN=http://127.0.0.1:9999/.well-known/openid-configuration \
  -e NEXT_PRIVATE_OIDC_CLIENT_ID=test-client -e NEXT_PRIVATE_OIDC_CLIENT_SECRET=test-only \
  -e NEXT_PRIVATE_OIDC_SKIP_VERIFY=true -e NEXT_PRIVATE_OIDC_PROMPT=omit \
  -e NEXT_PUBLIC_DISABLE_EMAIL_PASSWORD_SIGNIN=true -e NEXT_PRIVATE_ALLOWED_SIGNUP_DOMAINS=example.com \
  "$IMG" >/dev/null
for _ in $(seq 1 90); do curl -fsS -m 3 -o /dev/null http://localhost:3000/api/health 2>/dev/null && break; sleep 2; done
curl -sS -m 5 -o /dev/null http://localhost:3000/api/health || fail "app did not start"

login() {  # $1 = email; prints the callback status line
  echo "$1" > "$W/mock-email"; local jar="$W/jar-$RANDOM"
  local r url cb
  r=$(curl -sS -c "$jar" -b "$jar" -X POST -H 'Origin: http://localhost:3000' -H 'Content-Type: application/json' -d '{}' \
      http://localhost:3000/api/auth/oauth/authorize/oidc)
  url=$(printf '%s' "$r" | python3 -c 'import json,sys; print(json.load(sys.stdin)["redirectUrl"])') || fail "authorize: $r"
  case "$url" in *prompt=*) fail "authorize URL still sends a prompt: ${url##*\?}";; esac
  cb=$(curl -sS -o /dev/null -w '%{redirect_url}' "$url")
  curl -sS -c "$jar" -b "$jar" -o "$W/body" -w '%{http_code} %{redirect_url}' "$cb"
  grep -q session "$jar" || { echo " (no session cookie; body: $(head -c 120 "$W/body"))"; return 0; }
  echo " session"
}

out=$(login pat.lee@example.com); echo "new user, first sign-in:  $out"
[[ $out == "302 http://localhost:3000/ session" ]] || fail "first sign-in"
out=$(login pat.lee@example.com); echo "new user, second sign-in: $out"
[[ $out == "302 http://localhost:3000/ session" ]] || fail "second sign-in"
name=$(sql "select name from \"User\" where email='pat.lee@example.com'")
[ "$name" = "Pat Lee" ] || fail "name is '$name', expected 'Pat Lee'"
n=$(sql "select count(*) from \"Account\" a join \"User\" u on u.id=a.\"userId\" where u.email='pat.lee@example.com' and a.provider='oidc'")
[ "$n" = 1 ] || fail "$n OIDC accounts for the new user, expected 1"

sql "insert into \"User\"(name,email,\"emailVerified\",\"updatedAt\") values ('Owner Person','owner@example.com',now(),now())" >/dev/null
out=$(login owner@example.com); echo "existing user, sign-in:   $out"
[[ $out == "302 http://localhost:3000/ session" ]] || fail "existing-user sign-in"
r=$(sql "select count(*)||' '||max(name) from \"User\" where email='owner@example.com'")
[ "$r" = "1 Owner Person" ] || fail "existing user: '$r', expected one user named Owner Person"
n=$(sql "select count(*) from \"Account\" a join \"User\" u on u.id=a.\"userId\" where u.email='owner@example.com' and a.provider='oidc'")
[ "$n" = 1 ] || fail "existing user has $n OIDC accounts, expected 1"
echo "PASS: OIDC sign-in without a name claim (new user named 'Pat Lee', re-login reuses the account, existing user linked, no prompt sent)"
