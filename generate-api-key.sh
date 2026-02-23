#!/usr/bin/env bash
set -euo pipefail

# Generate a URL-safe API key with strong entropy.
if command -v python3 >/dev/null 2>&1; then
  api_key="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
elif command -v openssl >/dev/null 2>&1; then
  api_key="$(openssl rand -base64 64 | tr -d '\n' | tr '/+' '_-' | tr -d '=')"
else
  echo "Error: python3 or openssl is required to generate a secure API key." >&2
  exit 1
fi

echo "API_KEY=${api_key}"
