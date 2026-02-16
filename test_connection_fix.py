#!/usr/bin/env python3
"""Quick test to verify the database connection fix works."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project to the path
sys.path.insert(0, os.path.dirname(__file__))

from lf_automator.automator.tokenpools.pools import TokenPool

def test_connection_persistence():
    """Test that database connections persist across multiple calls."""
    print("Testing database connection persistence...")
    
    try:
        # Create a token pool instance
        pool = TokenPool()
        print("✓ TokenPool created")
        
        # First call to get_total_available_tokens
        total1 = pool.get_total_available_tokens()
        print(f"✓ First call successful: {total1} tokens")
        
        # Second call - this would fail with "connection already closed" before the fix
        total2 = pool.get_total_available_tokens()
        print(f"✓ Second call successful: {total2} tokens")
        
        # Third call to be sure
        total3 = pool.get_total_available_tokens()
        print(f"✓ Third call successful: {total3} tokens")
        
        print("\n✅ All tests passed! Connection persistence is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection_persistence()
    sys.exit(0 if success else 1)
