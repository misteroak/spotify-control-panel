# Deploying to Google Cloud Run

This project uses a single-container deployment via a multi-stage Dockerfile. The frontend is built and served as static files by FastAPI, so only one Cloud Run service is needed.

## 1. Install the Google Cloud CLI

Follow the [official install guide](https://cloud.google.com/sdk/docs/install) for your platform, then authenticate:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

## 2. Enable required GCP APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

## 3. Create a Cloud SQL (Postgres) instance

```bash
# Provision a small Postgres 16 server (takes a few minutes)
gcloud sql instances create spotify-panel-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-east1 \
  --edition=ENTERPRISE

# Create the application database
gcloud sql databases create spotify_panel \
  --instance=spotify-panel-db

# Generate a random password and set it on the default postgres user
DB_PASSWORD=$(openssl rand -base64 24)

gcloud sql users set-password postgres \
  --instance=spotify-panel-db \
  --password="$DB_PASSWORD"

# Grab the connection name (e.g. my-project:us-east1:spotify-panel-db)
CONNECTION_NAME=$(gcloud sql instances describe spotify-panel-db --format="value(connectionName)")

# Store the full connection string in Secret Manager (while $DB_PASSWORD is still in memory)
echo -n "postgresql+asyncpg://postgres:${DB_PASSWORD}@/spotify_panel?host=/cloudsql/${CONNECTION_NAME}" \
  | gcloud secrets create database-url --data-file=-
```

## 4. Store Spotify credentials in Secret Manager

```bash
echo -n "your-client-id" | gcloud secrets create spotify-client-id --data-file=-
echo -n "your-client-secret" | gcloud secrets create spotify-client-secret --data-file=-
```

## 5. Store Google OAuth credentials in Secret Manager

```bash
echo -n "your-google-client-id" | gcloud secrets create google-client-id --data-file=-
echo -n "your-google-client-secret" | gcloud secrets create google-client-secret --data-file=-
echo -n "$(openssl rand -base64 32)" | gcloud secrets create session-secret --data-file=-
```

If any secrets already exist and you need to update them:

```bash
echo -n "new-value" | gcloud secrets versions add spotify-client-id --data-file=-
echo -n "new-value" | gcloud secrets versions add spotify-client-secret --data-file=-

# For database-url, rebuild the connection string with the correct connection name
CONNECTION_NAME=$(gcloud sql instances describe spotify-panel-db --format="value(connectionName)")

echo -n "postgresql+asyncpg://postgres:${DB_PASSWORD}@/spotify_panel?host=/cloudsql/${CONNECTION_NAME}" \
  | gcloud secrets versions add database-url --data-file=-
```

## 6. Grant Secret Manager access to Cloud Run

The default Compute Engine service account used by Cloud Run needs permission to read your secrets:

```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 7. Configure allowed emails

Before deploying, copy the example file and add the Google email addresses that should be able to log in:

```bash
cp allowed_emails.txt.example allowed_emails.txt
```

Edit `allowed_emails.txt` with your email(s), one per line. This file is gitignored but gets baked into the Docker image at build time.

## 8. Deploy to Cloud Run

```bash
PROJECT=$(gcloud config get-value project)

gcloud run deploy spotify-panel \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --add-cloudsql-instances=${PROJECT}:us-east1:spotify-panel-db \
  --set-secrets="SPOTIFY_CLIENT_ID=spotify-client-id:latest,SPOTIFY_CLIENT_SECRET=spotify-client-secret:latest,DATABASE_URL=database-url:latest,GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,SESSION_SECRET=session-secret:latest"
```

On the first deploy, you'll be prompted to create an Artifact Registry repository (`cloud-run-source-deploy`) to store built container images — confirm with **yes**. Cloud Build will then build the image from the Dockerfile and deploy it. This takes a few minutes on the first run.

## 9. Configure the service URL

Once deployed, grab the service URL. The new Cloud Run URL format is deterministic:

```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

SERVICE_URL="https://spotify-panel-${PROJECT_NUMBER}.us-east1.run.app"
```

Set the redirect and frontend URL env vars so the backend knows its own public address:

```bash
gcloud run services update spotify-panel \
  --region us-east1 \
  --update-env-vars="SPOTIFY_REDIRECT_URI=${SERVICE_URL}/auth/callback,FRONTEND_URL=${SERVICE_URL},GOOGLE_REDIRECT_URI=${SERVICE_URL}/google/callback"
```

Then register the redirect URIs in the respective dashboards:

1. **Spotify**: Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), open your app's settings, and add the Spotify redirect URI.
2. **Google**: Go to [Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials), open your OAuth 2.0 client, and add the Google redirect URI.

Print both so you can copy-paste them:

```bash
echo "Spotify: ${SERVICE_URL}/auth/callback"
echo "Google:  ${SERVICE_URL}/google/callback"
```