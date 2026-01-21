# Deployment Guide - Google Cloud Run

## Prerequisites
1. Google Account (Gmail)
2. Google Cloud CLI installed (or use Cloud Shell in browser)

## Quick Deployment Steps

### Option 1: Using Cloud Shell (Easiest - No Installation Required)

1. **Go to Google Cloud Console**: https://console.cloud.google.com
2. **Sign up/Login** with your Gmail account
3. **Activate $300 free credit** (for new users)
4. **Open Cloud Shell** (button at top right)
5. **Upload your project folder** using Cloud Shell's upload feature
6. **Run these commands**:

```bash
# Navigate to your project
cd web_app

# Set your project ID (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required services
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sqladmin.googleapis.com

# Create PostgreSQL instance (free tier - db-f1-micro)
gcloud sql instances create jphn-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create jphn_transfer --instance=jphn-db

# Set database password
gcloud sql users set-password postgres \
  --instance=jphn-db \
  --password=YOUR_SECURE_PASSWORD

# Build and deploy to Cloud Run
gcloud run deploy jphn-transfer \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars="FLASK_CONFIG=production,SECRET_KEY=$(openssl rand -hex 32)"

# Connect Cloud Run to Cloud SQL
gcloud run services update jphn-transfer \
  --add-cloudsql-instances YOUR_PROJECT_ID:us-central1:jphn-db \
  --set-env-vars="DATABASE_URL=postgresql://postgres:YOUR_SECURE_PASSWORD@/jphn_transfer?host=/cloudsql/YOUR_PROJECT_ID:us-central1:jphn-db"
```

### Option 2: Using Local gcloud CLI

1. **Install Google Cloud CLI**: https://cloud.google.com/sdk/docs/install
2. **Login**: `gcloud auth login`
3. **Follow same commands as Option 1**

## After Deployment

1. **Get your app URL**:
   ```bash
   gcloud run services describe jphn-transfer --region us-central1 --format="value(status.url)"
   ```

2. **Access your app**: The URL will be something like:
   `https://jphn-transfer-xxxxx-uc.a.run.app`

3. **Login credentials** (default):
   - User ID: `admin`
   - Password: `admin123`

## Cost Estimates (Free Tier)

- **Cloud Run**: 2 million requests/month FREE
- **Cloud SQL**: db-f1-micro is ~$7/month (after free trial)
- **Alternative**: Use SQLite (free, but limited to single instance)

## Using SQLite (Completely Free Alternative)

Edit `config.py` to use SQLite:

```python
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///jphn_transfer.db'
```

Then deploy normally. SQLite is good for testing but Cloud SQL is better for production.

## Troubleshooting

### Error: Project not set
```bash
gcloud config set project YOUR_PROJECT_ID
```

### Error: Service not enabled
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### Check logs
```bash
gcloud run logs read jphn-transfer --region us-central1
```

### Update application
```bash
gcloud run deploy jphn-transfer --source . --region us-central1
```

## Security Notes

1. **Change default password** immediately after first login
2. **Use strong SECRET_KEY** (generated automatically in deploy command)
3. **Enable HTTPS** (automatic with Cloud Run)
4. **Set up Cloud SQL backups**:
   ```bash
   gcloud sql instances patch jphn-db --backup-start-time=03:00
   ```

## Monitoring

- **View metrics**: https://console.cloud.google.com/run
- **View logs**: https://console.cloud.google.com/logs
- **Set up alerts**: https://console.cloud.google.com/monitoring

## Need Help?

- Google Cloud Run docs: https://cloud.google.com/run/docs
- Cloud SQL docs: https://cloud.google.com/sql/docs
- Support: https://cloud.google.com/support
