#!/usr/bin/env bash
# Deploy a published Documate image to dgb-n8n-prod. Run from a machine with ssh access (host alias n8n-prod):
#   bash deploy/deploy.sh sha256:<digest>        (the digest is in the GitHub Actions run summary)
# Pulls by digest, backs up compose.yml, swaps only the documate image line, restarts the app, waits for healthy,
# records the digest in DEPLOYED. On an unhealthy start it puts the previous compose.yml back and restarts that.
set -euo pipefail
HOST=${DOCUMATE_HOST:-n8n-prod}
D=${1:?usage: deploy.sh sha256:<digest>}
[[ $D =~ ^sha256:[0-9a-f]{64}$ ]] || { echo "digest must look like sha256:<64 hex>" >&2; exit 2; }
IMG=ghcr.io/myklwcs/documate@$D

ssh -o BatchMode=yes "$HOST" "sudo -n env IMG='$IMG' D='$D' sh -eu" <<'REMOTE'
cd /opt/dollar-loans/documate
docker pull -q "$IMG" >/dev/null
bak=compose.yml.bak-$(date -u +%Y%m%dT%H%M%SZ)
cp -p compose.yml "$bak"
sed -i "s#^\( *image: \)ghcr.io/myklwcs/documate@sha256:[0-9a-f]\{64\}#\1$IMG#" compose.yml
grep -q "image: $IMG" compose.yml || { echo "image line not updated"; cp -p "$bak" compose.yml; exit 1; }
docker compose up -d documate
h=starting
for i in $(seq 1 48); do
  h=$(docker inspect -f '{{.State.Health.Status}}' documate 2>/dev/null || echo missing)
  [ "$h" = healthy ] && break
  sleep 5
done
if [ "$h" != healthy ]; then
  echo "documate is $h after 4 minutes — rolling back to $bak"
  docker logs --tail 40 documate 2>&1 | sed 's/^/  | /'
  cp -p "$bak" compose.yml && docker compose up -d documate
  exit 1
fi
echo "$D" > DEPLOYED
echo "documate healthy on $IMG"
REMOTE
curl -fsS https://documate.dontgetbroke.com/api/health && echo
