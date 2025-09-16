#!/usr/bin/env python3
"""
Simple test script for TheNeural Backend API
Run this to verify your setup is working correctly
"""

import requests
import json
from datetime import datetime
from google.cloud import storage
import os

# Configuration
BASE_URL = "http://localhost:8080"
API_BASE = f"{BASE_URL}/api"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("🏠 Testing root endpoint...")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data['message']}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_projects_endpoint():
    """Test the projects endpoint"""
    print("📊 Testing projects endpoint...")
    try:
        response = requests.get(f"{API_BASE}/projects")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Projects endpoint: {len(data['data'])} projects found")
            return True
        else:
            print(f"❌ Projects endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Projects endpoint error: {e}")
        return False

def test_create_project():
    """Test creating a new project"""
    print("➕ Testing project creation...")
    try:
        project_data = {
            "name": f"Test Project {datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "description": "Test project created by API test script",
            "type": "text-recognition",
            "createdBy": "test-user",
            "tags": ["test", "api"],
            "notes": "This is a test project"
        }
        
        response = requests.post(
            f"{API_BASE}/projects",
            json=project_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            project_id = data['data']['id']
            print(f"✅ Project created successfully: {project_id}")
            return project_id
        else:
            print(f"❌ Project creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Project creation error: {e}")
        return None

def test_get_project(project_id):
    """Test getting a project by ID"""
    print(f"📖 Testing get project: {project_id}")
    try:
        response = requests.get(f"{API_BASE}/projects/{project_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Project retrieved: {data['data']['name']}")
            return True
        else:
            print(f"❌ Get project failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get project error: {e}")
        return False

def test_project_status(project_id):
    """Test getting project status"""
    print(f"📊 Testing project status: {project_id}")
    try:
        response = requests.get(f"{API_BASE}/projects/{project_id}/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Project status: {data['data']['status']}")
            return True
        else:
            print(f"❌ Project status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Project status error: {e}")
        return False

def test_add_examples(project_id):
    """Test adding examples to a project"""
    print(f"📝 Testing example addition: {project_id}")
    try:
        examples_data = {
            "examples": [
                {"text": "I love playing soccer", "label": "Sports"},
                {"text": "Basketball is fun", "label": "Sports"},
                {"text": "I scored a goal", "label": "Sports"},
                {"text": "Pizza is delicious", "label": "Food"},
                {"text": "I enjoy cooking", "label": "Food"},
                {"text": "This burger tastes great", "label": "Food"},
                {"text": "I like running", "label": "Sports"},
                {"text": "Swimming is refreshing", "label": "Sports"},
                {"text": "I love pasta", "label": "Food"},
                {"text": "Cooking is my hobby", "label": "Food"}
            ]
        }
        
        response = requests.post(
            f"{API_BASE}/projects/{project_id}/examples",
            json=examples_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Examples added: {data['totalExamples']} total examples")
            print(f"📊 Labels: {data['labels']}")
            return True
        else:
            print(f"❌ Example addition failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Example addition error: {e}")
        return False

def test_start_training(project_id):
    """Test starting training for a project"""
    print(f"🚀 Testing training start: {project_id}")
    try:
        response = requests.post(f"{API_BASE}/projects/{project_id}/train")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Training started: {data['message']}")
            print(f"🆔 Job ID: {data['jobId']}")
            return data['jobId']
        else:
            print(f"❌ Training start failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Training start error: {e}")
        return None

def test_training_status(project_id):
    """Test getting training status"""
    print(f"📊 Testing training status: {project_id}")
    try:
        response = requests.get(f"{API_BASE}/projects/{project_id}/train")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Training status: {data['projectStatus']}")
            if data['currentJob']:
                print(f"🔄 Current job: {data['currentJob']['status']}")
                print(f"📈 Progress: {data['currentJob']['progress']}%")
            return True
        else:
            print(f"❌ Training status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Training status error: {e}")
        return False

def test_gcs_model_exists(project_id):
    """Test if the trained model exists in Google Cloud Storage"""
    print(f"☁️ Testing GCS model existence: {project_id}")
    try:
        # Get GCS bucket name from environment or use default
        bucket_name = os.getenv('GCS_BUCKET_NAME', 'playgroundai-470111-data')
        
        # Initialize GCS client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Expected model path
        model_path = f"models/{project_id}/model_{project_id}.pkl"
        blob = bucket.blob(model_path)
        
        # Check if blob exists
        if blob.exists():
            # Get blob metadata
            blob.reload()
            size_mb = blob.size / (1024 * 1024)
            print(f"✅ Model found in GCS: {model_path}")
            print(f"📦 Size: {size_mb:.2f} MB")
            print(f"🕒 Created: {blob.time_created}")
            return True
        else:
            print(f"❌ Model not found in GCS: {model_path}")
            return False
            
    except Exception as e:
        print(f"❌ GCS model check error: {e}")
        return False

def test_prediction(project_id):
    """Test making predictions with trained model"""
    print(f"🔮 Testing prediction: {project_id}")
    try:
        prediction_data = {
            "text": "I love playing basketball"
        }
        
        response = requests.post(
            f"{API_BASE}/projects/{project_id}/predict",
            json=prediction_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Prediction: {data['label']} (confidence: {data['confidence']}%)")
            if data['alternatives']:
                print(f"🔄 Alternatives: {data['alternatives']}")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 TheNeural Backend API Test Suite")
    print("=" * 50)
    
    # Test basic endpoints
    health_ok = test_health_endpoint()
    root_ok = test_root_endpoint()
    
    if not health_ok or not root_ok:
        print("❌ Basic endpoints failed. Make sure the server is running.")
        print("💡 Start the server with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8080")
        return
    
    # Test API endpoints
    projects_ok = test_projects_endpoint()
    
    if not projects_ok:
        print("❌ Projects endpoint failed. Check your GCP configuration.")
        return
    
    # Test project creation
    project_id = test_create_project()
    
    if project_id:
        # Test getting the project
        test_get_project(project_id)
        
        # Test adding examples
        examples_ok = test_add_examples(project_id)
        
        if examples_ok:
            # Test starting training
            job_id = test_start_training(project_id)
            
            if job_id:
                print(f"🔄 Training job started with ID: {job_id}")
                print("⏳ Waiting for training to complete...")
                
                # Wait a bit and check status
                import time
                time.sleep(5)
                
                # Check training status
                status_ok = test_training_status(project_id)
                
                # If training completed successfully, test GCS model and predictions
                if status_ok:
                    # Check if model exists in GCS
                    print("☁️ Checking if model is saved in Google Cloud Storage...")
                    gcs_ok = test_gcs_model_exists(project_id)
                    
                    # If model exists, test predictions
                    if gcs_ok:
                        print("🔮 Testing predictions with trained model...")
                        test_prediction(project_id)
                
                # Note: In a real scenario, you'd wait for training to complete
                print("💡 To test the complete workflow:")
                print("   1. Start the training worker: python start_worker.py")
                print("   2. Wait for training to complete")
                print("   3. Run: python test_api.py")
                print("   4. Test prediction with: test_prediction(project_id)")
    
    print("\n" + "=" * 50)
    print("🎉 Test suite completed!")
    
    if project_id:
        print(f"📝 Test project created with ID: {project_id}")
        print("💡 You can view it in the API docs at: http://localhost:8080/docs")
        print("🚀 Complete workflow test available in the test functions above")

if __name__ == "__main__":
    main()
