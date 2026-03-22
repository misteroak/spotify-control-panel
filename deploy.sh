#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env.deploy"

# --- Load config ---
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: ${ENV_FILE} not found. Copy .env.deploy.example and fill it in."
  exit 1
fi
source "$ENV_FILE"

: "${GCP_PROJECT:?GCP_PROJECT must be set in .env.deploy}"
: "${GCP_REGION:?GCP_REGION must be set in .env.deploy}"
: "${CLOUD_RUN_SERVICE:?CLOUD_RUN_SERVICE must be set in .env.deploy}"
: "${CLOUDSQL_INSTANCE:?CLOUDSQL_INSTANCE must be set in .env.deploy}"

# --- Pre-flight checks ---
if [[ ! -f "${SCRIPT_DIR}/allowed_emails.txt" ]]; then
  echo "Error: allowed_emails.txt not found. Copy allowed_emails.txt.example and add your email(s)."
  exit 1
fi

echo "Deploying ${CLOUD_RUN_SERVICE} to ${GCP_REGION} (project: ${GCP_PROJECT})"

# --- Build secrets list (public-api-key is optional) ---
SECRETS="SPOTIFY_CLIENT_ID=spotify-client-id:latest,SPOTIFY_CLIENT_SECRET=spotify-client-secret:latest,DATABASE_URL=database-url:latest,GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,SESSION_SECRET=session-secret:latest"

if gcloud secrets describe public-api-key --project "$GCP_PROJECT" &>/dev/null; then
  echo "Found public-api-key secret — enabling public API endpoints"
  SECRETS="${SECRETS},PUBLIC_API_KEY=public-api-key:latest"
fi

# --- Deploy to Cloud Run ---
gcloud run deploy "$CLOUD_RUN_SERVICE" \
  --project "$GCP_PROJECT" \
  --source "$SCRIPT_DIR" \
  --region "$GCP_REGION" \
  --allow-unauthenticated \
  --add-cloudsql-instances="${GCP_PROJECT}:${GCP_REGION}:${CLOUDSQL_INSTANCE}" \
  --set-secrets="$SECRETS"

# --- Set redirect/frontend env vars ---
PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT" --format="value(projectNumber)")
SERVICE_URL="https://${CLOUD_RUN_SERVICE}-${PROJECT_NUMBER}.${GCP_REGION}.run.app"

gcloud run services update "$CLOUD_RUN_SERVICE" \
  --project "$GCP_PROJECT" \
  --region "$GCP_REGION" \
  --update-env-vars="SPOTIFY_REDIRECT_URI=${SERVICE_URL}/auth/callback,FRONTEND_URL=${SERVICE_URL},GOOGLE_REDIRECT_URI=${SERVICE_URL}/google/callback"

echo ""
echo "Deployed to: ${SERVICE_URL}"
echo "Spotify redirect URI: ${SERVICE_URL}/auth/callback"
echo "Google redirect URI:  ${SERVICE_URL}/google/callback"
echo ""
echo "To stop all playback (e.g. from iOS Shortcuts or a webhook):"
echo "  curl -X POST ${SERVICE_URL}/api/public/stop-all \\"
echo "       -H 'Authorization: Bearer <your-public-api-key>'"
