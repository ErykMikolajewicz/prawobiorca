gcloud container clusters create-auto prawobiorca --region=europe-central2

gcloud services enable artifactregistry.googleapis.com

gcloud artifacts repositories create prawobiorca-repo \
  --repository-format=docker \
  --location=europe-central2


gcloud services enable container.googleapis.com

gcloud iam service-accounts create prawobiorca-deployer \
  --project=prawobiorca \
  --display-name="Prawobiorca app deployer"


gcloud artifacts repositories add-iam-policy-binding "prawobiorca-repo" \
  --location=europe-central2 \
  --member="serviceAccount:prawobiorca-deployer@prawobiorca.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"


gcloud services enable iamcredentials.googleapis.com
gcloud iam service-accounts add-iam-policy-binding "prawobiorca-deployer@prawobiorca.iam.gserviceaccount.com" \
  --member="user:eryk.mikolajewicz@gmail.com" \
  --role="roles/iam.serviceAccountTokenCreator"


gcloud projects add-iam-policy-binding prawobiorca \
  --member="serviceAccount:296630821006-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

gcloud projects add-iam-policy-binding prawobiorca \
  --member="serviceAccount:296630821006-compute@developer.gserviceaccount.com" \
  --role="roles/container.defaultNodeServiceAccount"

gcloud projects remove-iam-policy-binding prawobiorca \
  --member="serviceAccount:296630821006-compute@developer.gserviceaccount.com" \
  --role="roles/editor"

gcloud services enable container.googleapis.com secretmanager.googleapis.com


gcloud secrets create postgres-password \
  --data-file=./deploy/gcp/secrets/postgres-password.txt \
  --replication-policy=automatic

gcloud container clusters update prawobiorca \
  --location=europe-central2 \
  --workload-pool=prawobiorca.svc.id.goog

gcloud container clusters update prawobiorca \
  --location=europe-central2 \
  --enable-secret-manager

gcloud iam service-accounts create prawobiorca-runner \
  --project=prawobiorca \
  --display-name="Prawobiorca app runner"

gcloud secrets add-iam-policy-binding postgres-password \
  --role=roles/secretmanager.secretAccessor \
  --member="principal://iam.googleapis.com/projects/296630821006/locations/global/workloadIdentityPools/prawobiorca.svc.id.goog/subject/ns/default/sa/prawobiorca-runner"

gcloud storage buckets create gs://prawobiorca-regulations \
  --project=prawobiorca \
  --location=europe-central2 \
  --uniform-bucket-level-access

gcloud storage buckets add-iam-policy-binding gs://prawobiorca-regulations \
  --member="serviceAccount:prawobiorca-runner@prawobiorca.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud storage hmac create prawobiorca-runner@prawobiorca.iam.gserviceaccount.com \
  --project=prawobiorca

gcloud secrets create object-storage-access-key \
  --data-file=./deploy/gcp/secrets/object-storage-access-key.txt \
  --replication-policy=automatic

gcloud secrets create object-storage-secret-key \
  --data-file=./deploy/gcp/secrets/object-storage-secret-key.txt \
  --replication-policy=automatic

gcloud secrets add-iam-policy-binding object-storage-access-key \
  --role=roles/secretmanager.secretAccessor \
  --member="principal://iam.googleapis.com/projects/296630821006/locations/global/workloadIdentityPools/prawobiorca.svc.id.goog/subject/ns/default/sa/prawobiorca-runner"

gcloud secrets add-iam-policy-binding object-storage-secret-key \
  --role=roles/secretmanager.secretAccessor \
  --member="principal://iam.googleapis.com/projects/296630821006/locations/global/workloadIdentityPools/prawobiorca.svc.id.goog/subject/ns/default/sa/prawobiorca-runner"

gcloud secrets create jwt-secret-key \
  --data-file=./deploy/gcp/secrets/jwt-secret-key.txt \
  --replication-policy=automatic

gcloud secrets add-iam-policy-binding jwt-secret-key \
  --role=roles/secretmanager.secretAccessor \
  --member="principal://iam.googleapis.com/projects/296630821006/locations/global/workloadIdentityPools/prawobiorca.svc.id.goog/subject/ns/default/sa/prawobiorca-runner"

gcloud storage buckets update gs://prawobiorca-regulations \
  --cors-file=./deploy/gcp/bucket-cors.json

gcloud services enable run.googleapis.com

gcloud iam service-accounts create extraction-service-runner \
  --project=prawobiorca \
  --display-name="Prawobiorca extraction-service runner"

gcloud iam service-accounts create embedding-batch-service-runner \
  --project=prawobiorca \
  --display-name="Prawobiorca embedding-batch-service runner"
