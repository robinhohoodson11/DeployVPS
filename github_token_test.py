import requests
import sys
import json
from datetime import datetime

class GitHubTokenTester:
    def __init__(self):
        self.base_url = "https://redeploy-fallback.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.user_id = None
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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {"status": "success"}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def setup_admin_user(self):
        """Create or login as admin user"""
        print("\n🔧 Setting up Admin User...")
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Try to register as first admin user
        admin_user_data = {
            "name": f"Admin Token Test {timestamp}",
            "email": f"tokenadmin{timestamp}@example.com",
            "password": "tokenadmin123"
        }
        
        response = self.run_test("Register Admin User", "POST", "auth/register", 200, admin_user_data)
        if response and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        
        # If registration didn't work, try login with a test user
        login_data = {
            "email": admin_user_data["email"],
            "password": admin_user_data["password"]
        }
        
        login_response = self.run_test("Login Test User", "POST", "auth/login", 200, login_data)
        if login_response and 'access_token' in login_response:
            self.token = login_response['access_token']
            self.user_id = login_response['user']['id']
            return True
            
        return False

    def setup_test_deployment(self):
        """Create VPS and deployment for testing"""
        print("\n🔧 Setting up Test VPS and Deployment...")
        
        # Create VPS
        vps_data = {
            "name": "GitHub Token Test VPS",
            "host": "192.168.1.100",
            "port": 22,
            "username": "testuser",
            "auth_type": "password",
            "password": "testpassword123"
        }
        
        vps_response = self.run_test("Create Test VPS", "POST", "vps", 200, vps_data)
        if not vps_response:
            return None, None
            
        vps_id = vps_response.get('id')
        
        # Create deployment
        timestamp = datetime.now().strftime('%H%M%S')
        deployment_data = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/facebook/react",
            "branch": "main",
            "project_name": f"github-token-test-{timestamp}",
            "port": 3020,
            "env_vars": {"NODE_ENV": "production"},
            "github_token": "old_expired_token_12345"
        }
        
        deployment_response = self.run_test("Create Test Deployment", "POST", "deployments", 200, deployment_data)
        if not deployment_response:
            return vps_id, None
            
        deployment_id = deployment_response.get('id')
        return vps_id, deployment_id

    def test_github_token_endpoints(self):
        """Test the new GitHub token related endpoints"""
        print("\n🔍 Testing GitHub Token Endpoints...")
        
        if not self.token:
            self.log_test("GitHub Token Tests", False, "No authentication token available")
            return False
            
        vps_id, deployment_id = self.setup_test_deployment()
        if not deployment_id:
            self.log_test("GitHub Token Tests Setup", False, "Could not create test deployment")
            return False
            
        print(f"\n  Using deployment ID: {deployment_id}")
        
        # Test 1: PUT /api/deployments/{deployment_id}/github-token - Update token
        print("\n  Testing PUT /api/deployments/{deployment_id}/github-token...")
        new_token_data = {
            "github_token": "ghp_new_valid_token_abcdef12345"
        }
        
        token_update_response = self.run_test(
            "Update GitHub Token", 
            "PUT", 
            f"deployments/{deployment_id}/github-token", 
            200, 
            new_token_data
        )
        
        # Verify response format
        if token_update_response:
            if 'message' in token_update_response:
                self.log_test("Token Update Response Format", True, "Response contains message field")
            else:
                self.log_test("Token Update Response Format", False, "Response missing message field")
        
        # Test 2: POST /api/deployments/{deployment_id}/redeploy-with-token - Update token and redeploy
        print("\n  Testing POST /api/deployments/{deployment_id}/redeploy-with-token...")
        redeploy_token_data = {
            "github_token": "ghp_redeploy_token_xyz789"
        }
        
        redeploy_response = self.run_test(
            "Redeploy with New Token",
            "POST", 
            f"deployments/{deployment_id}/redeploy-with-token",
            200,
            redeploy_token_data
        )
        
        # Verify response structure for redeploy-with-token
        if redeploy_response:
            expected_fields = ['id', 'status', 'vps_id', 'repo_url', 'project_name', 'port', 'created_at', 'updated_at']
            present_fields = [field for field in expected_fields if field in redeploy_response]
            missing_fields = [field for field in expected_fields if field not in redeploy_response]
            
            if len(present_fields) >= 6:
                self.log_test("Redeploy-with-Token Response Structure", True, f"Contains {len(present_fields)}/{len(expected_fields)} expected fields")
            else:
                self.log_test("Redeploy-with-Token Response Structure", False, f"Missing critical fields: {missing_fields}")
            
            # Check if status is set to pending (indicating redeploy started)
            if redeploy_response.get('status') == 'pending':
                self.log_test("Redeploy-with-Token Status", True, "Status correctly set to pending")
            else:
                self.log_test("Redeploy-with-Token Status", False, f"Expected 'pending', got '{redeploy_response.get('status')}'")
                
            # Verify error_type is cleared
            error_type = redeploy_response.get('error_type')
            if error_type is None:
                self.log_test("Error Type Cleared", True, "error_type is cleared after token update")
            else:
                self.log_test("Error Type Cleared", False, f"error_type should be None, got: {error_type}")

        # Test 3: Verify DeploymentResponse model includes optional error_type field
        print("\n  Testing DeploymentResponse Model - error_type field...")
        
        # Get deployment details to check model structure
        deployment_details = self.run_test(
            "Get Deployment Details", 
            "GET", 
            f"deployments/{deployment_id}",
            200
        )
        
        if deployment_details:
            # error_type field should be present (can be None or a string)
            if 'error_type' in deployment_details:
                self.log_test("DeploymentResponse error_type Field", True, f"error_type field present: {deployment_details.get('error_type')}")
            else:
                self.log_test("DeploymentResponse error_type Field", False, "error_type field missing from DeploymentResponse model")

        # Test 4: Authentication protection - Test endpoints without token
        print("\n  Testing Authentication Protection...")
        original_token = self.token
        self.token = None
        
        # Test without authentication - should return 403/401
        self.run_test(
            "Update Token Without Auth",
            "PUT",
            f"deployments/{deployment_id}/github-token",
            403,  # Expect 403 Forbidden
            new_token_data
        )
        
        self.run_test(
            "Redeploy With Token Without Auth",
            "POST",
            f"deployments/{deployment_id}/redeploy-with-token", 
            403,  # Expect 403 Forbidden
            redeploy_token_data
        )
        
        # Restore token
        self.token = original_token
        
        # Test 5: Invalid deployment ID - should return 404
        print("\n  Testing Invalid Deployment ID...")
        invalid_deployment_id = "invalid-deployment-id-12345"
        
        self.run_test(
            "Update Token Invalid ID",
            "PUT",
            f"deployments/{invalid_deployment_id}/github-token",
            404,  # Expect 404 Not Found
            new_token_data
        )
        
        self.run_test(
            "Redeploy With Token Invalid ID", 
            "POST",
            f"deployments/{invalid_deployment_id}/redeploy-with-token",
            404,  # Expect 404 Not Found
            redeploy_token_data
        )

        # Test 6: Test with empty/invalid token data
        print("\n  Testing Invalid Token Data...")
        
        # Test with missing github_token field
        invalid_data = {}
        invalid_response = requests.put(
            f"{self.api_url}/deployments/{deployment_id}/github-token",
            json=invalid_data,
            headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
            timeout=30
        )
        
        # This might return 422 (validation error) or 400 (bad request)
        if invalid_response.status_code in [400, 422]:
            self.log_test("Invalid Token Data Validation", True, f"Correctly rejected invalid data with status {invalid_response.status_code}")
        else:
            self.log_test("Invalid Token Data Validation", False, f"Expected 400 or 422, got {invalid_response.status_code}")

        # Cleanup
        print("\n  Cleaning up test data...")
        if deployment_id:
            self.run_test("Cleanup Test Deployment", "DELETE", f"deployments/{deployment_id}", 200)
        if vps_id:
            self.run_test("Cleanup Test VPS", "DELETE", f"vps/{vps_id}", 200)
        
        return True

    def run_github_token_tests(self):
        """Run all GitHub token related tests"""
        print(f"🚀 Starting GitHub Token API Tests for {self.base_url}")
        print("=" * 70)
        
        # Setup admin user
        if not self.setup_admin_user():
            print("❌ Could not setup admin user, stopping tests")
            return self.generate_report()
        
        # Run GitHub token tests
        self.test_github_token_endpoints()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 70)
        print(f"📊 GitHub Token Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "results": self.test_results
        }

def main():
    tester = GitHubTokenTester()
    report = tester.run_github_token_tests()
    
    # Return appropriate exit code
    return 0 if report["success_rate"] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())