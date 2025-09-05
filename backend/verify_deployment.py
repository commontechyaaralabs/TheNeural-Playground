#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies that the backend deployment has the correct enum values and can handle the API properly.
"""

import requests
import json
import sys

def test_enum_values():
    """Test that the ProjectType enum includes image-recognition-teachable-machine"""
    try:
        # Test the debug endpoint to see if it works
        base_url = "https://playgroundai-backend-773717965404.us-central1.run.app"
        
        # Test health endpoint first
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code != 200:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
        
        print("✅ Health check passed")
        
        # Test creating a guest session
        session_response = requests.post(f"{base_url}/api/guests/session")
        if session_response.status_code != 201:
            print(f"❌ Session creation failed: {session_response.status_code}")
            print(f"Response: {session_response.text}")
            return False
        
        session_data = session_response.json()
        session_id = session_data['data']['session_id']
        print(f"✅ Session created: {session_id}")
        
        # Test creating an image-recognition-teachable-machine project
        project_data = {
            "name": "Test Image Project",
            "description": "Test project for deployment verification",
            "type": "image-recognition-teachable-machine",
            "teachable_machine_link": "https://teachablemachine.withgoogle.com/models/test123/"
        }
        
        project_response = requests.post(
            f"{base_url}/api/guests/session/{session_id}/projects",
            json=project_data,
            headers={"Content-Type": "application/json"}
        )
        
        if project_response.status_code != 201:
            print(f"❌ Image recognition project creation failed: {project_response.status_code}")
            print(f"Response: {project_response.text}")
            return False
        
        print("✅ Image recognition project created successfully")
        
        # Test getting projects
        projects_response = requests.get(f"{base_url}/api/guests/session/{session_id}/projects")
        if projects_response.status_code != 200:
            print(f"❌ Getting projects failed: {projects_response.status_code}")
            print(f"Response: {projects_response.text}")
            return False
        
        projects_data = projects_response.json()
        print(f"✅ Retrieved {len(projects_data['data'])} projects")
        
        # Verify the project has the correct type
        if projects_data['data']:
            project = projects_data['data'][0]
            if project['type'] != 'image-recognition-teachable-machine':
                print(f"❌ Project type mismatch: expected 'image-recognition-teachable-machine', got '{project['type']}'")
                return False
            print("✅ Project type is correct")
        
        print("🎉 All tests passed! Deployment is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False

def test_fix_endpoint(session_id):
    """Test the fix endpoint for a specific session"""
    try:
        base_url = "https://playgroundai-backend-773717965404.us-central1.run.app"
        
        print(f"🔧 Testing fix endpoint for session: {session_id}")
        
        fix_response = requests.post(f"{base_url}/api/guests/debug/fix-project-types/{session_id}")
        
        if fix_response.status_code == 200:
            fix_data = fix_response.json()
            print(f"✅ Fix endpoint successful")
            print(f"   Fixed {fix_data.get('fixed_count', 0)} projects")
            print(f"   Total docs: {fix_data.get('total_docs', 0)}")
            if fix_data.get('errors'):
                print(f"   Errors: {fix_data['errors']}")
            return True
        else:
            print(f"❌ Fix endpoint failed: {fix_response.status_code}")
            print(f"Response: {fix_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Fix endpoint test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying deployment...")
    success = test_enum_values()
    
    if not success:
        print("\n🔧 Testing fix endpoint as fallback...")
        # Test with the problematic session ID
        fix_success = test_fix_endpoint("session_efc5177ce60c4d8d")
        if fix_success:
            print("✅ Fix endpoint works - you can use it to fix existing data")
        else:
            print("❌ Fix endpoint also failed - need to redeploy")
    
    sys.exit(0 if success else 1)
