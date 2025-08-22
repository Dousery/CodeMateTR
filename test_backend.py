#!/usr/bin/env python3
"""
Simple test script to check backend connectivity
"""
import requests
import json

def test_backend():
    base_url = "https://btk-project-backend.onrender.com"
    
    print("Testing backend connectivity...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Test health endpoint
    try:
        print("1. Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Database Status: {data.get('database_status', 'N/A')}")
            print(f"   Flask Env: {data.get('flask_env', 'N/A')}")
            print(f"   Gemini API Key: {data.get('gemini_api_key', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("-" * 50)
    
    # Test database endpoint
    try:
        print("2. Testing /db-test endpoint...")
        response = requests.get(f"{base_url}/db-test", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Database Test: {data.get('database_test', 'N/A')}")
            print(f"   Pool Info: {data.get('pool_info', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("-" * 50)
    
    # Test session status endpoint
    try:
        print("3. Testing /session-status endpoint...")
        response = requests.get(f"{base_url}/session-status", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Has Username: {data.get('has_username', 'N/A')}")
            print(f"   Has User ID: {data.get('has_user_id', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("-" * 50)
    print("Backend test completed!")

if __name__ == "__main__":
    test_backend()
