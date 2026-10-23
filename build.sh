#!/usr/bin/env bash
# Build the Documate image: pinned upstream Documenso source + rebrand.py, built with upstream's own Dockerfile.
#   ./build.sh                      -> image documate:local
#   IMAGE=ghcr.io/x/documate:tag ./build.sh
# Needs: git, docker. Everything else (python, Pillow, fontTools, Inter, rsvg-convert) runs in a pinned container.
# LOCAL_CA=/path/ca.crt adds a TLS-intercepting proxy CA for sandboxed test builds only (never for release images).
set -euo pipefail
cd "$(dirname "$0")"

TAG=$(sed -n 's/^tag=//p' UPSTREAM)
SHA=$(sed -n 's/^commit=//p' UPSTREAM)
IMAGE=${IMAGE:-documate:local}
TOOLS=alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f   # alpine 3.22
REV=$(git rev-parse HEAD 2>/dev/null || echo unversioned)

rm -rf ./.build
mkdir -p ./.build
git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$TAG" https://github.com/documenso/documenso.git ./.build/src
GOT=$(git -C ./.build/src rev-parse HEAD)
[ "$GOT" = "$SHA" ] || { echo "upstream $TAG is $GOT, expected $SHA — refusing to build" >&2; exit 1; }

net=(); ca=(); prep=""
if [ -n "${LOCAL_CA:-}" ]; then
  net=(--network host -e "https_proxy=${HTTPS_PROXY:-}" -e "http_proxy=${HTTP_PROXY:-}")
  ca=(-v "$LOCAL_CA:/ca.crt:ro")
  prep="cat /ca.crt >> /etc/ssl/certs/ca-certificates.crt && "
fi
docker run --rm "${net[@]}" "${ca[@]}" -v "$PWD:/w" -w /w "$TOOLS" sh -c \
  "${prep}apk add --no-cache -q python3 py3-pillow py3-fonttools font-inter rsvg-convert && (cd brand && python3 gen.py) && python3 rebrand.py .build/src && chown -R $(id -u):$(id -g) .build/src brand"

DOCKERFILE=./.build/src/docker/Dockerfile
build=(--network default)
if [ -n "${LOCAL_CA:-}" ]; then
  cp "$LOCAL_CA" ./.build/src/.local-ca.crt
  sed '0,/^FROM node:24-alpine3.23 AS base$/s//&\nCOPY .local-ca.crt \/tmp\/local-ca.crt\nRUN cat \/tmp\/local-ca.crt >> \/etc\/ssl\/certs\/ca-certificates.crt\nENV NODE_EXTRA_CA_CERTS=\/tmp\/local-ca.crt NPM_CONFIG_CAFILE=\/etc\/ssl\/certs\/ca-certificates.crt/' \
    "$DOCKERFILE" > ./.build/Dockerfile.local
  grep -q 'local-ca.crt' ./.build/Dockerfile.local || { echo "could not add local CA to Dockerfile" >&2; exit 1; }
  DOCKERFILE=./.build/Dockerfile.local
  build=(--network host --build-arg "HTTPS_PROXY=${HTTPS_PROXY:-}" --build-arg "HTTP_PROXY=${HTTP_PROXY:-}"
         --build-arg "https_proxy=${HTTPS_PROXY:-}" --build-arg "http_proxy=${HTTP_PROXY:-}")
fi

docker build "${build[@]}" -f "$DOCKERFILE" \
  --label "org.opencontainers.image.title=Documate" \
  --label "org.opencontainers.image.source=https://github.com/MYKLWCS/documate" \
  --label "org.opencontainers.image.licenses=AGPL-3.0-only" \
  --label "org.opencontainers.image.revision=$REV" \
  --label "documate.upstream=$TAG@$SHA" \
  -t "$IMAGE" ./.build/src

# The shipped client bundle must not say Documenso anywhere a user can read it.
docker run --rm --entrypoint sh "$IMAGE" -c \
  'cd /app/apps/remix/build/client && n=$(grep -rhoE "(^|[^A-Za-z0-9_$-])Documenso([^A-Za-z0-9_$]|$)" . | wc -l); echo "client bundle Documenso mentions: $n"; [ "$n" = 0 ]'
echo "built $IMAGE (upstream $TAG, documate $REV)"
