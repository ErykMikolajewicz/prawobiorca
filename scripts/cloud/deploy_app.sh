#!/usr/bin/env bash
set -euo pipefail

echo "Applying shared resources..."
kubectl apply -f deploy/gcp/rbac.yaml
kubectl apply -f deploy/gcp/secrets.yaml
kubectl apply -f deploy/gcp/config.yaml
kubectl apply -f deploy/gcp/ingress.yaml

echo "Applying databases..."
kubectl apply -f deploy/gcp/postgres.yaml

echo "Waiting for database..."
kubectl rollout status deployment/postgres --timeout=180s

echo "Running migrations..."
kubectl delete job prawobiorca-migrations --ignore-not-found
kubectl apply -f deploy/gcp/prawobiorca-migrations.yaml
kubectl wait --for=condition=complete job/prawobiorca-migrations --timeout=300s

echo "Applying backend..."
kubectl apply -f deploy/gcp/prawobiorca-backend.yaml

echo "Waiting for backend..."
kubectl rollout status deployment/prawobiorca-backend --timeout=180s

echo "Applying worker..."
kubectl apply -f deploy/gcp/prawobiorca-worker.yaml

echo "Waiting for worker..."
kubectl rollout status deployment/prawobiorca-worker --timeout=180s

echo "Applying frontend..."
kubectl apply -f deploy/gcp/prawobiorca-frontend.yaml

echo "Waiting for frontend..."
kubectl rollout status deployment/prawobiorca-frontend --timeout=180s

echo "Deployment completed."
