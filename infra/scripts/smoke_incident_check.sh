#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://localhost}"

echo "[1/3] API health"
curl -fsS "${BASE_URL}/api/health" > /dev/null

echo "[2/3] Create test session"
SESSION_JSON="$(curl -fsS -X POST "${BASE_URL}/api/v1/sessions" -H "Content-Type: application/json" -d '{"learner_id":"incident-check","lesson_topic":"smoke"}')"
SESSION_ID="$(echo "$SESSION_JSON" | sed -n 's/.*"session_id":"\([^"]*\)".*/\1/p')"

if [ "$SESSION_ID" = "" ]; then
  echo "Cannot parse session_id from response"
  exit 1
fi

echo "[3/3] Turn pipeline"
curl -fsS -X POST "${BASE_URL}/api/v1/sessions/${SESSION_ID}/turns" -H "Content-Type: application/json" -d '{"text_input":"kiem tra incident flow"}' > /dev/null

echo "Incident smoke check passed"
