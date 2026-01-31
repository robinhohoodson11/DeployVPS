import requests
import json
from datetime import datetime

def test_deployment_api():
    """Quick test of deployment API with new fields"""
    base_url = "https://appdeployer-1.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Testing DeployVPS API - New Deployment Features")
    print("=" * 60)
    
    # Step 1: Register and get token
    print("\n1. Registering user...")
    timestamp = datetime.now().strftime('%H%M%S')
    user_data = {
        "name": f"Quick Test User {timestamp}",
        "email": f"quicktest{timestamp}@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{api_url}/auth/register", json=user_data, timeout=10)
        if response.status_code == 200:
            token = response.json()['access_token']
            print("✅ User registered successfully")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Step 2: Create VPS
    print("\n2. Creating VPS...")
    vps_data = {
        "name": "Quick Test VPS",
        "host": "192.168.1.100",
        "port": 22,
        "username": "testuser",
        "auth_type": "password",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{api_url}/vps", json=vps_data, headers=headers, timeout=10)
        if response.status_code == 200:
            vps_id = response.json()['id']
            print("✅ VPS created successfully")
        else:
            print(f"❌ VPS creation failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ VPS creation error: {e}")
        return
    
    # Step 3: Test deployment with new fields
    print("\n3. Testing deployment with new admin fields...")
    deployment_data = {
        "vps_id": vps_id,
        "repo_url": "https://github.com/facebook/react",
        "branch": "main",
        "project_name": "quick-test-app",
        "port": 3001,
        "create_mongodb": True,
        "mongodb_port": 27018,
        "create_admin": True,
        "admin_email": "admin@quicktest.com",
        "admin_password": "QuickAdmin123!"
    }
    
    try:
        response = requests.post(f"{api_url}/deployments", json=deployment_data, headers=headers, timeout=15)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Deployment created successfully")
            
            # Check for new fields in response
            print("\n4. Checking response fields...")
            
            fields_to_check = {
                'deploy_type': 'Deploy Type',
                'backend_port': 'Backend Port', 
                'admin_credentials': 'Admin Credentials',
                'id': 'Deployment ID',
                'status': 'Status'
            }
            
            for field, description in fields_to_check.items():
                if field in result:
                    value = result[field]
                    print(f"✅ {description}: {value}")
                else:
                    print(f"❌ {description}: Missing")
            
            # Test getting deployment details
            deployment_id = result.get('id')
            if deployment_id:
                print(f"\n5. Getting deployment details for {deployment_id[:8]}...")
                try:
                    detail_response = requests.get(f"{api_url}/deployments/{deployment_id}", headers=headers, timeout=10)
                    if detail_response.status_code == 200:
                        detail_result = detail_response.json()
                        print("✅ Deployment details retrieved")
                        
                        # Check admin credentials in detail response
                        admin_creds = detail_result.get('admin_credentials')
                        if admin_creds:
                            print(f"✅ Admin Credentials: {admin_creds}")
                        else:
                            print("❌ Admin Credentials: Not found in details")
                    else:
                        print(f"❌ Failed to get deployment details: {detail_response.status_code}")
                except Exception as e:
                    print(f"❌ Error getting deployment details: {e}")
        else:
            print(f"❌ Deployment creation failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Error text: {response.text}")
                
    except Exception as e:
        print(f"❌ Deployment creation error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Quick test completed")

if __name__ == "__main__":
    test_deployment_api()