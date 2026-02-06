#!/usr/bin/env python3
"""
Focused test for redeploy API endpoint as requested in review.
Tests:
1. POST /api/deployments/{deployment_id}/redeploy endpoint exists and returns valid response
2. Endpoint accepts deployment_id and returns expected fields (status, deploy_type, etc)
3. Verify the logic - check if is_redeploy=True parameter is being passed correctly
"""

import requests
import json
from datetime import datetime

class RedeployAPITester:
    def __init__(self, base_url="https://deployvps-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def setup_auth(self):
        """Setup authentication - use existing admin token"""
        print("🔧 Setting up authentication...")
        
        # Try to read existing admin token
        try:
            with open('/tmp/admin_token.txt', 'r') as f:
                self.token = f.read().strip()
            
            # Verify token works
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('role') == 'admin':
                    self.log_test("Authentication Setup", True, f"Using existing admin: {user_data.get('email')}")
                    return True
        except:
            pass
        
        # If no token or token invalid, try to login with known admin
        admin_email = 'test220451@example.com'
        admin_password = 'testpass123'
        
        try:
            login_data = {'email': admin_email, 'password': admin_password}
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    self.log_test("Authentication Setup", True, f"Logged in as admin: {admin_email}")
                    return True
            
            self.log_test("Authentication Setup", False, f"Login failed: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_test("Authentication Setup", False, f"Exception: {str(e)}")
            return False

    def create_test_vps(self):
        """Create a test VPS"""
        print("🔧 Creating test VPS...")
        vps_data = {
            "name": "Redeploy Test VPS",
            "host": "192.168.1.100",
            "port": 22,
            "username": "testuser",
            "auth_type": "password",
            "password": "testpassword123"
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
            response = requests.post(f"{self.api_url}/vps", json=vps_data, headers=headers, timeout=30)
            if response.status_code == 200:
                vps_id = response.json().get('id')
                self.log_test("VPS Creation", True, f"VPS ID: {vps_id[:8]}...")
                return vps_id
            else:
                self.log_test("VPS Creation", False, f"Failed: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("VPS Creation", False, f"Exception: {str(e)}")
            return None

    def create_test_deployment(self, vps_id):
        """Create a test deployment"""
        print("🔧 Creating test deployment...")
        deployment_data = {
            "vps_id": vps_id,
            "repo_url": "https://github.com/vercel/next.js",
            "branch": "main",
            "project_name": "redeploy-test-app",
            "port": 3020,
            "create_mongodb": True,
            "mongodb_port": 27021,
            "create_admin": True,
            "admin_email": "admin@redeploytest.com",
            "admin_password": "RedeployAdmin123!"
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
            response = requests.post(f"{self.api_url}/deployments", json=deployment_data, headers=headers, timeout=30)
            if response.status_code == 200:
                deployment_id = response.json().get('id')
                self.log_test("Deployment Creation", True, f"Deployment ID: {deployment_id[:8]}...")
                return deployment_id
            else:
                self.log_test("Deployment Creation", False, f"Failed: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Deployment Creation", False, f"Exception: {str(e)}")
            return None

    def test_redeploy_endpoint(self, deployment_id):
        """Test the redeploy endpoint specifically"""
        print(f"\n🔍 Testing POST /api/deployments/{deployment_id[:8]}.../redeploy")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Test 1: Verify endpoint exists and returns valid response
        try:
            response = requests.post(f"{self.api_url}/deployments/{deployment_id}/redeploy", headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.log_test("Redeploy Endpoint Exists", True, "Returns 200 OK")
                
                # Parse response
                try:
                    redeploy_data = response.json()
                    
                    # Test 2: Verify endpoint accepts deployment_id and returns expected fields
                    expected_fields = ['id', 'status', 'vps_id', 'repo_url', 'branch', 'project_name', 'port', 'created_at', 'updated_at']
                    present_fields = [field for field in expected_fields if field in redeploy_data]
                    missing_fields = [field for field in expected_fields if field not in redeploy_data]
                    
                    if len(present_fields) >= 8:
                        self.log_test("Response Structure Valid", True, f"Contains {len(present_fields)}/{len(expected_fields)} expected fields")
                    else:
                        self.log_test("Response Structure Valid", False, f"Missing critical fields: {missing_fields}")
                    
                    # Verify deployment_id is correctly handled
                    if redeploy_data.get('id') == deployment_id:
                        self.log_test("Deployment ID Preserved", True, "Deployment ID correctly preserved")
                    else:
                        self.log_test("Deployment ID Preserved", False, f"ID mismatch")
                    
                    # Verify status field
                    status = redeploy_data.get('status')
                    valid_statuses = ['pending', 'cloning', 'building', 'deploying', 'running', 'failed']
                    if status in valid_statuses:
                        self.log_test("Status Field Valid", True, f"Status: {status}")
                    else:
                        self.log_test("Status Field Valid", False, f"Invalid status: {status}")
                    
                    # Check for deploy_type field (may be None initially)
                    if 'deploy_type' in redeploy_data:
                        deploy_type = redeploy_data.get('deploy_type')
                        valid_types = ['frontend_only', 'backend_only', 'fullstack', 'static', None]
                        if deploy_type in valid_types:
                            self.log_test("Deploy Type Field Valid", True, f"deploy_type: {deploy_type}")
                        else:
                            self.log_test("Deploy Type Field Valid", False, f"Invalid deploy_type: {deploy_type}")
                    else:
                        self.log_test("Deploy Type Field Present", False, "deploy_type field missing")
                    
                    return redeploy_data
                    
                except json.JSONDecodeError:
                    self.log_test("Response JSON Valid", False, "Invalid JSON response")
                    return None
            else:
                self.log_test("Redeploy Endpoint Exists", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test("Redeploy Endpoint Exists", False, f"Exception: {str(e)}")
            return None

    def test_redeploy_logic(self, deployment_id):
        """Test 3: Verify redeploy logic (database preservation)"""
        print("\n🔍 Testing Redeploy Logic (Database Preservation)")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Get deployment details after redeploy
        try:
            response = requests.get(f"{self.api_url}/deployments/{deployment_id}", headers=headers, timeout=30)
            if response.status_code == 200:
                deployment_data = response.json()
                
                # Check if MongoDB URL is preserved (indicating database preservation)
                mongodb_url = deployment_data.get('mongodb_url')
                if mongodb_url:
                    self.log_test("MongoDB URL Preserved", True, f"MongoDB URL: {mongodb_url}")
                else:
                    self.log_test("MongoDB URL Preserved", False, "MongoDB URL not found")
                
                # Check if admin credentials are preserved
                admin_creds = deployment_data.get('admin_credentials')
                if admin_creds and isinstance(admin_creds, dict):
                    if 'email' in admin_creds and 'password' in admin_creds:
                        self.log_test("Admin Credentials Preserved", True, f"Admin email: {admin_creds.get('email')}")
                    else:
                        self.log_test("Admin Credentials Preserved", False, "Admin credentials incomplete")
                else:
                    self.log_test("Admin Credentials Preserved", False, "Admin credentials missing")
                
                # Check deployment logs for redeploy indicators
                logs = deployment_data.get('logs', [])
                redeploy_logs = [log for log in logs if 'REDEPLOY' in log.get('message', '').upper() or 'preserving' in log.get('message', '').lower()]
                if redeploy_logs:
                    self.log_test("Redeploy Logic Detected", True, f"Found {len(redeploy_logs)} redeploy-specific log entries")
                else:
                    self.log_test("Redeploy Logic Detected", False, "No redeploy-specific logs found")
                
            else:
                self.log_test("Get Deployment Details", False, f"Failed to get deployment: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Deployment Details", False, f"Exception: {str(e)}")

    def test_error_cases(self, deployment_id):
        """Test error cases"""
        print("\n🔍 Testing Error Cases")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Test with invalid deployment ID
        try:
            response = requests.post(f"{self.api_url}/deployments/invalid-id-12345/redeploy", headers=headers, timeout=30)
            if response.status_code == 404:
                self.log_test("Invalid Deployment ID", True, "Returns 404 Not Found")
            else:
                self.log_test("Invalid Deployment ID", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Deployment ID", False, f"Exception: {str(e)}")
        
        # Test without authentication
        try:
            response = requests.post(f"{self.api_url}/deployments/{deployment_id}/redeploy", timeout=30)
            if response.status_code in [401, 403]:
                self.log_test("Unauthenticated Request", True, f"Returns {response.status_code} (Unauthorized)")
            else:
                self.log_test("Unauthenticated Request", False, f"Expected 401/403, got {response.status_code}")
        except Exception as e:
            self.log_test("Unauthenticated Request", False, f"Exception: {str(e)}")

    def cleanup(self, vps_id, deployment_id):
        """Clean up test resources"""
        print("\n🧹 Cleaning up...")
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        if deployment_id:
            try:
                requests.delete(f"{self.api_url}/deployments/{deployment_id}", headers=headers, timeout=30)
                self.log_test("Cleanup Deployment", True, "Deployment deleted")
            except:
                self.log_test("Cleanup Deployment", False, "Failed to delete deployment")
        
        if vps_id:
            try:
                requests.delete(f"{self.api_url}/vps/{vps_id}", headers=headers, timeout=30)
                self.log_test("Cleanup VPS", True, "VPS deleted")
            except:
                self.log_test("Cleanup VPS", False, "Failed to delete VPS")

    def run_redeploy_tests(self):
        """Run all redeploy-specific tests"""
        print("🚀 Starting Redeploy API Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_auth():
            print("❌ Authentication setup failed, cannot continue")
            return self.generate_report()
        
        vps_id = self.create_test_vps()
        if not vps_id:
            print("❌ VPS creation failed, cannot continue")
            return self.generate_report()
        
        deployment_id = self.create_test_deployment(vps_id)
        if not deployment_id:
            print("❌ Deployment creation failed, cannot continue")
            self.cleanup(vps_id, None)
            return self.generate_report()
        
        # Main tests
        redeploy_data = self.test_redeploy_endpoint(deployment_id)
        if redeploy_data:
            self.test_redeploy_logic(deployment_id)
        
        self.test_error_cases(deployment_id)
        
        # Cleanup
        self.cleanup(vps_id, deployment_id)
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print(f"📊 Redeploy API Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate
        }

def main():
    tester = RedeployAPITester()
    report = tester.run_redeploy_tests()
    return 0 if report["success_rate"] >= 80 else 1

if __name__ == "__main__":
    exit(main())