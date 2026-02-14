#!/usr/bin/env python3
"""
Manual test script for Jobs and Files endpoints
Run this to manually verify endpoints are working

Usage: python tests/integration/test_manual_jobs_files.py
"""

import requests
import json
import sys
from uuid import uuid4

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_jobs_endpoints():
    """Test Jobs endpoints"""
    print_section("Testing Jobs Endpoints")
    
    # Generate a test project_id (you may need to use a real one from your DB)
    test_project_id = str(uuid4())
    
    print(f"Using test project_id: {test_project_id}\n")
    
    # 1. Test creating a job with invalid UUID (should return 400)
    print("1. Testing invalid UUID format...")
    response = requests.post(
        f"{API_BASE}/jobs/",
        json={
            "project_id": "invalid-uuid-format",
            "status": "pending"
        },
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code} (Expected: 400)")
    if response.status_code == 400:
        print(f"   ✅ Correctly rejected invalid UUID")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    # 2. Test creating a job with missing project_id (should return 422)
    print("\n2. Testing missing project_id...")
    response = requests.post(
        f"{API_BASE}/jobs/",
        json={"status": "pending"},
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code} (Expected: 422)")
    if response.status_code in [400, 422]:
        print(f"   ✅ Correctly rejected missing project_id")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    # 3. Test creating a job with valid format (may return 400 if project doesn't exist)
    print("\n3. Testing valid UUID format (project may not exist)...")
    response = requests.post(
        f"{API_BASE}/jobs/",
        json={
            "project_id": test_project_id,
            "status": "pending",
            "transcript": "Test transcript"
        },
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   ✅ Job created successfully!")
        print(f"   Job ID: {data.get('id')}")
        print(f"   Project ID: {data.get('project_id')}")
        print(f"   Status: {data.get('status')}")
        return data.get('id')
    elif response.status_code == 400:
        print(f"   ⚠️  Job creation failed (project doesn't exist) - This is expected")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    # 4. Test listing jobs
    print("\n4. Testing list jobs endpoint...")
    response = requests.get(
        f"{API_BASE}/jobs/",
        params={"project_id": test_project_id},
        timeout=5
    )
    print(f"   Status: {response.status_code} (Expected: 200)")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Successfully retrieved jobs list")
        print(f"   Number of jobs: {len(data)}")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    # 5. Test getting a non-existent job (should return 404)
    print("\n5. Testing get non-existent job...")
    fake_job_id = "00000000-0000-0000-0000-000000000999"
    response = requests.get(
        f"{API_BASE}/jobs/{fake_job_id}",
        timeout=5
    )
    print(f"   Status: {response.status_code} (Expected: 404)")
    if response.status_code == 404:
        print(f"   ✅ Correctly returned 404 for non-existent job")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    return None

def test_files_endpoints():
    """Test Files endpoints"""
    print_section("Testing Files Endpoints")
    
    # Generate a test job_id (you may need to use a real one from your DB)
    test_job_id = str(uuid4())
    
    print(f"Using test job_id: {test_job_id}\n")
    
    # 1. Test creating a file with invalid UUID (should return 400)
    print("1. Testing invalid UUID format...")
    response = requests.post(
        f"{API_BASE}/files/",
        json={
            "job_id": "invalid-uuid-format",
            "file_url": "https://example.com/test.dxf"
        },
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code} (Expected: 400)")
    if response.status_code == 400:
        print(f"   ✅ Correctly rejected invalid UUID")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    # 2. Test creating a file with missing job_id (should return 422)
    print("\n2. Testing missing job_id...")
    response = requests.post(
        f"{API_BASE}/files/",
        json={"file_url": "https://example.com/test.dxf"},
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code} (Expected: 422)")
    if response.status_code in [400, 422]:
        print(f"   ✅ Correctly rejected missing job_id")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    # 3. Test creating a file with valid format (may return 400 if job doesn't exist)
    print("\n3. Testing valid UUID format (job may not exist)...")
    response = requests.post(
        f"{API_BASE}/files/",
        json={
            "job_id": test_job_id,
            "file_url": "https://example.com/test-manual.dxf",
            "file_type": "dxf"
        },
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   ✅ File created successfully!")
        print(f"   File ID: {data.get('id')}")
        print(f"   Job ID: {data.get('job_id')}")
        print(f"   File URL: {data.get('file_url')}")
        print(f"   File Type: {data.get('file_type')}")
        return data.get('id')
    elif response.status_code == 400:
        print(f"   ⚠️  File creation failed (job doesn't exist) - This is expected")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    # 4. Test creating a file with default file_type
    print("\n4. Testing default file_type (dxf)...")
    response = requests.post(
        f"{API_BASE}/files/",
        json={
            "job_id": test_job_id,
            "file_url": "https://example.com/test-default.dxf"
            # file_type not provided - should default to 'dxf'
        },
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   ✅ File created with default type!")
        print(f"   File Type: {data.get('file_type')} (Expected: dxf)")
        if data.get('file_type') == 'dxf':
            print(f"   ✅ Default file_type is correct")
    elif response.status_code == 400:
        print(f"   ⚠️  File creation failed (job doesn't exist) - This is expected")
    
    # 5. Test listing files
    print("\n5. Testing list files endpoint...")
    response = requests.get(
        f"{API_BASE}/files/",
        params={"job_id": test_job_id},
        timeout=5
    )
    print(f"   Status: {response.status_code} (Expected: 200)")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Successfully retrieved files list")
        print(f"   Number of files: {len(data)}")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    # 6. Test getting a non-existent file (should return 404)
    print("\n6. Testing get non-existent file...")
    fake_file_id = "00000000-0000-0000-0000-000000000999"
    response = requests.get(
        f"{API_BASE}/files/{fake_file_id}",
        timeout=5
    )
    print(f"   Status: {response.status_code} (Expected: 404)")
    if response.status_code == 404:
        print(f"   ✅ Correctly returned 404 for non-existent file")
    else:
        print(f"   ❌ Unexpected status: {response.text}")
    
    return None

def main():
    """Run all manual tests"""
    print("\n" + "="*60)
    print("  Manual Testing: Jobs and Files Endpoints")
    print("="*60)
    print("\nMake sure the server is running on http://localhost:8000")
    print("Press Ctrl+C to cancel\n")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            sys.exit(1)
        print("✅ Server is running\n")
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start it with: make run")
        sys.exit(1)
    
    # Test Jobs endpoints
    job_id = test_jobs_endpoints()
    
    # Test Files endpoints
    file_id = test_files_endpoints()
    
    print_section("Test Summary")
    print("✅ All endpoint tests completed!")
    print("\nNote: 400 errors are expected when:")
    print("  - Project/Job doesn't exist in database")
    print("  - Foreign key constraints are not met")
    print("\nThe important thing is that:")
    print("  ✅ Invalid UUIDs are rejected (400)")
    print("  ✅ Missing fields are rejected (422)")
    print("  ✅ Non-existent resources return 404")
    print("  ✅ Valid requests return proper status codes")

if __name__ == "__main__":
    main()

