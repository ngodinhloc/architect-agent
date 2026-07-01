#!/bin/sh
set -e

KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
KEYCLOAK_PUBLIC_URL="${KEYCLOAK_PUBLIC_URL:-${KEYCLOAK_URL}}"
REALM="${KEYCLOAK_REALM:-architect-multi-agent}"
REALM_URL="${KEYCLOAK_URL}/realms/${REALM}"
ISSUER="${KEYCLOAK_PUBLIC_URL}/realms/${REALM}"

printf '[kong-init] Waiting for Keycloak at %s ...\n' "$REALM_URL"
until curl -sf "$REALM_URL" > /dev/null 2>&1; do
  sleep 3
done
printf '[kong-init] Keycloak ready.\n'

PUBLIC_KEY=$(curl -sf "$REALM_URL" | jq -r '.public_key')
if [ -z "$PUBLIC_KEY" ] || [ "$PUBLIC_KEY" = "null" ]; then
  printf '[kong-init] ERROR: could not fetch public key from Keycloak\n' >&2
  exit 1
fi

# Fold to 64-char lines, indent 10 spaces for YAML block scalar
PEM_BODY=$(printf '%s' "$PUBLIC_KEY" | fold -w 64 | sed 's/^/          /')

cat > /tmp/kong.yml <<KONG_CONFIG
_format_version: "3.0"

consumers:
  - username: browser-user
    jwt_secrets:
      - key: "${ISSUER}"
        algorithm: RS256
        rsa_public_key: |
          -----BEGIN PUBLIC KEY-----
${PEM_BODY}
          -----END PUBLIC KEY-----

  - username: service-account
    jwt_secrets:
      - key: "${REALM_URL}"
        algorithm: RS256
        rsa_public_key: |
          -----BEGIN PUBLIC KEY-----
${PEM_BODY}
          -----END PUBLIC KEY-----

plugins:
  - name: rate-limiting
    config:
      minute: 100
      policy: local
  - name: jwt
    config:
      key_claim_name: iss
      claims_to_verify:
        - exp
      cookie_names:
        - kc_token

services:
  - name: backend
    url: http://backend:8000
    routes:
      - name: backend-route
        paths:
          - /backend
        strip_path: true

  - name: ticket-service
    url: http://ticket-service:8000
    routes:
      - name: ticket-service-route
        paths:
          - /ticket-service
        strip_path: true

  - name: ticket-agent
    url: http://ticket-agent:8000
    routes:
      - name: ticket-agent-route
        paths:
          - /ticket-agent
        strip_path: true

  - name: mcp-server
    url: http://mcp-server:8000
    routes:
      - name: mcp-server-route
        paths:
          - /mcp-server
        strip_path: true
KONG_CONFIG

printf '[kong-init] Config written to /tmp/kong.yml, starting Kong...\n'
export KONG_DECLARATIVE_CONFIG=/tmp/kong.yml
exec /docker-entrypoint.sh kong docker-start
