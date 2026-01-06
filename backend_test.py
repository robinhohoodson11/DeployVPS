import requests
import sys
import json
from datetime import datetime

class DeployVPSAPITester:
    def __init__(self, base_url="https://auth-control-6.preview.emergentagent.com"):
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

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        self.run_test("Health Check", "GET", "", 200)
        self.run_test("API Root", "GET", "health", 200)

    def test_user_registration(self):
        """Test user registration"""
        print("\n🔍 Testing User Registration...")
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "testpass123"
        }
        
        response = self.run_test("User Registration", "POST", "auth/register", 200, user_data)
        if response and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_user_login(self):
        """Test user login with existing user"""
        print("\n🔍 Testing User Login...")
        # First register a user
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"Login Test User {timestamp}",
            "email": f"logintest{timestamp}@example.com", 
            "password": "testpass123"
        }
        
        # Register
        reg_response = self.run_test("Register for Login Test", "POST", "auth/register", 200, user_data)
        if not reg_response:
            return False
            
        # Now test login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        if response and 'access_token' in response:
            # Keep the original token for other tests
            return True
        return False

    def test_get_current_user(self):
        """Test get current user endpoint"""
        print("\n🔍 Testing Get Current User...")
        if not self.token:
            self.log_test("Get Current User", False, "No token available")
            return False
            
        response = self.run_test("Get Current User", "GET", "auth/me", 200)
        return response is not None

    def test_vps_operations(self):
        """Test VPS CRUD operations"""
        print("\n🔍 Testing VPS Operations...")
        if not self.token:
            self.log_test("VPS Operations", False, "No token available")
            return None
            
        # Test create VPS
        vps_data = {
            "name": "Test VPS Server",
            "host": "192.168.1.100",
            "port": 22,
            "username": "testuser",
            "auth_type": "password",
            "password": "testpassword123"
        }
        
        create_response = self.run_test("Create VPS", "POST", "vps", 200, vps_data)
        if not create_response:
            return None
            
        vps_id = create_response.get('id')
        if not vps_id:
            self.log_test("VPS ID Missing", False, "No VPS ID in response")
            return None
            
        # Test list VPS
        self.run_test("List VPS", "GET", "vps", 200)
        
        # Test get specific VPS
        self.run_test("Get VPS", "GET", f"vps/{vps_id}", 200)
        
        # Test VPS connection (this will likely fail without real VPS)
        self.run_test("Test VPS Connection", "POST", f"vps/{vps_id}/test", 200)
        
        return vps_id

    def test_deployment_operations(self, vps_id):
        """Test Deployment CRUD operations"""
        print("\n🔍 Testing Deployment Operations...")
        if not self.token or not vps_id:
            self.log_test("Deployment Operations", False, "No token or VPS ID available")
            return None
            
        # Test create deployment
        deployment_data = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/vercel/next.js",
            "branch": "main",
            "project_name": "test-nextjs-app",
            "port": 3000,
            "env_vars": {"NODE_ENV": "production"},
            "github_token": None
        }
        
        create_response = self.run_test("Create Deployment", "POST", "deployments", 200, deployment_data)
        if not create_response:
            return None
            
        deployment_id = create_response.get('id')
        if not deployment_id:
            self.log_test("Deployment ID Missing", False, "No deployment ID in response")
            return None
            
        # Test list deployments
        self.run_test("List Deployments", "GET", "deployments", 200)
        
        # Test get specific deployment
        self.run_test("Get Deployment", "GET", f"deployments/{deployment_id}", 200)
        
        # Test deployment logs
        self.run_test("Get Deployment Logs", "GET", f"deployments/{deployment_id}/logs", 200)
        
        # Test redeploy
        self.run_test("Redeploy", "POST", f"deployments/{deployment_id}/redeploy", 200)
        
        # Test stop deployment
        self.run_test("Stop Deployment", "POST", f"deployments/{deployment_id}/stop", 200)
        
        return deployment_id

    def test_new_deployment_features(self, vps_id):
        """Test new deployment features: admin creation, fullstack detection, dynamic ports"""
        print("\n🔍 Testing New Deployment Features...")
        if not self.token or not vps_id:
            self.log_test("New Deployment Features", False, "No token or VPS ID available")
            return None

        # Test 1: Deployment with admin creation enabled
        print("\n  Testing Admin User Creation...")
        admin_deployment_data = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/facebook/react",
            "branch": "main", 
            "project_name": "test-admin-app",
            "port": 3001,
            "create_mongodb": True,
            "mongodb_port": 27018,
            "create_admin": True,
            "admin_email": "admin@testapp.com",
            "admin_password": "AdminPass123!"
        }
        
        admin_response = self.run_test("Create Deployment with Admin", "POST", "deployments", 200, admin_deployment_data)
        admin_deployment_id = None
        if admin_response:
            admin_deployment_id = admin_response.get('id')
            
            # Verify the response contains expected fields
            if 'deploy_type' in admin_response:
                self.log_test("Deploy Type Field Present", True, f"deploy_type: {admin_response.get('deploy_type')}")
            else:
                self.log_test("Deploy Type Field Present", False, "deploy_type field missing from response")
                
            # Check for backend_port field (should be present for fullstack)
            if 'backend_port' in admin_response:
                self.log_test("Backend Port Field Present", True, f"backend_port: {admin_response.get('backend_port')}")
            else:
                self.log_test("Backend Port Field Present", False, "backend_port field missing from response")

        # Test 2: Fullstack project detection
        print("\n  Testing Fullstack Detection...")
        fullstack_deployment_data = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/vercel/next.js",
            "branch": "main",
            "project_name": "test-fullstack-app", 
            "port": 3002,
            "create_mongodb": False,
            "create_admin": False
        }
        
        fullstack_response = self.run_test("Create Fullstack Deployment", "POST", "deployments", 200, fullstack_deployment_data)
        fullstack_deployment_id = None
        if fullstack_response:
            fullstack_deployment_id = fullstack_response.get('id')

        # Test 3: Dynamic port assignment for backend
        print("\n  Testing Dynamic Port Assignment...")
        dynamic_port_data = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/tiangolo/fastapi",
            "branch": "master",
            "project_name": "test-backend-app",
            "port": 3003,
            "create_mongodb": True,
            "mongodb_port": 27019,
            "create_admin": True,
            "admin_email": "backend@testapp.com", 
            "admin_password": "BackendPass123!"
        }
        
        dynamic_response = self.run_test("Create Backend with Dynamic Port", "POST", "deployments", 200, dynamic_port_data)
        dynamic_deployment_id = None
        if dynamic_response:
            dynamic_deployment_id = dynamic_response.get('id')
            
            # Verify backend port is port + 1000
            expected_backend_port = 3003 + 1000
            actual_backend_port = dynamic_response.get('backend_port')
            if actual_backend_port == expected_backend_port:
                self.log_test("Dynamic Port Calculation", True, f"Backend port correctly set to {actual_backend_port}")
            else:
                self.log_test("Dynamic Port Calculation", False, f"Expected {expected_backend_port}, got {actual_backend_port}")

        # Test 4: Verify deployment details include admin credentials
        if admin_deployment_id:
            print("\n  Testing Admin Credentials in Response...")
            detail_response = self.run_test("Get Deployment with Admin Details", "GET", f"deployments/{admin_deployment_id}", 200)
            if detail_response:
                admin_creds = detail_response.get('admin_credentials')
                if admin_creds and isinstance(admin_creds, dict):
                    if 'email' in admin_creds and 'password' in admin_creds:
                        self.log_test("Admin Credentials Present", True, f"Admin email: {admin_creds.get('email')}")
                    else:
                        self.log_test("Admin Credentials Present", False, "Admin credentials missing email/password fields")
                else:
                    self.log_test("Admin Credentials Present", False, "admin_credentials field missing or invalid")

        # Return deployment IDs for cleanup
        return [admin_deployment_id, fullstack_deployment_id, dynamic_deployment_id]

    def test_domain_configuration(self, deployment_id):
        """Test domain configuration"""
        print("\n🔍 Testing Domain Configuration...")
        if not self.token or not deployment_id:
            self.log_test("Domain Configuration", False, "No token or deployment ID available")
            return False
            
        # Test configure domain
        domain_data = {"domain": "test.example.com"}
        self.run_test("Configure Domain", "POST", f"deployments/{deployment_id}/domain", 200, domain_data)
        
        # Test remove domain
        self.run_test("Remove Domain", "DELETE", f"deployments/{deployment_id}/domain", 200)
        
        return True

    def test_cleanup(self, vps_id, deployment_ids):
        """Clean up test data"""
        print("\n🔍 Cleaning Up Test Data...")
        if deployment_ids:
            if isinstance(deployment_ids, list):
                for deployment_id in deployment_ids:
                    if deployment_id:
                        self.run_test(f"Delete Deployment {deployment_id[:8]}", "DELETE", f"deployments/{deployment_id}", 200)
            else:
                self.run_test("Delete Deployment", "DELETE", f"deployments/{deployment_ids}", 200)
        if vps_id:
            self.run_test("Delete VPS", "DELETE", f"vps/{vps_id}", 200)

    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting API Tests for {self.base_url}")
        print("=" * 60)
        
        # Test health endpoints
        self.test_health_check()
        
        # Test authentication
        if not self.test_user_registration():
            print("❌ Registration failed, stopping tests")
            return self.generate_report()
            
        self.test_user_login()
        self.test_get_current_user()
        
        # Test VPS operations
        vps_id = self.test_vps_operations()
        
        # Test deployment operations
        deployment_id = None
        new_deployment_ids = []
        if vps_id:
            deployment_id = self.test_deployment_operations(vps_id)
            
            # Test new deployment features
            new_deployment_ids = self.test_new_deployment_features(vps_id)
            
            # Test domain configuration
            if deployment_id:
                self.test_domain_configuration(deployment_id)
        
        # Cleanup - combine all deployment IDs
        all_deployment_ids = [deployment_id] if deployment_id else []
        if new_deployment_ids:
            all_deployment_ids.extend([d for d in new_deployment_ids if d])
        
        self.test_cleanup(vps_id, all_deployment_ids)
        
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
    tester = DeployVPSAPITester()
    report = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if report["success_rate"] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())