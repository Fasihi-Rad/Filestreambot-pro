#!/usr/bin/env python3
"""
Test script to verify race condition fix for download limits.
This script simulates multiple concurrent requests to test the atomic limit checking.
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Adarsh.utils.database import Database


async def test_concurrent_limit_check():
    """Test concurrent limit checking to ensure no race conditions"""
    print("🧪 Testing concurrent download limit checks...")
    
    # Mock database setup
    mock_client = AsyncMock()
    mock_db = AsyncMock()
    mock_col = AsyncMock()
    
    db = Database("mock://uri", "test_db")
    db._client = mock_client
    db.db = mock_db
    db.col = mock_col
    
    # Mock user data
    test_user = {
        'id': 12345,
        'name': 'Test User',
        'status': 'free',
        'link_made': 3,  # Already made 3 links
        'total_download': 1000000,  # 1MB downloaded
        'link_date': '2025-09-25'
    }
    
    # Set daily limits (simulate 5 files, 5MB total)
    import Adarsh.vars
    Adarsh.vars.Var.DAILY_LIMIT_FILE = 5
    Adarsh.vars.Var.DAILY_LIMIT_DOWNLOAD = 5000000  # 5MB
    
    # Mock database response
    mock_col.find_one.return_value = test_user.copy()
    mock_col.update_one.return_value = AsyncMock()
    
    # Test scenario: User tries to upload 5 files simultaneously (should only allow 2)
    file_size = 500000  # 0.5MB per file
    user_id = 12345
    
    async def simulate_request(request_id):
        """Simulate a single file upload request"""
        print(f"  📤 Request {request_id}: Checking limits...")
        result = await db.check_user_link_limit(user_id, file_size)
        
        if result is True:
            print(f"  ✅ Request {request_id}: Limit check passed")
            # Simulate successful processing
            await asyncio.sleep(0.1)  # Simulate file processing time
            await db.consume_user_limits(user_id, file_size)
            print(f"  ✅ Request {request_id}: Limits consumed")
            return True
        elif result is False:
            print(f"  ❌ Request {request_id}: Daily limit exceeded")
            return False
        elif result == 2:
            print(f"  ❌ Request {request_id}: File too large")
            return False
    
    # Simulate 5 concurrent requests
    print("\n🚀 Starting 5 concurrent requests...")
    tasks = [simulate_request(i+1) for i in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_requests = sum(1 for r in results if r is True)
    failed_requests = sum(1 for r in results if r is False)
    
    print(f"\n📊 Results:")
    print(f"  ✅ Successful requests: {successful_requests}")
    print(f"  ❌ Failed requests: {failed_requests}")
    print(f"  🎯 Expected: 2 successful, 3 failed")
    
    if successful_requests == 2 and failed_requests == 3:
        print("  🎉 TEST PASSED: Race condition fixed!")
        return True
    else:
        print("  ⚠️  TEST FAILED: Race condition still exists!")
        return False


async def test_atomic_operations():
    """Test atomic database operations"""
    print("\n🧪 Testing atomic database operations...")
    
    # This would require a real database connection to test properly
    # For now, we'll just verify the method structure
    
    db = Database("mock://uri", "test_db")
    
    # Check if the new methods exist
    methods_to_check = ['check_user_link_limit', 'consume_user_limits', '_get_user_lock']
    
    for method in methods_to_check:
        if hasattr(db, method):
            print(f"  ✅ Method {method} exists")
        else:
            print(f"  ❌ Method {method} missing")
            return False
    
    print("  🎉 All required methods present!")
    return True


async def main():
    """Run all tests"""
    print("🧪 Starting Filestreambot Pro - Race Condition Tests")
    print("=" * 60)
    
    try:
        # Test 1: Atomic operations
        test1_result = await test_atomic_operations()
        
        # Test 2: Concurrent requests  
        test2_result = await test_concurrent_limit_check()
        
        print("\n" + "=" * 60)
        if test1_result and test2_result:
            print("🎉 ALL TESTS PASSED! Race condition has been fixed.")
        else:
            print("⚠️  SOME TESTS FAILED! Review the implementation.")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())