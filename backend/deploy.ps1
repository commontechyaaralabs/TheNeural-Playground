# TheNeural Backend - Cloud Run Deployment Script (PowerShell)
# This script builds and deploys the FastAPI backend to Google Cloud Run

# Exit on error
$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = gcloud config get-value project
$SERVICE_NAME = "playground-backend-v2"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  TheNeural Backend - Cloud Run Deployment  " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Project ID:  $PROJECT_ID" -ForegroundColor Cyan
Write-Host "  Service:     $SERVICE_NAME" -ForegroundColor Cyan
Write-Host "  Region:      $REGION" -ForegroundColor Cyan
Write-Host "  Image:       ${IMAGE_NAME}:latest" -ForegroundColor Cyan
Write-Host ""
Write-Host "=============================================" -ForegroundColor Yellow
Write-Host ""

# Step 1: Authenticate Docker with Google Cloud
Write-Host "[1/6] Authenticating Docker with Google Cloud..." -ForegroundColor Blue
gcloud auth configure-docker gcr.io --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Docker authentication failed" -ForegroundColor Red
    exit 1
}
Write-Host "  SUCCESS: Docker authenticated" -ForegroundColor Green
Write-Host ""

# Step 2: Build the Docker image
Write-Host "[2/6] Building Docker image..." -ForegroundColor Blue
Write-Host "  This may take 5-10 minutes..." -ForegroundColor DarkGray
docker build --no-cache --pull -t "${IMAGE_NAME}:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Docker build failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  1. Check requirements.txt for Python 3.12 compatibility" -ForegroundColor White
    Write-Host "  2. Ensure tensorflow>=2.16.1 (not 2.15.0)" -ForegroundColor White
    Write-Host "  3. Run 'docker system prune' to clean up Docker" -ForegroundColor White
    exit 1
}
Write-Host "  SUCCESS: Docker image built" -ForegroundColor Green
Write-Host ""

# Step 3: Push to Google Container Registry
Write-Host "[3/6] Pushing image to Container Registry..." -ForegroundColor Blue
docker push "${IMAGE_NAME}:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Docker push failed" -ForegroundColor Red
    exit 1
}
Write-Host "  SUCCESS: Image pushed" -ForegroundColor Green
Write-Host ""

# Step 4: Deploy to Cloud Run
Write-Host "[4/6] Deploying to Cloud Run..." -ForegroundColor Blue
Write-Host "  This may take 2-3 minutes..." -ForegroundColor DarkGray

# Build the command with proper escaping
$corsOrigins = "https://playground-theneural.vercel.app,https://playground.theneural.in,https://scratch-editor-uaaur7no2a-uc.a.run.app"
$envVars = @(
    "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    "ENVIRONMENT=production"
    "FIRESTORE_DATABASE_ID=(default)"
    "GCS_BUCKET_NAME=playgroundai-470111-data"
    "PUBSUB_TOPIC_NAME=train-jobs"
    "CORS_ORIGIN=$corsOrigins"
    "FIRESTORE_BATCH_SIZE=500"
    "GCS_CHUNK_SIZE=8388608"
) -join ","

gcloud run deploy $SERVICE_NAME `
    --image="${IMAGE_NAME}:latest" `
    --region=$REGION `
    --platform=managed `
    --allow-unauthenticated `
    --service-account="svc-backend@${PROJECT_ID}.iam.gserviceaccount.com" `
    --set-env-vars=$envVars `
    --memory=8Gi `
    --cpu=4 `
    --max-instances=50 `
    --timeout=1500 `
    --port=8080 `
    --execution-environment=gen2 `
    --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Cloud Run deployment failed" -ForegroundColor Red
    exit 1
}
Write-Host "  SUCCESS: Deployed to Cloud Run" -ForegroundColor Green
Write-Host ""

# Step 5: Get the service URL
Write-Host "[5/6] Retrieving service URL..." -ForegroundColor Blue
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to retrieve service URL" -ForegroundColor Red
    exit 1
}
Write-Host "  SUCCESS: Service URL retrieved" -ForegroundColor Green
Write-Host ""

# Step 6: Test the deployment
Write-Host "[6/6] Testing deployment..." -ForegroundColor Blue
Start-Sleep -Seconds 5

try {
    $response = Invoke-RestMethod -Uri "$SERVICE_URL/health" -Method Get -TimeoutSec 30
    Write-Host "  SUCCESS: Health check passed" -ForegroundColor Green
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor DarkGray
}
catch {
    Write-Host "  WARNING: Health check failed (service may still be starting)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT SUCCESSFUL!                    " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  Main:        $SERVICE_URL" -ForegroundColor White
Write-Host "  API Docs:    $SERVICE_URL/docs" -ForegroundColor White
Write-Host "  Health:      $SERVICE_URL/health" -ForegroundColor White
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Cyan
Write-Host "  View logs:" -ForegroundColor White
Write-Host "    gcloud run logs tail $SERVICE_NAME --region $REGION" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Scale service:" -ForegroundColor White
Write-Host "    gcloud run services update $SERVICE_NAME --region $REGION --max-instances 20" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Redeploy:" -ForegroundColor White
Write-Host "    .\deploy.ps1" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Update frontend CORS_ORIGIN to: $SERVICE_URL" -ForegroundColor White
Write-Host "  2. Test the API at: $SERVICE_URL/docs" -ForegroundColor White
Write-Host "  3. Monitor logs for any errors" -ForegroundColor White
Write-Host ""