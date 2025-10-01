import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from lilux_app.backend.main import app

client = TestClient(app)

class TestAuthentication:
    """Test authentication functionality"""
    
    def test_login_page_accessible(self):
        """Test that login page is accessible"""
        response = client.get("/login")
        assert response.status_code == 200
        assert "login" in response.text.lower()
    
    def test_invalid_login_returns_401(self):
        """Test that invalid credentials return 401"""
        response = client.post("/login", json={
            "username": "invalid_user",
            "password": "wrong_password"
        })
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_valid_login_returns_token(self):
        """Test that valid credentials return JWT token"""
        response = client.post("/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    def test_dashboard_requires_authentication(self):
        """Test that dashboard requires authentication"""
        response = client.get("/dashboard")
        # Should redirect to login (302) or return 401
        assert response.status_code in [302, 401]
    
    def test_api_endpoints_require_authentication(self):
        """Test that API endpoints require authentication"""
        endpoints = ["/api/portfolio", "/api/trades", "/api/status"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 403  # Forbidden without auth

if __name__ == "__main__":
    pytest.main([__file__, "-v"])