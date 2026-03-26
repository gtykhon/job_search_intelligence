#!/usr/bin/env python3
"""
Test LinkedIn Authentication System
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_authentication():
    try:
        from src.core.linkedin_authenticator import LinkedInAuthenticator
        print('✅ LinkedInAuthenticator import successful')
        
        # Test credential loading
        auth = LinkedInAuthenticator(debug=True)
        print(f'✅ Credentials loaded: {auth.username[:10]}***')
        
        # Test cookie retrieval
        print('🔍 Testing cookie retrieval (this may take a moment)...')
        cookies = auth.get_cookies()
        if cookies:
            print(f'✅ Authentication successful! Got {len(cookies)} cookies')
            return True
        else:
            print('❌ Authentication failed - no cookies retrieved')
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_authentication()
    sys.exit(0 if success else 1)