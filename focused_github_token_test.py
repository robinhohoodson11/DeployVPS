import requests
import sys
import json
from datetime import datetime

class FocusedGitHubTokenTester:
    def __init__(self):
        self.base_url = "https://github-auth-retry.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def get_admin_token(self):
        """Get admin token by registering the first user"""
        print("🔐 Setting up authentication...")
        
        timestamp = datetime.now().strftime('%H%M%S')
        admin_data = {
            "name": f"Token Admin {timestamp}",
            "email": f"tokenadmin{timestamp}@test.com",
            "password": "admin123456"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/register", json=admin_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    print(f"✅ Admin user created with role: {data['user'].get('role')}")
                    return True
                elif data.get('status') == 'pending':
                    print("ℹ️ User is pending - admin already exists, trying to get existing admin")
                    # Try to use a known admin account
                    return self._try_existing_admin()
            else:
                print(f"❌ Registration failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {str(e)}")
            return False
    
    def _try_existing_admin(self):
        """Try to login with potential existing admin accounts"""
        # Common admin patterns to try
        admin_attempts = [
            {"email": "admin@admin.com", "password": "Admin@123"},
            {"email": "admin@example.com", "password": "admin123456"},
            {"email": "test@example.com", "password": "testpass123"}
        ]
        
        for attempt in admin_attempts:
            try:
                response = requests.post(f"{self.api_url}/auth/login", json=attempt, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'access_token' in data and data.get('user', {}).get('role') == 'admin':
                        self.token = data['access_token']
                        print(f"✅ Logged in as existing admin: {attempt['email']}")
                        return True
            except:
                continue
                
        print("❌ Could not authenticate as admin")
        return False

    def test_github_token_functionality(self):
        """Test GitHub token endpoints with proper setup"""
        print("\n🧪 Testing GitHub Token Endpoints...")
        
        # Step 1: Create VPS
        vps_data = {
            "name": "GitHub Test VPS",
            "host": "test.example.com",
            "port": 22,
            "username": "root",
            "auth_type": "password",
            "password": "testpass123"
        }
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        try:
            vps_response = requests.post(f"{self.api_url}/vps", json=vps_data, headers=headers, timeout=30)
            if vps_response.status_code != 200:
                print(f"❌ VPS creation failed: {vps_response.status_code}")
                return False
                
            vps_id = vps_response.json().get('id')
            print(f"✅ VPS created: {vps_id}")
            
        except Exception as e:
            print(f"❌ VPS creation error: {str(e)}")
            return False
        
        # Step 2: Create deployment
        timestamp = datetime.now().strftime('%H%M%S')
        deployment_data = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/facebook/react",
            "branch": "main",
            "project_name": f"token-test-{timestamp}",
            "port": 3050,
            "github_token": "ghp_initial_token_123456789"
        }
        
        try:
            dep_response = requests.post(f"{self.api_url}/deployments", json=deployment_data, headers=headers, timeout=30)
            if dep_response.status_code != 200:
                print(f"❌ Deployment creation failed: {dep_response.status_code}")
                # Try to clean up VPS
                requests.delete(f"{self.api_url}/vps/{vps_id}", headers=headers)
                return False
                
            deployment_id = dep_response.json().get('id')
            print(f"✅ Deployment created: {deployment_id}")
            
        except Exception as e:
            print(f"❌ Deployment creation error: {str(e)}")
            # Try to clean up VPS
            requests.delete(f"{self.api_url}/vps/{vps_id}", headers=headers)
            return False
        
        # Step 3: Test PUT /api/deployments/{id}/github-token
        print("\n🔄 Testing PUT /api/deployments/{id}/github-token...")
        
        token_data = {"github_token": "ghp_new_updated_token_987654321"}
        
        try:
            token_response = requests.put(
                f"{self.api_url}/deployments/{deployment_id}/github-token",
                json=token_data, 
                headers=headers,
                timeout=30
            )
            
            if token_response.status_code == 200:
                self.log_test("PUT github-token endpoint", True, "Token update successful")
                response_data = token_response.json()
                if 'message' in response_data:
                    self.log_test("PUT github-token response format", True, f"Message: {response_data['message']}")
                else:
                    self.log_test("PUT github-token response format", False, "No message in response")
            else:
                self.log_test("PUT github-token endpoint", False, f"Status: {token_response.status_code}")
                
        except Exception as e:
            self.log_test("PUT github-token endpoint", False, f"Exception: {str(e)}")
        
        # Step 4: Test POST /api/deployments/{id}/redeploy-with-token
        print("\n🚀 Testing POST /api/deployments/{id}/redeploy-with-token...")
        
        redeploy_token_data = {"github_token": "ghp_redeploy_token_abcdef123"}
        
        try:
            redeploy_response = requests.post(
                f"{self.api_url}/deployments/{deployment_id}/redeploy-with-token",
                json=redeploy_token_data,
                headers=headers,
                timeout=30
            )
            
            if redeploy_response.status_code == 200:
                self.log_test("POST redeploy-with-token endpoint", True, "Redeploy with token successful")
                response_data = redeploy_response.json()
                
                # Check response structure
                required_fields = ['id', 'status', 'vps_id', 'repo_url', 'project_name']
                missing_fields = [field for field in required_fields if field not in response_data]
                
                if not missing_fields:
                    self.log_test("POST redeploy-with-token response structure", True, "All required fields present")
                else:
                    self.log_test("POST redeploy-with-token response structure", False, f"Missing: {missing_fields}")
                
                # Check if status is pending (indicates redeploy started)
                if response_data.get('status') == 'pending':
                    self.log_test("POST redeploy-with-token status", True, "Status correctly set to pending")
                else:
                    self.log_test("POST redeploy-with-token status", False, f"Status: {response_data.get('status')}")
                    
                # Check error_type field presence and value
                if 'error_type' in response_data:
                    if response_data.get('error_type') is None:
                        self.log_test("DeploymentResponse error_type field", True, "error_type field present and cleared")
                    else:
                        self.log_test("DeploymentResponse error_type field", True, f"error_type field present: {response_data.get('error_type')}")
                else:
                    self.log_test("DeploymentResponse error_type field", False, "error_type field missing")
                    
            else:
                self.log_test("POST redeploy-with-token endpoint", False, f"Status: {redeploy_response.status_code}")
                
        except Exception as e:
            self.log_test("POST redeploy-with-token endpoint", False, f"Exception: {str(e)}")
        
        # Step 5: Test authentication protection (403 without token)
        print("\n🔒 Testing authentication protection...")
        
        no_auth_headers = {'Content-Type': 'application/json'}
        
        try:
            # Test PUT without auth
            unauth_put = requests.put(
                f"{self.api_url}/deployments/{deployment_id}/github-token",
                json=token_data,
                headers=no_auth_headers,
                timeout=30
            )
            
            if unauth_put.status_code == 403:
                self.log_test("PUT github-token auth protection", True, "Correctly blocked unauthenticated request")
            else:
                self.log_test("PUT github-token auth protection", False, f"Expected 403, got {unauth_put.status_code}")
                
            # Test POST without auth
            unauth_post = requests.post(
                f"{self.api_url}/deployments/{deployment_id}/redeploy-with-token",
                json=redeploy_token_data,
                headers=no_auth_headers,
                timeout=30
            )
            
            if unauth_post.status_code == 403:
                self.log_test("POST redeploy-with-token auth protection", True, "Correctly blocked unauthenticated request")
            else:
                self.log_test("POST redeploy-with-token auth protection", False, f"Expected 403, got {unauth_post.status_code}")
                
        except Exception as e:
            self.log_test("Authentication protection", False, f"Exception: {str(e)}")
        
        # Step 6: Test invalid deployment ID (404)
        print("\n🔍 Testing invalid deployment ID...")
        
        invalid_id = "invalid-deployment-id-12345"
        
        try:
            # Test PUT with invalid ID
            invalid_put = requests.put(
                f"{self.api_url}/deployments/{invalid_id}/github-token",
                json=token_data,
                headers=headers,
                timeout=30
            )
            
            if invalid_put.status_code == 404:
                self.log_test("PUT github-token invalid ID", True, "Correctly returned 404 for invalid deployment")
            else:
                self.log_test("PUT github-token invalid ID", False, f"Expected 404, got {invalid_put.status_code}")
                
            # Test POST with invalid ID
            invalid_post = requests.post(
                f"{self.api_url}/deployments/{invalid_id}/redeploy-with-token",
                json=redeploy_token_data,
                headers=headers,
                timeout=30
            )
            
            if invalid_post.status_code == 404:
                self.log_test("POST redeploy-with-token invalid ID", True, "Correctly returned 404 for invalid deployment")
            else:
                self.log_test("POST redeploy-with-token invalid ID", False, f"Expected 404, got {invalid_post.status_code}")
                
        except Exception as e:
            self.log_test("Invalid deployment ID handling", False, f"Exception: {str(e)}")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        try:
            requests.delete(f"{self.api_url}/deployments/{deployment_id}", headers=headers, timeout=30)
            print("✅ Deployment cleaned up")
        except:
            print("⚠️ Deployment cleanup timed out")
            
        try:
            requests.delete(f"{self.api_url}/vps/{vps_id}", headers=headers, timeout=30)
            print("✅ VPS cleaned up")
        except:
            print("⚠️ VPS cleanup timed out")
        
        return True

    def run_tests(self):
        """Run all GitHub token tests"""
        print(f"🚀 GitHub Token API Testing")
        print(f"🌐 Target: {self.base_url}")
        print("=" * 60)
        
        # Get admin authentication
        if not self.get_admin_token():
            print("❌ Could not authenticate - stopping tests")
            return False
        
        # Run tests
        self.test_github_token_functionality()
        
        # Generate report
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        return success_rate >= 80

def main():
    tester = FocusedGitHubTokenTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())