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
kubectl delete job core-migrations --ignore-not-found
kubectl apply -f deploy/gcp/core-migrations.yaml
kubectl wait --for=condition=complete job/core-migrations --timeout=300s

echo "Applying core..."
kubectl apply -f deploy/gcp/core.yaml

echo "Waiting for core..."
kubectl rollout status deployment/core --timeout=180s

echo "Applying worker..."
kubectl apply -f deploy/gcp/core-worker.yaml

echo "Waiting for worker..."
kubectl rollout status deployment/core-worker --timeout=180s

echo "Applying web..."
kubectl apply -f deploy/gcp/web.yaml

echo "Waiting for web..."
kubectl rollout status deployment/web --timeout=180s

echo "Deployment completed."
