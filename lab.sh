#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ -n "${DOCKER_CONTEXT:-}" ]; then
    exec docker compose "$@"
elif docker --context colima-pr4 info >/dev/null 2>&1; then
    exec docker --context colima-pr4 compose "$@"
else
    exec docker compose "$@"
fi
