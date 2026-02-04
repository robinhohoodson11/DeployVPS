import requests
import sys
import json
from datetime import datetime

class DeployVPSAPIValidationTester:
    def __init__(self, base_url="https://vps-automation.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
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
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)

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

    def test_authentication(self):
        """Test authentication to get token"""
        print("\n🔍 Testing Authentication...")
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"API Test User {timestamp}",
            "email": f"apitest{timestamp}@example.com",
            "password": "testpass123"
        }
        
        response = self.run_test("User Registration", "POST", "auth/register", 200, user_data)
        if response and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_deployment_model_validation(self):
        """Test DeploymentCreate model accepts new fields"""
        print("\n🔍 Testing Deployment Model Validation...")
        if not self.token:
            self.log_test("Deployment Model Validation", False, "No token available")
            return False

        # First create a VPS for testing
        vps_data = {
            "name": "Test VPS for Validation",
            "host": "192.168.1.100",
            "port": 22,
            "username": "testuser",
            "auth_type": "password",
            "password": "testpassword123"
        }
        
        vps_response = self.run_test("Create VPS for Testing", "POST", "vps", 200, vps_data)
        if not vps_response:
            return False
            
        vps_id = vps_response.get('id')
        if not vps_id:
            self.log_test("VPS ID Missing", False, "No VPS ID in response")
            return False

        # Test 1: Deployment with all new fields
        deployment_with_admin = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/facebook/react",
            "branch": "main",
            "project_name": "test-validation-app",
            "port": 3001,
            "create_mongodb": True,
            "mongodb_port": 27018,
            "create_admin": True,
            "admin_email": "admin@validation.com",
            "admin_password": "AdminPass123!"
        }
        
        response = self.run_test("Deployment with Admin Fields", "POST", "deployments", 200, deployment_with_admin)
        deployment_id = None
        if response:
            deployment_id = response.get('id')
            
            # Check if response contains expected fields
            expected_fields = ['deploy_type', 'backend_port', 'admin_credentials']
            for field in expected_fields:
                if field in response:
                    self.log_test(f"Response contains {field}", True, f"{field}: {response.get(field)}")
                else:
                    self.log_test(f"Response contains {field}", False, f"{field} field missing")

        # Test 2: Deployment without admin fields (should still work)
        deployment_without_admin = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/vercel/next.js",
            "branch": "main",
            "project_name": "test-no-admin-app",
            "port": 3002,
            "create_mongodb": False,
            "create_admin": False
        }
        
        response2 = self.run_test("Deployment without Admin Fields", "POST", "deployments", 200, deployment_without_admin)
        deployment_id2 = None
        if response2:
            deployment_id2 = response2.get('id')

        # Test 3: Invalid admin email should fail validation
        deployment_invalid_email = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/facebook/react",
            "branch": "main",
            "project_name": "test-invalid-email",
            "port": 3003,
            "create_admin": True,
            "admin_email": "invalid-email",  # Invalid email format
            "admin_password": "AdminPass123!"
        }
        
        # This should fail with 422 (validation error)
        self.run_test("Invalid Admin Email Validation", "POST", "deployments", 422, deployment_invalid_email)

        return deployment_id, deployment_id2, vps_id

    def test_deployment_response_structure(self, deployment_id):
        """Test that deployment response includes required fields"""
        print("\n🔍 Testing Deployment Response Structure...")
        if not self.token or not deployment_id:
            self.log_test("Deployment Response Structure", False, "No token or deployment ID")
            return False

        response = self.run_test("Get Deployment Details", "GET", f"deployments/{deployment_id}", 200)
        if response:
            # Check for required fields in response
            required_fields = {
                'id': str,
                'vps_id': str,
                'repo_url': str,
                'project_name': str,
                'port': int,
                'status': str,
                'deploy_type': (str, type(None)),
                'backend_port': (int, type(None)),
                'admin_credentials': (dict, type(None)),
                'created_at': str,
                'updated_at': str
            }
            
            for field, expected_type in required_fields.items():
                if field in response:
                    actual_value = response[field]
                    if isinstance(actual_value, expected_type):
                        self.log_test(f"Field {field} type check", True, f"{field}: {type(actual_value).__name__}")
                    else:
                        self.log_test(f"Field {field} type check", False, f"Expected {expected_type}, got {type(actual_value)}")
                else:
                    self.log_test(f"Field {field} present", False, f"{field} missing from response")

            # Check admin_credentials structure if present
            if response.get('admin_credentials'):
                admin_creds = response['admin_credentials']
                if isinstance(admin_creds, dict):
                    if 'email' in admin_creds and 'password' in admin_creds:
                        self.log_test("Admin Credentials Structure", True, "Contains email and password")
                    else:
                        self.log_test("Admin Credentials Structure", False, "Missing email or password fields")
                else:
                    self.log_test("Admin Credentials Structure", False, "Not a dictionary")

        return True

    def test_deployment_list_structure(self):
        """Test that deployment list returns proper structure"""
        print("\n🔍 Testing Deployment List Structure...")
        if not self.token:
            self.log_test("Deployment List Structure", False, "No token available")
            return False

        response = self.run_test("List Deployments", "GET", "deployments", 200)
        if response:
            if isinstance(response, list):
                self.log_test("Deployments List Type", True, f"Returned {len(response)} deployments")
                
                if len(response) > 0:
                    # Check first deployment structure
                    first_deployment = response[0]
                    required_fields = ['id', 'vps_id', 'repo_url', 'project_name', 'port', 'status']
                    
                    for field in required_fields:
                        if field in first_deployment:
                            self.log_test(f"List item has {field}", True)
                        else:
                            self.log_test(f"List item has {field}", False, f"{field} missing")
                else:
                    self.log_test("Deployments List Content", True, "Empty list (no deployments)")
            else:
                self.log_test("Deployments List Type", False, f"Expected list, got {type(response)}")

        return True

    def cleanup_test_data(self, deployment_ids, vps_id):
        """Clean up test data"""
        print("\n🔍 Cleaning Up Test Data...")
        if deployment_ids:
            for dep_id in deployment_ids:
                if dep_id:
                    self.run_test(f"Delete Deployment {dep_id[:8]}", "DELETE", f"deployments/{dep_id}", 200)
        
        if vps_id:
            self.run_test("Delete Test VPS", "DELETE", f"vps/{vps_id}", 200)

    def run_validation_tests(self):
        """Run focused validation tests"""
        print(f"🚀 Starting API Validation Tests for {self.base_url}")
        print("=" * 60)
        
        # Test authentication
        if not self.test_authentication():
            print("❌ Authentication failed, stopping tests")
            return self.generate_report()
        
        # Test deployment model validation
        deployment_id, deployment_id2, vps_id = self.test_deployment_model_validation()
        
        # Test deployment response structure
        if deployment_id:
            self.test_deployment_response_structure(deployment_id)
        
        # Test deployment list structure
        self.test_deployment_list_structure()
        
        # Cleanup
        deployment_ids = [deployment_id, deployment_id2]
        self.cleanup_test_data(deployment_ids, vps_id)
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
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
    tester = DeployVPSAPIValidationTester()
    report = tester.run_validation_tests()
    
    # Return appropriate exit code
    return 0 if report["success_rate"] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())