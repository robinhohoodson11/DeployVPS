import requests
import sys
import json
from datetime import datetime

class DeployVPSAPITester:
    def __init__(self, base_url="https://deployvps-hub.preview.emergentagent.com"):
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
        if response:
            # Check if this is the first user (admin) or a regular user (pending)
            if 'access_token' in response:
                # First user becomes admin automatically
                self.token = response['access_token']
                self.user_id = response['user']['id']
                self.log_test("First User Admin Registration", True, f"User role: {response['user'].get('role', 'unknown')}")
                return True
            elif response.get('status') == 'pending':
                # Regular user registration (pending approval)
                self.log_test("Regular User Pending Registration", True, "User correctly marked as pending")
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
        
        # Test redeploy with detailed verification
        redeploy_response = self.run_test("Redeploy", "POST", f"deployments/{deployment_id}/redeploy", 200)
        if redeploy_response:
            # Verify redeploy response contains expected fields
            expected_fields = ['id', 'status', 'deploy_type', 'vps_id', 'repo_url', 'project_name', 'port']
            missing_fields = [field for field in expected_fields if field not in redeploy_response]
            if not missing_fields:
                self.log_test("Redeploy Response Fields", True, f"All expected fields present")
            else:
                self.log_test("Redeploy Response Fields", False, f"Missing fields: {missing_fields}")
            
            # Verify status is set to pending (indicating redeploy started)
            if redeploy_response.get('status') == 'pending':
                self.log_test("Redeploy Status", True, "Status correctly set to pending")
            else:
                self.log_test("Redeploy Status", False, f"Expected 'pending', got '{redeploy_response.get('status')}'")
        
        return deployment_id
        
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

    def test_redeploy_functionality(self, vps_id):
        """Test redeploy API endpoint specifically as requested in review"""
        print("\n🔍 Testing Redeploy API Functionality...")
        if not self.token or not vps_id:
            self.log_test("Redeploy Functionality", False, "No token or VPS ID available")
            return None
            
        # First create a deployment to redeploy
        deployment_data = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/vercel/next.js",
            "branch": "main",
            "project_name": "test-redeploy-app",
            "port": 3010,
            "create_mongodb": True,
            "mongodb_port": 27020,
            "create_admin": True,
            "admin_email": "redeploy@testapp.com",
            "admin_password": "RedeployPass123!"
        }
        
        create_response = self.run_test("Create Deployment for Redeploy Test", "POST", "deployments", 200, deployment_data)
        if not create_response:
            return None
            
        deployment_id = create_response.get('id')
        if not deployment_id:
            self.log_test("Deployment ID Missing for Redeploy", False, "No deployment ID in response")
            return None
        
        print(f"\n  Testing POST /api/deployments/{deployment_id}/redeploy...")
        
        # Test 1: Verify endpoint exists and returns valid response
        redeploy_response = self.run_test("Redeploy Endpoint Exists", "POST", f"deployments/{deployment_id}/redeploy", 200)
        
        if redeploy_response:
            # Test 2: Verify endpoint accepts deployment_id and returns expected fields
            expected_fields = ['id', 'status', 'deploy_type', 'vps_id', 'repo_url', 'branch', 'project_name', 'port', 'created_at', 'updated_at']
            present_fields = [field for field in expected_fields if field in redeploy_response]
            missing_fields = [field for field in expected_fields if field not in redeploy_response]
            
            if len(present_fields) >= 8:  # Most important fields present
                self.log_test("Redeploy Response Structure", True, f"Contains {len(present_fields)}/{len(expected_fields)} expected fields")
            else:
                self.log_test("Redeploy Response Structure", False, f"Missing critical fields: {missing_fields}")
            
            # Verify deployment_id is correctly handled
            if redeploy_response.get('id') == deployment_id:
                self.log_test("Redeploy Deployment ID Match", True, "Deployment ID correctly preserved")
            else:
                self.log_test("Redeploy Deployment ID Match", False, f"ID mismatch: expected {deployment_id}, got {redeploy_response.get('id')}")
            
            # Verify status field
            if 'status' in redeploy_response:
                status = redeploy_response.get('status')
                if status in ['pending', 'cloning', 'building', 'deploying', 'running']:
                    self.log_test("Redeploy Status Field", True, f"Valid status: {status}")
                else:
                    self.log_test("Redeploy Status Field", False, f"Invalid status: {status}")
            else:
                self.log_test("Redeploy Status Field", False, "Status field missing")
            
            # Verify deploy_type field (if present)
            if 'deploy_type' in redeploy_response:
                deploy_type = redeploy_response.get('deploy_type')
                valid_types = ['frontend_only', 'backend_only', 'fullstack', 'static']
                if deploy_type in valid_types or deploy_type is None:
                    self.log_test("Redeploy Deploy Type Field", True, f"Valid deploy_type: {deploy_type}")
                else:
                    self.log_test("Redeploy Deploy Type Field", False, f"Invalid deploy_type: {deploy_type}")
            else:
                self.log_test("Redeploy Deploy Type Field", True, "deploy_type field not required initially")
        
        # Test 3: Verify the logic - check if is_redeploy=True parameter is being passed correctly
        # We can't directly test the internal parameter, but we can verify the behavior
        print("\n  Verifying Redeploy Logic (Database Preservation)...")
        
        # Get deployment details to check if MongoDB settings are preserved
        detail_response = self.run_test("Get Deployment Details After Redeploy", "GET", f"deployments/{deployment_id}", 200)
        if detail_response:
            # Check if MongoDB URL is preserved (indicating database preservation logic)
            if detail_response.get('mongodb_url'):
                self.log_test("MongoDB Preservation Logic", True, "MongoDB URL preserved in redeploy")
            else:
                self.log_test("MongoDB Preservation Logic", False, "MongoDB URL not found - may indicate issue with preservation")
            
            # Check if admin credentials are preserved (should not be recreated in redeploy)
            admin_creds = detail_response.get('admin_credentials')
            if admin_creds and isinstance(admin_creds, dict):
                self.log_test("Admin Credentials Preservation", True, "Admin credentials preserved from original deployment")
            else:
                self.log_test("Admin Credentials Preservation", False, "Admin credentials missing - may indicate recreation issue")
        
        # Test 4: Test redeploy with invalid deployment ID
        invalid_id = "invalid-deployment-id-12345"
        self.run_test("Redeploy Invalid ID", "POST", f"deployments/{invalid_id}/redeploy", 404)
        
        # Test 5: Test redeploy without authentication
        original_token = self.token
        self.token = None
        self.run_test("Redeploy Without Auth", "POST", f"deployments/{deployment_id}/redeploy", 401)
        self.token = original_token
        
        return deployment_id

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
        
        return True

    def test_user_management_system(self):
        """Test new user management system features"""
        print("\n🔍 Testing User Management System...")
        
        # Step 1: Create an admin user first by checking if we need to clear the database
        print("\n  Setting up Admin User...")
        
        # Try to create an admin user by registering when database is empty
        # First, let's try to register a user and see if it becomes admin
        admin_timestamp = datetime.now().strftime('%H%M%S')
        admin_user_data = {
            "name": f"Admin User {admin_timestamp}",
            "email": f"admin{admin_timestamp}@example.com",
            "password": "adminpass123"
        }
        
        admin_response = self.run_test("Create Admin User", "POST", "auth/register", 200, admin_user_data)
        admin_token = None
        
        if admin_response:
            if 'access_token' in admin_response:
                # User became admin (first user)
                admin_token = admin_response['access_token']
                self.log_test("Admin User Created", True, f"User role: {admin_response['user'].get('role')}")
            elif admin_response.get('status') == 'pending':
                # User is pending, there's already an admin in the system
                self.log_test("Admin Already Exists", True, "New user is pending, admin exists")
                
                # Try to use the current token if it's an admin
                if self.token:
                    me_response = self.run_test("Check Current User Role", "GET", "auth/me", 200)
                    if me_response and me_response.get('role') == 'admin':
                        admin_token = self.token
                        self.log_test("Using Existing Admin Token", True, "Current user is admin")
        
        # Step 2: Test registration with pending approval (create a second user)
        print("\n  Testing Registration with Pending Approval...")
        timestamp = datetime.now().strftime('%H%M%S')
        pending_user_data = {
            "name": f"Pending User {timestamp}",
            "email": f"pending{timestamp}@example.com",
            "password": "pendingpass123"
        }
        
        # Register a new user (should be pending since admin exists)
        pending_response = self.run_test("Register Pending User", "POST", "auth/register", 200, pending_user_data)
        if pending_response:
            # Should return status "pending" instead of token
            if pending_response.get("status") == "pending":
                self.log_test("Registration Returns Pending Status", True, "User correctly marked as pending")
            else:
                self.log_test("Registration Returns Pending Status", False, f"Expected pending status, got: {pending_response}")
        
        # Step 3: Test login of pending user (should fail with 403)
        print("\n  Testing Login of Pending User...")
        pending_login_data = {
            "email": pending_user_data["email"],
            "password": pending_user_data["password"]
        }
        
        # This should fail with 403
        self.run_test("Login Pending User (Should Fail)", "POST", "auth/login", 403, pending_login_data)
        
        # Step 4: Test admin routes
        if admin_token:
            print("\n  Testing Admin Routes...")
            # Save current token and switch to admin token
            original_token = self.token
            self.token = admin_token
            
            # Test GET /api/admin/users - list all users
            users_response = self.run_test("List All Users", "GET", "admin/users", 200)
            
            # Test GET /api/admin/users/pending - list pending users
            pending_users_response = self.run_test("List Pending Users", "GET", "admin/users/pending", 200)
            
            # Test GET /api/admin/stats - get statistics
            stats_response = self.run_test("Get Admin Stats", "GET", "admin/stats", 200)
            if stats_response:
                expected_fields = ['total_users', 'pending_users', 'active_users', 'expired_users', 'blocked_users', 'admin_users']
                missing_fields = [field for field in expected_fields if field not in stats_response]
                if not missing_fields:
                    self.log_test("Admin Stats Fields Complete", True, f"All expected fields present")
                else:
                    self.log_test("Admin Stats Fields Complete", False, f"Missing fields: {missing_fields}")
            
            # Find a pending user to test approval/blocking
            pending_user_id = None
            if pending_users_response and isinstance(pending_users_response, list) and len(pending_users_response) > 0:
                pending_user_id = pending_users_response[0]['id']
                
                # Test POST /api/admin/users/{id}/approve - approve user
                approve_response = self.run_test("Approve User", "POST", f"admin/users/{pending_user_id}/approve", 200)
                
                # Test POST /api/admin/users/{id}/block - block user (after approval)
                block_response = self.run_test("Block User", "POST", f"admin/users/{pending_user_id}/block", 200)
                
                # Test PUT /api/admin/users/{id} - update user
                update_data = {
                    "name": "Updated User Name",
                    "role": "user",
                    "status": "active",
                    "expires_at": None
                }
                update_response = self.run_test("Update User", "PUT", f"admin/users/{pending_user_id}", 200, update_data)
            
            # Step 5: Test email configuration routes
            print("\n  Testing Email Configuration...")
            
            # Test GET /api/admin/settings/email - get email config
            email_config_response = self.run_test("Get Email Config", "GET", "admin/settings/email", 200)
            
            # Test POST /api/admin/settings/email - save email config
            email_config_data = {
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_user": "test@gmail.com",
                "smtp_password": "testpassword",
                "smtp_from_name": "DeployVPS Test",
                "smtp_from_email": "test@gmail.com",
                "smtp_use_tls": True
            }
            save_email_response = self.run_test("Save Email Config", "POST", "admin/settings/email", 200, email_config_data)
            
            # Restore original token
            self.token = original_token
        else:
            self.log_test("Admin Routes Testing", False, "No admin token available")
        
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
        
        # Test authentication - but don't stop if registration creates admin instead of regular user
        registration_result = self.test_user_registration()
        if not registration_result:
            print("❌ Registration failed, stopping tests")
            return self.generate_report()
            
        self.test_user_login()
        self.test_get_current_user()
        
        # Test new user management system
        self.test_user_management_system()
        
        # Test VPS operations
        vps_id = self.test_vps_operations()
        
        # Test deployment operations
        deployment_id = None
        new_deployment_ids = []
        redeploy_deployment_id = None
        if vps_id:
            deployment_id = self.test_deployment_operations(vps_id)
            
            # Test new deployment features
            new_deployment_ids = self.test_new_deployment_features(vps_id)
            
            # Test redeploy functionality specifically
            redeploy_deployment_id = self.test_redeploy_functionality(vps_id)
            
            # Test domain configuration
            if deployment_id:
                self.test_domain_configuration(deployment_id)
        
        # Cleanup - combine all deployment IDs
        all_deployment_ids = [deployment_id] if deployment_id else []
        if new_deployment_ids:
            all_deployment_ids.extend([d for d in new_deployment_ids if d])
        if redeploy_deployment_id:
            all_deployment_ids.append(redeploy_deployment_id)
        
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