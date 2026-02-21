#!/usr/bin/env bash
set -euo pipefail

# Linux CI/system deps required by release smoke tests.
# Provides libGL.so.1 for Qt offscreen PNG export.
if ! command -v apt-get >/dev/null 2>&1; then
  echo "Unsupported package manager: expected apt-get" >&2
  exit 1
fi

APT_CMD=(apt-get)
if [ "$(id -u)" -ne 0 ]; then
  if command -v sudo >/dev/null 2>&1; then
    APT_CMD=(sudo apt-get)
  else
    echo "apt-get requires root privileges and sudo is unavailable" >&2
    exit 1
  fi
fi

export DEBIAN_FRONTEND=noninteractive
"${APT_CMD[@]}" update
"${APT_CMD[@]}" install -y --no-install-recommends libgl1
