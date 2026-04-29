#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://localhost}"
ADMIN_EMAIL="${BOOTSTRAP_ADMIN_EMAIL:-admin@lumiedu.local}"
ADMIN_PASSWORD="${BOOTSTRAP_ADMIN_PASSWORD:-Admin123!}"

echo "[1/4] API health"
curl -fsS "${BASE_URL}/api/health" > /dev/null

echo "[2/4] Login"
TOKEN_JSON="$(curl -fsS -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")"
TOKEN="$(echo "$TOKEN_JSON" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"

if [ "$TOKEN" = "" ]; then
  echo "Cannot parse access_token from login response"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer ${TOKEN}"

echo "[3/4] Create test session"
SESSION_JSON="$(curl -fsS -X POST "${BASE_URL}/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{"learner_id":"incident-check","lesson_topic":"smoke"}')"
SESSION_ID="$(echo "$SESSION_JSON" | sed -n 's/.*"session_id":"\([^"]*\)".*/\1/p')"

if [ "$SESSION_ID" = "" ]; then
  echo "Cannot parse session_id from response"
  exit 1
fi

echo "[4/4] Turn pipeline"
curl -fsS -X POST "${BASE_URL}/api/v1/sessions/${SESSION_ID}/turns" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{"text_input":"kiem tra incident flow"}' > /dev/null

echo "Incident smoke check passed"
