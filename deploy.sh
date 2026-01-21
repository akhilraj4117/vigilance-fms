#!/bin/bash

# Google Cloud Run Deployment Script
# Run this in Google Cloud Shell

echo "=== JPHN Transfer System - Google Cloud Deployment ==="

# Check if project is set
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "Error: No project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "Using project: $PROJECT_ID"

# Enable required APIs
echo "Enabling Cloud Run and Cloud Build APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Generate a secret key
SECRET_KEY=$(openssl rand -hex 32)

# Deploy to Cloud Run (with SQLite - simplest option)
echo "Deploying to Cloud Run..."
gcloud run deploy jphn-transfer \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 2 \
    --set-env-vars="FLASK_CONFIG=production,SECRET_KEY=$SECRET_KEY"

# Get the URL
echo ""
echo "=== Deployment Complete ==="
URL=$(gcloud run services describe jphn-transfer --region us-central1 --format="value(status.url)")
echo "Your app is live at: $URL"
echo ""
echo "Login credentials:"
echo "  User ID: admin"
echo "  Password: admin123"
echo ""
echo "IMPORTANT: Change the password after first login!"
