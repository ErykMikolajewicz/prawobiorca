#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="prawobiorca"
LOCATION="europe-central2"
IMAGE="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/prawobiorca-repo/embedding:latest"

echo "Deploying embedding-batch..."
gcloud run deploy embedding-batch \
  --project="${PROJECT_ID}" \
  --region="${LOCATION}" \
  --image="${IMAGE}" \
  --service-account="embedding-batch-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
  --args='^|^--model_path=/models/mmlw-retrieval-roberta-large-v2|--model_name=mmlw-retrieval-roberta-large-v2|--task=embeddings|--pooling=CLS|--target_device=CPU|--plugin_config={"INFERENCE_NUM_THREADS":8}|--rest_port=8080' \
  --port=8080 \
  --cpu=8 \
  --memory=4Gi \
  --concurrency=1 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300 \
  --cpu-boost \
  --startup-probe=httpGet.path=/v2/health/ready,httpGet.port=8080,periodSeconds=10,failureThreshold=30 \
  --ingress=internal \
  --allow-unauthenticated

echo "Deployment completed."
gcloud run services describe embedding-batch \
  --project="${PROJECT_ID}" \
  --region="${LOCATION}" \
  --format="value(urls[0])"
