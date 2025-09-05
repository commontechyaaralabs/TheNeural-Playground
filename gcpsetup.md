Here's the clean one-command-per-line setup for Firestore, GCS, Pub/Sub, and Cloud Run (no code or endpoints yet).

## Current Project Setup: playgroundai-470111

1. Set project
bash
Copy
Edit
gcloud config set project playgroundai-470111
2. Enable APIs
bash
Copy
Edit
gcloud services enable firestore.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
3. Create service accounts
bash
Copy
Edit
gcloud iam service-accounts create svc-backend --display-name "Backend SA"
gcloud iam service-accounts create svc-trainer --display-name "Trainer SA"
gcloud iam service-accounts create svc-infer --display-name "Inference SA"
gcloud iam service-accounts create svc-cleaner --display-name "Cleaner SA"
4. Assign roles
Backend SA

bash
Copy
Edit
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-backend@playgroundai-470111.iam.gserviceaccount.com --role=roles/datastore.user
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-backend@playgroundai-470111.iam.gserviceaccount.com --role=roles/pubsub.publisher
Trainer SA

bash
Copy
Edit
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-trainer@playgroundai-470111.iam.gserviceaccount.com --role=roles/storage.objectAdmin
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-trainer@playgroundai-470111.iam.gserviceaccount.com --role=roles/pubsub.subscriber
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-trainer@playgroundai-470111.iam.gserviceaccount.com --role=roles/datastore.user
Inference SA

bash
Copy
Edit
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-infer@playgroundai-470111.iam.gserviceaccount.com --role=roles/storage.objectViewer
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-infer@playgroundai-470111.iam.gserviceaccount.com --role=roles/datastore.user
Cleaner SA

bash
Copy
Edit
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-cleaner@playgroundai-470111.iam.gserviceaccount.com --role=roles/storage.admin
gcloud projects add-iam-policy-binding playgroundai-470111 --member=serviceAccount:svc-cleaner@playgroundai-470111.iam.gserviceaccount.com --role=roles/datastore.user
5. Firestore database
bash
Copy
Edit
gcloud firestore databases create --location=us-central
6. GCS bucket
bash
Copy
Edit
gcloud storage buckets create gs://playgroundai-470111-data --location=us-central1 --uniform-bucket-level-access
Lifecycle policy file (lifecycle.json)

json
Copy
Edit
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": { "age": 7 }
    }
  ]
}
Apply lifecycle policy

bash
Copy
Edit
gcloud storage buckets update gs://playgroundai-470111-data --lifecycle-file=lifecycle.json
7. Pub/Sub topics and subscriptions
bash
Copy
Edit
gcloud pubsub topics create train-jobs
gcloud pubsub subscriptions create trainer-sub --topic=train-jobs --ack-deadline=600
At this point:
✅ Firestore is ready for storing metadata.
✅ GCS is ready for datasets & models.
✅ Pub/Sub is ready for queueing training jobs.
✅ Service accounts & roles are ready for when you deploy backend, trainer, and inference.




things done!!:


✅ Completed GCP Setup for playgroundai-470111
1. Service Accounts Created
Backend SA:
Name: svc-backend
Email: svc-backend@playgroundai-470111.iam.gserviceaccount.com

Trainer SA:
Name: svc-trainer
Email: svc-trainer@playgroundai-470111.iam.gserviceaccount.com

Inference SA:
Name: svc-infer
Email: svc-infer@playgroundai-470111.iam.gserviceaccount.com

Cleaner SA:
Name: svc-cleaner
Email: svc-cleaner@playgroundai-470111.iam.gserviceaccount.com

2. IAM Roles Assigned
Backend:
roles/datastore.user
roles/pubsub.publisher

Trainer:
roles/storage.objectAdmin
roles/pubsub.subscriber
roles/datastore.user

Inference:
roles/storage.objectViewer
roles/datastore.user

Cleaner:
roles/storage.admin
roles/datastore.user

3. Firestore Database
Project ID: playgroundai-470111

Database ID: (default)

Location: us-central1

Mode: Native

Status: ✅ Successfully Created

4. Google Cloud Storage Bucket
Bucket Name: playgroundai-470111-data

URI: gs://playgroundai-470111-data

Location: us-central1

Uniform Bucket-Level Access: Enabled

Lifecycle Rule: Delete objects after 7 days

5. Pub/Sub
Topic: train-jobs

Subscription: trainer-sub

Ack Deadline: 600 seconds

📌 Next Steps for Code Integration
For each service, you will:

Use the service account email and downloaded JSON key file when initializing GCP clients in your backend, trainer, inference, or cleanup scripts.

Connect to:

Firestore → projects/playgroundai-470111/databases/(default)

GCS Bucket → playgroundai-470111-data

Pub/Sub Topic → train-jobs




scale to reduce cost:
gcloud run services update theneural-backend --region us-central1 --max-instances 20


service urls:
Next steps:
   1. Update your frontend CORS_ORIGIN to point to: https://theneural-backend-ed2fe2fxhq-uc.a.run.app
   2. Test the API: https://theneural-backend-ed2fe2fxhq-uc.a.run.app/docs