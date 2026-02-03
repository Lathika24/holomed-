"""API client for communicating with the backend"""

import requests
from typing import Optional, Dict, List
from pathlib import Path
import os
from config import Config

class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or Config.API_BASE_URL).rstrip('/')
        self.token: Optional[str] = None
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
    
    def _headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def register(self, username: str, email: str, password: str) -> Dict:
        """Register a new user"""
        response = requests.post(
            f"{self.base_url}/api/auth/register",
            json={"username": username, "email": email, "password": password},
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    def login(self, username: str, password: str) -> Dict:
        """Login and get token"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            data={"username": username, "password": password},
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        if "access_token" in data:
            self.token = data["access_token"]
        return data
    
    def get_current_user(self) -> Dict:
        """Get current user info"""
        response = requests.get(
            f"{self.base_url}/api/auth/me",
            headers=self._headers(),
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    def upload_model(self, file_path: str, name: str = None) -> Dict:
        """Upload a 3D model"""
        if name is None:
            name = Path(file_path).name
        
        with open(file_path, 'rb') as f:
            files = {"file": (Path(file_path).name, f, "application/octet-stream")}
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            response = requests.post(
                f"{self.base_url}/api/models/upload",
                files=files,
                headers=headers,
                timeout=120  # Longer timeout for file uploads
            )
            response.raise_for_status()
            return response.json()
    
    def get_models(self) -> List[Dict]:
        """Get list of user's models"""
        response = requests.get(
            f"{self.base_url}/api/models",
            headers=self._headers(),
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    def get_model(self, model_id: str) -> Dict:
        """Get a specific model by ID"""
        response = requests.get(
            f"{self.base_url}/api/models/{model_id}",
            headers=self._headers(),
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model"""
        response = requests.delete(
            f"{self.base_url}/api/models/{model_id}",
            headers=self._headers(),
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        return True
    
    def download_model_file(self, model: Dict, save_path: str) -> bool:
        """Download a model file from the server
        
        The model dict should contain 'file_path' which is the path
        to the file. The backend stores it as 'uploads/filename' format.
        """
        # Get file_path from model
        # Backend stores: uploads/userid_timestamp_filename.ext
        file_path = model.get('file_path', '')
        
        # Extract just the filename (basename)
        # This handles both 'uploads/filename' and just 'filename' formats
        filename = os.path.basename(file_path)
        
        if not filename:
            raise ValueError("Invalid file path in model data")
        
        # Construct the download URL
        # The backend mounts /uploads as static files
        download_url = f"{self.base_url}/uploads/{filename}"
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        response = requests.get(
            download_url,
            headers=headers,
            timeout=120,  # Longer timeout for file downloads
            stream=True
        )
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
