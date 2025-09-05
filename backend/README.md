# TheNeural Backend API

**FastAPI-based backend for ML project management with GCP integration**

## 🎯 **Features**

### **Complete ML Workflow:**
- ✅ **Project Management**: Create, read, update, delete ML projects
- ✅ **Example Management**: Add up to 50 text examples per project
- ✅ **Training Pipeline**: Queue-based training with logistic regression
- ✅ **Model Storage**: Automatic model persistence to Google Cloud Storage
- ✅ **Inference**: Real-time predictions with confidence scores
- ✅ **Job Management**: Training job status, progress tracking, cancellation

### **Architecture:**
- **FastAPI**: Modern, fast web framework with automatic API docs
- **Google Cloud**: Firestore, Cloud Storage, Pub/Sub integration
- **Training Service**: Scikit-learn logistic regression with TF-IDF
- **Job Queue**: Asynchronous training with Pub/Sub messaging
- **Worker System**: Scalable training worker architecture

## 📁 **Project Structure**

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and GCP clients
│   ├── models.py            # Pydantic data models
│   ├── services.py          # Business logic layer
│   ├── training_service.py  # Logistic regression training
│   ├── training_job_service.py  # Training job management
│   ├── training_worker.py   # Background worker for training
│   └── api/
│       ├── __init__.py
│       ├── health.py        # Health check endpoints
│       └── projects.py      # Project management endpoints
├── requirements.txt          # Main dependencies
├── requirements-minimal.txt  # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── install.py               # Automated installation script
├── start_all.py             # Start both backend and worker
├── start_worker.py          # Training worker startup script
├── test_api.py              # API testing script
├── Dockerfile               # Container configuration
├── cloudbuild.yaml          # Cloud Build CI/CD
├── env.example              # Environment variables template
└── README.md                # This file
```

## 🚀 **Quick Start**

### **Option 1: Automated Installation (Recommended)**
```bash
cd backend
python install.py
```

### **Option 2: Manual Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install -r requirements-dev.txt
```

### **3. Configure GCP**
```bash
# Copy environment template
cp env.example .env

# Edit .env with your GCP settings
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_BUCKET_NAME=your-bucket-name
PUBSUB_TOPIC_NAME=train-jobs
```

### **4. Start Services**

#### **Option A: Start Everything at Once (Recommended)**
```bash
python start_all.py
```

#### **Option B: Start Manually**
```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Terminal 2: Start training worker
python start_worker.py
```

## 🔄 **Complete Workflow**

### **1. Create Project**
```bash
POST /api/projects
{
  "name": "Text Classifier",
  "description": "Classify text into categories",
  "type": "text-recognition",
  "createdBy": "user@example.com",
  "schoolId": "school-1",
  "classId": "class-1"
}
```

### **2. Add Examples**
```bash
POST /api/projects/{project_id}/examples
{
  "examples": [
    {"text": "I love soccer", "label": "Sports"},
    {"text": "Pizza is great", "label": "Food"},
    {"text": "Basketball is fun", "label": "Sports"}
  ]
}
```

### **3. Start Training**
```bash
POST /api/projects/{project_id}/train
# Returns job ID for tracking
```

### **4. Monitor Training**
```bash
GET /api/projects/{project_id}/train
# Shows job status, progress, and results
```

### **5. Make Predictions**
```bash
POST /api/projects/{project_id}/predict
{
  "text": "I enjoy playing tennis"
}
# Returns: {"label": "Sports", "confidence": 85.2}
```

## 📊 **API Endpoints**

### **Projects**
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### **Examples**
- `POST /api/projects/{id}/examples` - Add text examples
- `GET /api/projects/{id}/examples` - Get all examples

### **Training**
- `POST /api/projects/{id}/train` - Start training job
- `GET /api/projects/{id}/train` - Get training status
- `DELETE /api/projects/{id}/train` - Cancel training

### **Inference**
- `POST /api/projects/{id}/predict` - Make predictions

### **Job Management**
- `GET /api/training/jobs/{job_id}` - Get job status
- `DELETE /api/training/jobs/{job_id}` - Cancel job

## 🧪 **Testing**

### **Run Complete Test Suite**
```bash
python test_api.py
```

### **Test Individual Components**
```python
# Test project creation
project_id = test_create_project()

# Test adding examples
test_add_examples(project_id)

# Test training
job_id = test_start_training(project_id)

# Test prediction
test_prediction(project_id)
```

## 🏗️ **Deployment**

### **Local Development**
```bash
# Use the automated startup
python start_all.py

# Or start manually
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### **Docker**
```bash
docker build -t playgroundai-backend .
docker run -p 8080:8080 playgroundai-backend
```

### **Google Cloud Run**
```bash
# Windows
deploy.bat

# Linux/Mac
./deploy.sh
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_BUCKET_NAME=your-bucket-name
PUBSUB_TOPIC_NAME=train-jobs
FIRESTORE_DATABASE_ID=(default)
CORS_ORIGIN=http://localhost:3000
JWT_SECRET=your-secret-key
```

### **GCP Services Required**
- **Firestore**: Project metadata and training jobs
- **Cloud Storage**: Model artifacts and datasets
- **Pub/Sub**: Training job queue
- **Cloud Run**: API hosting and training workers

## 📈 **Training Architecture**

### **Job Flow**
1. **Queue**: Training request → Pub/Sub topic
2. **Worker**: Background worker processes jobs
3. **Training**: Logistic regression with TF-IDF
4. **Storage**: Model saved to GCS
5. **Update**: Project status updated in Firestore

### **Model Details**
- **Algorithm**: Logistic Regression
- **Features**: TF-IDF vectorization (unigrams + bigrams)
- **Validation**: 80/20 train/validation split
- **Output**: Label + confidence + alternatives

### **Scalability Features**
- **Concurrent Jobs**: Configurable worker pool
- **Job Queuing**: Pub/Sub for reliable message delivery
- **Progress Tracking**: Real-time training progress
- **Error Handling**: Graceful failure and cleanup

## 🚨 **Limits & Constraints**

### **Per Project**
- **Examples**: 3-50 per label, minimum 10 total
- **File Upload**: 100MB maximum
- **Training Time**: Varies by dataset size

### **System**
- **Concurrent Training**: 3 jobs maximum (configurable)
- **Model Storage**: Automatic cleanup after 7 days
- **API Rate Limits**: None currently (add as needed)

## 🔍 **Monitoring & Debugging**

### **Health Checks**
- `GET /health` - Service health status
- `GET /` - API information and docs links

### **Logging**
- Training progress updates
- Job status changes
- Error details and stack traces

### **API Documentation**
- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`
- **OpenAPI Schema**: `http://localhost:8080/openapi.json`

## 🎉 **What's Next?**

### **Phase A (Current)**
- ✅ Complete training pipeline
- ✅ Job queue management
- ✅ Model storage and inference

### **Phase B (Future)**
- 🔄 Vertex AI integration for heavy training
- 🔄 Advanced model types (LSTM, Transformers)
- 🔄 Batch prediction endpoints
- 🔄 Model versioning and A/B testing

### **Phase C (Advanced)**
- 🔄 Multi-tenant school management
- 🔄 Usage quotas and billing
- 🔄 Advanced monitoring and alerting
- 🔄 Automated model retraining

## 🤝 **Contributing**

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Use conventional commit messages

## 📄 **License**

This project is part of TheNeural platform for kid-friendly ML education.
