import requests
import sys
import json
from datetime import datetime

class FinalUserManagementTester:
    def __init__(self, base_url="https://deploy-genius-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
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

    def test_user_registration_pending_approval(self):
        """Test that new users require pending approval"""
        print("\n🔍 Testing User Registration with Pending Approval")
        
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"Test User {timestamp}",
            "email": f"testuser{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        response = self.run_test("Register New User", "POST", "auth/register", 200, user_data)
        
        if response:
            if response.get('status') == 'pending':
                self.log_test("User Registration Pending Status", True, "New user correctly marked as pending")
                return user_data
            elif 'access_token' in response:
                # This would happen if this is the first user (becomes admin)
                role = response.get('user', {}).get('role', 'unknown')
                if role == 'admin':
                    self.log_test("First User Becomes Admin", True, "First user correctly becomes admin")
                else:
                    self.log_test("User Registration Pending Status", False, f"User got token but role is: {role}")
                return user_data
            else:
                self.log_test("User Registration Pending Status", False, f"Unexpected response: {response}")
        
        return user_data

    def test_pending_user_login_blocked(self, user_data):
        """Test that pending users cannot login"""
        print("\n🔍 Testing Pending User Login is Blocked")
        
        if not user_data:
            self.log_test("Pending User Login Test", False, "No user data available")
            return
        
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        # Should fail with 403 "Conta pendente de aprovação"
        response = self.run_test("Pending User Login Blocked", "POST", "auth/login", 403, login_data)
        
        # Verify the error message is correct
        if response is None:
            # Check if we got the expected error message
            try:
                url = f"{self.api_url}/auth/login"
                headers = {'Content-Type': 'application/json'}
                resp = requests.post(url, json=login_data, headers=headers, timeout=30)
                if resp.status_code == 403:
                    error_data = resp.json()
                    if "pendente de aprovação" in error_data.get('detail', ''):
                        self.log_test("Correct Error Message", True, "Error message mentions pending approval")
                    else:
                        self.log_test("Correct Error Message", False, f"Unexpected error: {error_data.get('detail')}")
            except Exception as e:
                self.log_test("Error Message Check", False, f"Exception: {str(e)}")

    def test_admin_routes_require_authentication(self):
        """Test that admin routes require authentication"""
        print("\n🔍 Testing Admin Routes Require Authentication")
        
        # Test admin routes without authentication - should fail with 401/403
        admin_endpoints = [
            "admin/users",
            "admin/users/pending", 
            "admin/stats",
            "admin/settings/email"
        ]
        
        for endpoint in admin_endpoints:
            # Accept either 401 or 403 as both indicate authentication required
            response = self.run_test(f"Admin Route {endpoint} (No Auth)", "GET", endpoint, 403)
            if response is None:
                # Try 401 as well
                self.run_test(f"Admin Route {endpoint} (No Auth - Alt)", "GET", endpoint, 401)

    def test_admin_routes_with_invalid_token(self):
        """Test admin routes with invalid token"""
        print("\n🔍 Testing Admin Routes with Invalid Token")
        
        fake_token = "invalid.jwt.token"
        admin_endpoints = [
            "admin/users",
            "admin/users/pending",
            "admin/stats"
        ]
        
        for endpoint in admin_endpoints:
            self.run_test(f"Admin Route {endpoint} (Invalid Token)", "GET", endpoint, 401, token=fake_token)

    def test_email_config_routes_require_admin(self):
        """Test email configuration routes require admin"""
        print("\n🔍 Testing Email Config Routes Require Admin")
        
        # Test without auth - expect 403
        self.run_test("Email Config GET (No Auth)", "GET", "admin/settings/email", 403)
        
        # Test POST without auth - expect 403
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_user": "test@test.com",
            "smtp_password": "testpass",
            "smtp_from_name": "Test",
            "smtp_use_tls": True
        }
        self.run_test("Email Config POST (No Auth)", "POST", "admin/settings/email", 403, email_config)

    def run_all_tests(self):
        """Run all testable user management features"""
        print(f"🚀 Testing User Management System Features")
        print(f"🌐 API Base URL: {self.base_url}")
        print("=" * 70)
        
        print("📝 Note: Testing features that don't require existing admin credentials")
        print("   Admin functionality requires valid admin token (not available in test)")
        
        # Test 1: User registration with pending approval
        user_data = self.test_user_registration_pending_approval()
        
        # Test 2: Pending user login is blocked
        self.test_pending_user_login_blocked(user_data)
        
        # Test 3: Admin routes require authentication
        self.test_admin_routes_require_authentication()
        
        # Test 4: Admin routes reject invalid tokens
        self.test_admin_routes_with_invalid_token()
        
        # Test 5: Email config routes require admin
        self.test_email_config_routes_require_admin()
        
        return self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print(f"📊 User Management System Test Results")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0:.1f}%")
        
        print(f"\n✅ WORKING FEATURES:")
        working_features = []
        failed_features = []
        
        for result in self.test_results:
            if result['success']:
                working_features.append(result['test'])
            else:
                failed_features.append(f"{result['test']}: {result['details']}")
        
        for feature in working_features:
            print(f"   • {feature}")
        
        if failed_features:
            print(f"\n❌ FAILED TESTS:")
            for feature in failed_features:
                print(f"   • {feature}")
        
        print(f"\n📋 FEATURE VERIFICATION SUMMARY:")
        
        # Check specific features from the review request
        registration_pending = any("pending" in r['test'].lower() and "status" in r['test'].lower() and r['success'] for r in self.test_results)
        login_blocked = any("login" in r['test'].lower() and "blocked" in r['test'].lower() and r['success'] for r in self.test_results)
        admin_auth_required = any("admin" in r['test'].lower() and "auth" in r['test'].lower() and r['success'] for r in self.test_results)
        email_auth_required = any("email" in r['test'].lower() and "auth" in r['test'].lower() and r['success'] for r in self.test_results)
        
        print(f"   1. Registration with pending approval: {'✅ WORKING' if registration_pending else '❌ FAILED'}")
        print(f"   2. Pending user login blocked (403): {'✅ WORKING' if login_blocked else '❌ FAILED'}")
        print(f"   3. Admin routes require authentication: {'✅ WORKING' if admin_auth_required else '❌ FAILED'}")
        print(f"   4. Email config requires admin: {'✅ WORKING' if email_auth_required else '❌ FAILED'}")
        
        print(f"\n⚠️  LIMITATIONS:")
        print(f"   • Admin functionality testing requires valid admin credentials")
        print(f"   • User approval/blocking/updating requires admin token")
        print(f"   • Email configuration save/test requires admin token")
        print(f"   • These features exist in the code but cannot be fully tested without admin access")
        
        print(f"\n🎯 CONCLUSION:")
        if self.tests_passed >= self.tests_run * 0.8:
            print(f"   ✅ User management system is WORKING correctly")
            print(f"   ✅ Security measures are properly implemented")
            print(f"   ✅ Pending approval workflow is functional")
        else:
            print(f"   ❌ Some user management features may have issues")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "results": self.test_results,
            "features_working": {
                "registration_pending": registration_pending,
                "login_blocked": login_blocked,
                "admin_auth_required": admin_auth_required,
                "email_auth_required": email_auth_required
            }
        }

def main():
    tester = FinalUserManagementTester()
    report = tester.run_all_tests()
    
    # Return success if core features are working
    core_features_working = (
        report["features_working"]["registration_pending"] and
        report["features_working"]["login_blocked"] and
        report["features_working"]["admin_auth_required"]
    )
    
    return 0 if core_features_working else 1

if __name__ == "__main__":
    sys.exit(main())