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

# Store the full connection string in Secret Manager (while $DB_PASSWORD is still in memory)
echo -n "postgresql+asyncpg://postgres:${DB_PASSWORD}@/spotify_panel?host=/cloudsql/PROJECT:us-east1:spotify-panel-db" \
  | gcloud secrets create database-url --data-file=-
```

Note the **connection name** for later — it looks like `PROJECT:us-east1:spotify-panel-db`. You can find it with:

```bash
gcloud sql instances describe spotify-panel-db --format="value(connectionName)"
```

## 4. Store Spotify credentials in Secret Manager

```bash
echo -n "your-client-id" | gcloud secrets create spotify-client-id --data-file=-
echo -n "your-client-secret" | gcloud secrets create spotify-client-secret --data-file=-
```

If the secrets already exist and you need to update them:

```bash
echo -n "new-value" | gcloud secrets versions add spotify-client-id --data-file=-
echo -n "new-value" | gcloud secrets versions add spotify-client-secret --data-file=-
echo -n "new-value" | gcloud secrets versions add database-url --data-file=-
```

## 5. Deploy to Cloud Run

Replace `PROJECT:us-east1:spotify-panel-db` with your connection name from step 3:

```bash
gcloud run deploy spotify-panel \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --add-cloudsql-instances=PROJECT:us-east1:spotify-panel-db \
  --set-secrets="SPOTIFY_CLIENT_ID=spotify-client-id:latest,SPOTIFY_CLIENT_SECRET=spotify-client-secret:latest,DATABASE_URL=database-url:latest"
```

Cloud Build will build the container image from the Dockerfile and deploy it. This takes a few minutes on the first run.

## 6. Update the Spotify redirect URI

Once deployed, Cloud Run will give you a service URL (e.g. `https://spotify-panel-xxxxx-uc.a.run.app`).

Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), open your app's settings, and add a redirect URI:

```
https://YOUR_SERVICE_URL/auth/callback
```

## 7. Run database migrations

The migrations need to run against your Cloud SQL instance. The simplest way is via [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy):

```bash
# In one terminal, start the proxy:
cloud-sql-proxy PROJECT:us-east1:spotify-panel-db

# In another terminal, fetch the password and run migrations:
cd backend
DB_PASSWORD=$(gcloud secrets versions access latest --secret=database-url | sed 's|.*://postgres:\(.*\)@.*|\1|')
DATABASE_URL="postgresql+asyncpg://postgres:${DB_PASSWORD}@localhost:5432/spotify_panel" \
  uv run alembic upgrade head
```
