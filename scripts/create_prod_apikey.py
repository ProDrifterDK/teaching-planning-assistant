#!/usr/bin/env python3
import requests
import json

TPA_BASE_URL = "https://teaching-planning-assistant-production.up.railway.app"

def get_admin_token():
    print("Getting admin token...")
    response = requests.post(
        f"{TPA_BASE_URL}/auth/token",
        data={"username": "admin", "password": "adminpass"},
        timeout=60
    )
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Got token: {token_data['access_token'][:20]}...")
        return token_data["access_token"]
    else:
        print(f"❌ Failed to get token: {response.status_code}")
        print(response.text)
        return None

def list_existing_keys(token):
    print("\nListing existing API keys...")
    response = requests.get(
        f"{TPA_BASE_URL}/admin/apikeys/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=60
    )
    if response.status_code == 200:
        keys = response.json()
        print(f"Found {len(keys)} existing keys:")
        for key in keys:
            print(f"  - {key['id']}: {key['client_name']} (active: {key['is_active']})")
        return keys
    else:
        print(f"Failed to list keys: {response.status_code}")
        print(response.text)
        return []

def create_api_key(token):
    print("\nCreating API key for 'colegio-alas-prod'...")
    response = requests.post(
        f"{TPA_BASE_URL}/admin/apikeys/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "client_name": "colegio-alas-prod",
            "permissions": [
                "batch:create",
                "batch:read",
                "generate:quiz",
                "generate:activity",
                "generate:exam",
                "generate:reinforcement",
                "generate:lesson"
            ],
            "rate_limit": 200
        },
        timeout=60
    )
    if response.status_code == 200:
        key_data = response.json()
        print(f"\n✅ API Key created successfully!")
        print(f"Client ID: {key_data['id']}")
        print(f"Client Name: {key_data['client_name']}")
        print(f"Permissions: {key_data['permissions']}")
        print(f"Rate Limit: {key_data['rate_limit']}")
        print(f"\n🔑 API KEY (save this - it won't be shown again!):")
        print(f"   {key_data['api_key']}")
        return key_data
    else:
        print(f"❌ Failed to create key: {response.status_code}")
        print(response.text)
        return None

def main():
    token = get_admin_token()
    if not token:
        return
    
    existing = list_existing_keys(token)
    
    colegio_exists = any(k['client_name'] == 'colegio-alas-prod' for k in existing)
    if colegio_exists:
        print("\n⚠️  'colegio-alas-prod' already exists!")
        print("If you need a new key, delete the existing one first.")
        return
    
    create_api_key(token)

if __name__ == "__main__":
    main()
