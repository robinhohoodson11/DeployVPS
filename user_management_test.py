import requests
import sys
import json
from datetime import datetime

class UserManagementTester:
    def __init__(self, base_url="https://redeploy-fallback.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
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
        
        if self.admin_token:
            test_headers['Authorization'] = f'Bearer {self.admin_token}'
        
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
        """Create or find an admin user"""
        print("\n🔍 Setting up Admin User...")
        
        # Try to create an admin user
        timestamp = datetime.now().strftime('%H%M%S')
        admin_data = {
            "name": f"Admin Test {timestamp}",
            "email": f"admin{timestamp}@test.com",
            "password": "AdminPass123!"
        }
        
        response = self.run_test("Create Admin User", "POST", "auth/register", 200, admin_data)
        
        if response:
            if 'access_token' in response:
                # User became admin (first user)
                self.admin_token = response['access_token']
                self.log_test("Admin User Setup", True, f"Role: {response['user'].get('role')}")
                return True
            elif response.get('status') == 'pending':
                # User is pending, admin already exists
                self.log_test("Admin Already Exists", True, "System has existing admin")
                
                # Try to login with a known admin (this is a limitation - we'd need to know admin credentials)
                # For now, we'll create a test that doesn't require admin token
                return False
        
        return False

    def test_user_registration_pending(self):
        """Test that new user registration creates pending users"""
        print("\n🔍 Testing User Registration (Pending)...")
        
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"Pending User {timestamp}",
            "email": f"pending{timestamp}@test.com",
            "password": "UserPass123!"
        }
        
        response = self.run_test("Register Pending User", "POST", "auth/register", 200, user_data)
        
        if response:
            if response.get('status') == 'pending':
                self.log_test("User Registration Pending", True, "User correctly marked as pending")
                return user_data
            elif 'access_token' in response:
                self.log_test("User Registration Pending", False, "User became admin instead of pending")
                # If this user became admin, save the token for admin tests
                self.admin_token = response['access_token']
                return user_data
        
        return None

    def test_pending_user_login(self, user_data):
        """Test that pending users cannot login"""
        print("\n🔍 Testing Pending User Login (Should Fail)...")
        
        if not user_data:
            self.log_test("Pending User Login Test", False, "No user data available")
            return
        
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        # This should fail with 403
        self.run_test("Pending User Login (Should Fail)", "POST", "auth/login", 403, login_data)

    def test_admin_routes(self):
        """Test admin-only routes"""
        print("\n🔍 Testing Admin Routes...")
        
        if not self.admin_token:
            self.log_test("Admin Routes Test", False, "No admin token available")
            return
        
        # Test GET /api/admin/users
        users_response = self.run_test("List All Users", "GET", "admin/users", 200)
        
        # Test GET /api/admin/users/pending
        pending_response = self.run_test("List Pending Users", "GET", "admin/users/pending", 200)
        
        # Test GET /api/admin/stats
        stats_response = self.run_test("Get Admin Stats", "GET", "admin/stats", 200)
        
        if stats_response:
            expected_fields = ['total_users', 'pending_users', 'active_users', 'expired_users', 'blocked_users', 'admin_users']
            missing_fields = [field for field in expected_fields if field not in stats_response]
            if not missing_fields:
                self.log_test("Admin Stats Complete", True, "All expected fields present")
            else:
                self.log_test("Admin Stats Complete", False, f"Missing: {missing_fields}")
        
        # Test user management if we have pending users
        if pending_response and isinstance(pending_response, list) and len(pending_response) > 0:
            user_id = pending_response[0]['id']
            
            # Test approve user
            self.run_test("Approve User", "POST", f"admin/users/{user_id}/approve", 200)
            
            # Test block user
            self.run_test("Block User", "POST", f"admin/users/{user_id}/block", 200)
            
            # Test update user
            update_data = {
                "name": "Updated Name",
                "role": "user",
                "status": "active"
            }
            self.run_test("Update User", "PUT", f"admin/users/{user_id}", 200, update_data)

    def test_email_configuration(self):
        """Test email configuration routes"""
        print("\n🔍 Testing Email Configuration...")
        
        if not self.admin_token:
            self.log_test("Email Config Test", False, "No admin token available")
            return
        
        # Test GET email config
        self.run_test("Get Email Config", "GET", "admin/settings/email", 200)
        
        # Test POST email config
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_user": "test@test.com",
            "smtp_password": "testpass",
            "smtp_from_name": "Test System",
            "smtp_use_tls": True
        }
        self.run_test("Save Email Config", "POST", "admin/settings/email", 200, email_config)

    def run_all_tests(self):
        """Run all user management tests"""
        print(f"🚀 Starting User Management Tests for {self.base_url}")
        print("=" * 60)
        
        # Setup admin user
        admin_setup = self.setup_admin_user()
        
        # Test user registration (pending)
        user_data = self.test_user_registration_pending()
        
        # Test pending user login
        self.test_pending_user_login(user_data)
        
        # Test admin routes
        self.test_admin_routes()
        
        # Test email configuration
        self.test_email_configuration()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print(f"📊 User Management Test Results: {self.tests_passed}/{self.tests_run} passed")
        
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
    tester = UserManagementTester()
    report = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if report["success_rate"] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())