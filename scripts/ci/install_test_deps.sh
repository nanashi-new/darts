#!/usr/bin/env bash
set -euo pipefail

# Linux CI/system deps required by release smoke tests.
# Provides libGL.so.1 for Qt offscreen PNG export.
if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends libgl1
else
  echo "Unsupported package manager: expected apt-get" >&2
  exit 1
fi
