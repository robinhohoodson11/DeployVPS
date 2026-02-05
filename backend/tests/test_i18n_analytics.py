"""
Test suite for i18n and Analytics features
- Analytics tracking endpoint (/api/analytics/track)
- Admin analytics endpoint (/api/admin/analytics)
- Authentication flows
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "Admin@123"


class TestHealthEndpoints:
    """Basic health check tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health endpoint working")
    
    def test_root_endpoint(self):
        """Test /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print("✅ Root endpoint working")


class TestAnalyticsTracking:
    """Test analytics tracking endpoint (public)"""
    
    def test_track_page_view(self):
        """Test tracking a page view event"""
        payload = {
            "event_type": "page_view",
            "page": "/",
            "country": "BR",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/analytics/track",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✅ Page view tracking working")
    
    def test_track_page_view_with_metadata(self):
        """Test tracking with additional metadata"""
        payload = {
            "event_type": "page_view",
            "page": "/login",
            "country": "US",
            "language": "en",
            "metadata": {"referrer": "google.com"}
        }
        response = requests.post(
            f"{BASE_URL}/api/analytics/track",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✅ Page view with metadata tracking working")
    
    def test_track_different_pages(self):
        """Test tracking multiple different pages"""
        pages = ["/", "/login", "/register", "/dashboard", "/vps"]
        for page in pages:
            payload = {
                "event_type": "page_view",
                "page": page,
                "country": "ES",
                "language": "es"
            }
            response = requests.post(
                f"{BASE_URL}/api/analytics/track",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200
        print(f"✅ Tracked {len(pages)} different pages successfully")


class TestAdminAuthentication:
    """Test admin authentication"""
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("role") == "admin"
        print("✅ Admin login successful")
        return data["access_token"]
    
    def test_admin_me_endpoint(self):
        """Test /api/auth/me returns admin user info"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        token = login_response.json().get("access_token")
        
        # Then get user info
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == ADMIN_EMAIL
        assert data.get("role") == "admin"
        print("✅ Admin /me endpoint working")


class TestAdminAnalytics:
    """Test admin analytics dashboard endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_admin_analytics_endpoint(self, admin_token):
        """Test /api/admin/analytics returns correct data structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify page_views structure
        assert "page_views" in data
        page_views = data["page_views"]
        assert "total" in page_views
        assert "today" in page_views
        assert "week" in page_views
        assert "month" in page_views
        
        # Verify unique_visitors structure
        assert "unique_visitors" in data
        unique_visitors = data["unique_visitors"]
        assert "today" in unique_visitors
        assert "week" in unique_visitors
        assert "month" in unique_visitors
        
        # Verify conversions structure
        assert "conversions" in data
        conversions = data["conversions"]
        assert "total" in conversions
        assert "month" in conversions
        assert "week" in conversions
        assert "rate" in conversions
        
        # Verify lists
        assert "top_pages" in data
        assert isinstance(data["top_pages"], list)
        
        assert "top_countries" in data
        assert isinstance(data["top_countries"], list)
        
        assert "daily_views" in data
        assert isinstance(data["daily_views"], list)
        
        assert "recent_activity" in data
        assert isinstance(data["recent_activity"], list)
        
        print("✅ Admin analytics endpoint returns correct structure")
        print(f"   - Page views (month): {page_views.get('month', 0)}")
        print(f"   - Unique visitors (month): {unique_visitors.get('month', 0)}")
        print(f"   - Conversion rate: {conversions.get('rate', 0)}%")
    
    def test_admin_analytics_requires_auth(self):
        """Test /api/admin/analytics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code in [401, 403]  # Both are valid for unauthorized
        print("✅ Admin analytics correctly requires authentication")
    
    def test_admin_analytics_requires_admin_role(self):
        """Test /api/admin/analytics requires admin role"""
        # Create a regular user and try to access admin endpoint
        test_email = f"test_user_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register regular user
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": test_email,
                "password": "TestPass123",
                "name": "Test User"
            }
        )
        
        if register_response.status_code == 201:
            # Login as regular user
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": test_email, "password": "TestPass123"}
            )
            
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                
                # Try to access admin analytics
                response = requests.get(
                    f"{BASE_URL}/api/admin/analytics",
                    headers={"Authorization": f"Bearer {token}"}
                )
                # Should be forbidden for non-admin users
                assert response.status_code in [401, 403]
                print("✅ Admin analytics correctly restricts non-admin users")
            else:
                # User might need approval
                print("⚠️ Regular user login failed (may need approval)")
        else:
            print("⚠️ Could not create test user for role check")


class TestAdminUsers:
    """Test admin users endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_admin_users_list(self, admin_token):
        """Test /api/admin/users returns user list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Admin users endpoint working - {len(data)} users found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
