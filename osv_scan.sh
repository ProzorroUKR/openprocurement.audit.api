#!/usr/bin/env sh
set -eu

OSV_IMAGE=${OSV_IMAGE:-ghcr.io/google/osv-scanner:v2.6.0}
OSV_FORMAT=${OSV_FORMAT:-vertical}

if [ -x /osv-scanner ]; then
    set -- /osv-scanner
elif command -v osv-scanner >/dev/null 2>&1; then
    set -- osv-scanner
else
    set -- docker run --rm \
        -v "$PWD":/src:ro -w /src \
        -v osv-db:/cache -e XDG_CACHE_HOME=/cache \
        "$OSV_IMAGE"
fi

exec "$@" scan source -r . \
    --offline-vulnerabilities \
    --download-offline-databases \
    --no-resolve \
    --format "$OSV_FORMAT"
