#!/usr/bin/env sh

set -eu

ENV_FILE="${1:-.env}"
SALTBOT_BIN="${SALTBOT_BIN:-saltbot}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing env file: $ENV_FILE" >&2
    exit 1
fi

# Export all variables loaded from .env
set -a
. "./$ENV_FILE"
set +a

# SALTBot configuration
SALT_USER="${WIKIBASE_USER:-}"
SALT_PASSWORD="${WIKIBASE_PASSWORD:-}"
SALT_MEDIAWIKI_API_URL="${MEDIAWIKI_API_URL:-}"
SALT_SPARQL_ENDPOINT_URL="${SPARQL_ENDPOINT_URL:-}"
SALT_WIKIBASE_URL="${WIKIBASE_URL:-}"

if [ -z "$SALT_USER" ]; then
    echo "Missing WIKIBASE_USER in $ENV_FILE" >&2
    exit 1
fi

if [ -z "$SALT_PASSWORD" ]; then
    echo "Missing WIKIBASE_PASSWORD in $ENV_FILE" >&2
    exit 1
fi

printf '%s\n%s\n%s\n%s\n%s\n' \
    "$SALT_USER" \
    "$SALT_PASSWORD" \
    "$SALT_MEDIAWIKI_API_URL" \
    "$SALT_SPARQL_ENDPOINT_URL" \
    "$SALT_WIKIBASE_URL" \
    | "$SALTBOT_BIN" configure

echo "SALTBot configuration created successfully."