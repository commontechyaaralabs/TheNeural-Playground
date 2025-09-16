#!/usr/bin/env python3
"""
Local development server for TheNeural Backend API
This script uses local configuration with CORS enabled for localhost
"""

import uvicorn
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import local configuration
from app.config_local import local_settings

if __name__ == "__main__":
    print("🚀 Starting TheNeural Backend API (Local Development Mode)")
    print(f"📍 Environment: {local_settings.node_env}")
    print(f"🌐 CORS Origin: {local_settings.cors_origin}")
    print(f"🔌 Port: {local_settings.port}")
    print(f"📚 GCP Project: {local_settings.google_cloud_project}")
    print()
    print("💡 This server allows CORS from localhost for development")
    print("🔒 For production, use the main config.py instead")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=local_settings.port,
        reload=True,
        log_level="info"
    )
