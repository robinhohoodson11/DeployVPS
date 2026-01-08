import requests
import sys
import json
from datetime import datetime

class ComprehensiveUserManagementTester:
    def __init__(self, base_url="https://deploy-genius-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.admin_user_id = None
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

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        elif self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Response: {error_data.get('detail', error_data)}"
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

    def test_1_registration_with_pending_approval(self):
        """Test 1: Registration with pending approval"""
        print("\n🔍 Test 1: Registration with Pending Approval")
        
        # Create multiple users to test the system
        timestamp = datetime.now().strftime('%H%M%S')
        
        # First user - might become admin if database is empty
        first_user_data = {
            "name": f"First User {timestamp}",
            "email": f"first{timestamp}@test.com",
            "password": "FirstPass123!"
        }
        
        first_response = self.run_test("Register First User", "POST", "auth/register", 200, first_user_data)
        
        if first_response:
            if 'access_token' in first_response:
                # First user became admin
                self.admin_token = first_response['access_token']
                self.admin_user_id = first_response['user']['id']
                role = first_response['user'].get('role', 'unknown')
                self.log_test("First User Role Check", role == 'admin', f"Role: {role}")
            elif first_response.get('status') == 'pending':
                self.log_test("First User Pending", True, "First user is pending (admin exists)")
        
        # Second user - should be pending
        second_user_data = {
            "name": f"Second User {timestamp}",
            "email": f"second{timestamp}@test.com",
            "password": "SecondPass123!"
        }
        
        second_response = self.run_test("Register Second User", "POST", "auth/register", 200, second_user_data)
        
        if second_response:
            if second_response.get('status') == 'pending':
                self.log_test("Second User Pending", True, "Second user correctly pending")
                return second_user_data
            else:
                self.log_test("Second User Pending", False, f"Expected pending, got: {second_response}")
        
        return second_user_data

    def test_2_login_of_pending_user(self, pending_user_data):
        """Test 2: Login of pending user should fail with 403"""
        print("\n🔍 Test 2: Login of Pending User (Should Fail)")
        
        if not pending_user_data:
            self.log_test("Pending User Login Test", False, "No pending user data")
            return
        
        login_data = {
            "email": pending_user_data["email"],
            "password": pending_user_data["password"]
        }
        
        # Should fail with 403
        self.run_test("Pending User Login (Should Fail)", "POST", "auth/login", 403, login_data)

    def test_3_admin_routes(self):
        """Test 3: Admin routes"""
        print("\n🔍 Test 3: Admin Routes")
        
        if not self.admin_token:
            self.log_test("Admin Routes", False, "No admin token available")
            return None
        
        # Test GET /api/admin/users
        users_response = self.run_test("GET /api/admin/users", "GET", "admin/users", 200)
        
        # Test GET /api/admin/users/pending
        pending_response = self.run_test("GET /api/admin/users/pending", "GET", "admin/users/pending", 200)
        
        # Test GET /api/admin/stats
        stats_response = self.run_test("GET /api/admin/stats", "GET", "admin/stats", 200)
        
        if stats_response:
            expected_fields = ['total_users', 'pending_users', 'active_users', 'expired_users', 'blocked_users', 'admin_users']
            missing_fields = [field for field in expected_fields if field not in stats_response]
            if not missing_fields:
                self.log_test("Admin Stats Fields", True, "All expected fields present")
            else:
                self.log_test("Admin Stats Fields", False, f"Missing: {missing_fields}")
        
        return pending_response

    def test_4_user_management_operations(self, pending_users):
        """Test 4: User management operations"""
        print("\n🔍 Test 4: User Management Operations")
        
        if not self.admin_token:
            self.log_test("User Management", False, "No admin token available")
            return
        
        if not pending_users or not isinstance(pending_users, list) or len(pending_users) == 0:
            self.log_test("User Management", False, "No pending users to test with")
            return
        
        user_id = pending_users[0]['id']
        
        # Test POST /api/admin/users/{id}/approve
        approve_response = self.run_test("POST /api/admin/users/{id}/approve", "POST", f"admin/users/{user_id}/approve", 200)
        
        # Test POST /api/admin/users/{id}/block
        block_response = self.run_test("POST /api/admin/users/{id}/block", "POST", f"admin/users/{user_id}/block", 200)
        
        # Test PUT /api/admin/users/{id}
        update_data = {
            "name": "Updated Test User",
            "role": "user",
            "status": "active",
            "expires_at": None
        }
        update_response = self.run_test("PUT /api/admin/users/{id}", "PUT", f"admin/users/{user_id}", 200, update_data)

    def test_5_email_configuration(self):
        """Test 5: Email configuration"""
        print("\n🔍 Test 5: Email Configuration")
        
        if not self.admin_token:
            self.log_test("Email Configuration", False, "No admin token available")
            return
        
        # Test GET /api/admin/settings/email
        get_response = self.run_test("GET /api/admin/settings/email", "GET", "admin/settings/email", 200)
        
        # Test POST /api/admin/settings/email
        email_config = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test@gmail.com",
            "smtp_password": "testpassword",
            "smtp_from_name": "DeployVPS Test",
            "smtp_from_email": "test@gmail.com",
            "smtp_use_tls": True
        }
        post_response = self.run_test("POST /api/admin/settings/email", "POST", "admin/settings/email", 200, email_config)

    def run_all_tests(self):
        """Run all user management tests"""
        print(f"🚀 Starting Comprehensive User Management Tests")
        print(f"🌐 Testing: {self.base_url}")
        print("=" * 70)
        
        # Test 1: Registration with pending approval
        pending_user_data = self.test_1_registration_with_pending_approval()
        
        # Test 2: Login of pending user
        self.test_2_login_of_pending_user(pending_user_data)
        
        # Test 3: Admin routes
        pending_users = self.test_3_admin_routes()
        
        # Test 4: User management operations
        self.test_4_user_management_operations(pending_users)
        
        # Test 5: Email configuration
        self.test_5_email_configuration()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 70)
        print(f"📊 User Management Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n✅ Passed Tests:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        # Summary of what was tested
        print(f"\n📋 Test Summary:")
        print(f"   • Registration with pending approval: {'✅' if any('Registration' in r['test'] and r['success'] for r in self.test_results) else '❌'}")
        print(f"   • Pending user login blocked: {'✅' if any('Should Fail' in r['test'] and r['success'] for r in self.test_results) else '❌'}")
        print(f"   • Admin routes accessible: {'✅' if any('admin' in r['test'].lower() and r['success'] for r in self.test_results) else '❌'}")
        print(f"   • User management operations: {'✅' if any('approve' in r['test'].lower() and r['success'] for r in self.test_results) else '❌'}")
        print(f"   • Email configuration: {'✅' if any('email' in r['test'].lower() and r['success'] for r in self.test_results) else '❌'}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "results": self.test_results,
            "admin_token_available": self.admin_token is not None
        }

def main():
    tester = ComprehensiveUserManagementTester()
    report = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if report["success_rate"] >= 70 else 1

if __name__ == "__main__":
    sys.exit(main())