gcloud services enable iamcredentials.googleapis.com sts.googleapis.com

gcloud iam workload-identity-pools create github \
  --project=prawobiorca \
  --location=global \
  --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc prawobiorca-backend \
  --project=prawobiorca \
  --location=global \
  --workload-identity-pool=github \
  --display-name="prawobiorca-backend repo" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository == 'ErykMikolajewicz/prawobiorca-backend' && assertion.repository_id == '989302666' && assertion.ref == 'refs/heads/main'"

gcloud iam service-accounts add-iam-policy-binding "prawobiorca-deployer@prawobiorca.iam.gserviceaccount.com" \
  --project=prawobiorca \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/296630821006/locations/global/workloadIdentityPools/github/attribute.repository/ErykMikolajewicz/prawobiorca-backend"

gcloud projects add-iam-policy-binding prawobiorca \
  --member="serviceAccount:prawobiorca-deployer@prawobiorca.iam.gserviceaccount.com" \
  --role="roles/container.developer"

gcloud artifacts repositories set-cleanup-policies prawobiorca-repo \
  --project=prawobiorca \
  --location=europe-central2 \
  --policy=./deploy/gcp/artifact-registry-cleanup-policy.json \
  --no-dry-run
