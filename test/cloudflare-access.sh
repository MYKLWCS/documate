#!/usr/bin/env bash
# Regression test: one sign-in through Cloudflare Access (no second login).
#   bash test/cloudflare-access.sh <image>
# A throwaway Postgres + the image on the host network, and a stand-in for Access (key set on 127.0.0.1:9998,
# tokens signed by the image's own node). Checks that a valid Access token on /signin signs the user straight in,
# that a new user from an allowed domain is created, and that a token from the wrong key, for the wrong app,
# expired, from a domain without sign-up, or missing gets no session and no redirect loop.
# Needs docker, curl, python3. Ports 3000, 55432 and 9998 must be free. Leaves nothing running.
set -euo pipefail
IMG=${1:?usage: cloudflare-access.sh <image>}
HERE=$(cd "$(dirname "$0")" && pwd)
PG=postgres:18-alpine@sha256:77f585114c32fbca283dc835b0596f4e52b51b4c6662d7810b2f4084f60a1873
ISS=http://127.0.0.1:9998
AUD=test-staff-app
U=http://localhost:3000
W=$(mktemp -d); chmod 777 "$W"
cleanup() { docker rm -f cfa-t-db cfa-t-app >/dev/null 2>&1 || true; [ -n "${KEYS:-}" ] && kill "$KEYS" 2>/dev/null || true; rm -rf "$W"; }
trap cleanup EXIT
fail() { echo "FAIL: $*" >&2; docker logs --tail 30 cfa-t-app 2>&1 | sed 's/^/  | /' >&2 || true; exit 1; }
sql() { docker exec cfa-t-db psql -p 55432 -U documate -d documate -At -c "$1"; }

cp "$HERE/make-access-tokens.mjs" "$W/"
docker run --rm --network none --user "$(id -u):$(id -g)" -v "$W:/w" --entrypoint node "$IMG" /w/make-access-tokens.mjs /w "$ISS" "$AUD"
# shellcheck disable=SC1091
. "$W/tokens.env"
python3 -m http.server 9998 --bind 127.0.0.1 --directory "$W/www" >/dev/null 2>&1 & KEYS=$!

docker rm -f cfa-t-db cfa-t-app >/dev/null 2>&1 || true
docker run -d --name cfa-t-db --network host -e POSTGRES_USER=documate -e POSTGRES_PASSWORD=pw -e POSTGRES_DB=documate \
  "$PG" -c port=55432 >/dev/null
for _ in $(seq 1 30); do docker exec cfa-t-db pg_isready -p 55432 -U documate >/dev/null 2>&1 && break; sleep 1; done
docker run -d --name cfa-t-app --network host \
  -e NEXT_PUBLIC_WEBAPP_URL=$U -e PORT=3000 \
  -e NEXT_PRIVATE_DATABASE_URL=postgres://documate:pw@127.0.0.1:55432/documate \
  -e NEXTAUTH_SECRET=test-only-secret-0000 -e NEXT_PRIVATE_ENCRYPTION_KEY=test-only-00000000000000000000000 \
  -e NEXT_PRIVATE_ENCRYPTION_SECONDARY_KEY=test-only-11111111111111111111111 \
  -e NEXT_PUBLIC_DISABLE_EMAIL_PASSWORD_SIGNIN=true -e NEXT_PRIVATE_ALLOWED_SIGNUP_DOMAINS=example.com \
  -e DOCUMATE_CF_ACCESS_TEAM_DOMAIN=$ISS -e DOCUMATE_CF_ACCESS_AUD=$AUD \
  "$IMG" >/dev/null
for _ in $(seq 1 90); do curl -fsS -m 3 -o /dev/null $U/api/health 2>/dev/null && break; sleep 2; done
curl -sS -m 5 -o /dev/null $U/api/health || fail "app did not start"
sql "insert into \"User\"(name,email,\"emailVerified\",\"updatedAt\") values ('Owner Person','owner@example.com',now(),now())" >/dev/null

hit() {  # $1 path, $2 token ('' = none) -> "<status> <location> <session|nosession>"
  local jar="$W/jar-$RANDOM" hdr=()
  [ -n "$2" ] && hdr=(-H "Cf-Access-Jwt-Assertion: $2")
  local res; res=$(curl -sS -m 15 -c "$jar" -o /dev/null -w '%{http_code} %{redirect_url}' "${hdr[@]}" "$U$1")
  if grep -q session "$jar" 2>/dev/null; then echo "$res session"; else echo "$res nosession"; fi
}

out=$(hit /signin "$T_EXISTING"); echo "signin with Access token:       $out"
[[ $out == "302 $U/api/auth/cloudflare-access nosession" ]] || fail "signin did not hand over to the Access sign-in"
out=$(hit /signin ""); echo "signin without token:            $out"
[[ $out == 200* ]] || fail "signin without a token should render the page"
out=$(hit "/signin?error=CLOUDFLARE_ACCESS" "$T_EXISTING"); echo "signin after a refusal:          $out"
[[ $out == 200* ]] || fail "a refused sign-in must not loop"

out=$(hit /api/auth/cloudflare-access "$T_EXISTING"); echo "existing user:                   $out"
[[ $out == "302 $U/ session" ]] || fail "existing user was not signed in"
[ "$(sql "select count(*)||' '||max(name) from \"User\" where email='owner@example.com'")" = "1 Owner Person" ] || fail "existing user changed or duplicated"
[ "$(sql "select count(*) from \"UserSecurityAuditLog\" l join \"User\" u on u.id=l.\"userId\" where u.email='owner@example.com' and l.type='SIGN_IN'")" -ge 1 ] || fail "no SIGN_IN audit row"

out=$(hit /api/auth/cloudflare-access "$T_NEW"); echo "new user, allowed domain:        $out"
[[ $out == "302 $U/ session" ]] || fail "new user was not signed in"
[ "$(sql "select name from \"User\" where email='newbie@example.com'")" = "Newbie" ] || fail "new user not created with a name"

for case in T_OTHER_DOMAIN T_WRONG_SIGNER T_WRONG_AUD T_EXPIRED NONE; do
  tok=""; [ "$case" != NONE ] && tok=${!case}
  out=$(hit /api/auth/cloudflare-access "$tok"); printf 'refused %-22s %s\n' "$case:" "$out"
  [[ $out == "302 $U/signin?error=CLOUDFLARE_ACCESS nosession" ]] || fail "$case was not refused"
done
[ "$(sql "select count(*) from \"User\" where email='someone@elsewhere.test'")" = 0 ] || fail "user created for a domain without sign-up"
echo "PASS: Cloudflare Access sign-in (existing and new users signed in once; bad, foreign, expired and missing tokens refused, no loop)"
