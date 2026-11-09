#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="prawobiorca"
LOCATION="europe-central2"
IMAGE="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/prawobiorca-repo/extraction:latest"

echo "Deploying extraction..."
gcloud run deploy extraction \
  --project="${PROJECT_ID}" \
  --region="${LOCATION}" \
  --image="${IMAGE}" \
  --service-account="extraction-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
  --port=8080 \
  --cpu=4 \
  --memory=4Gi \
  --concurrency=1 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=1800 \
  --cpu-boost \
  --ingress=internal \
  --allow-unauthenticated

echo "Deployment completed."
gcloud run services describe extraction \
  --project="${PROJECT_ID}" \
  --region="${LOCATION}" \
  --format="value(urls[0])"
