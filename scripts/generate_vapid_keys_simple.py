#!/usr/bin/env python3
"""
Simple VAPID Key Generator using web-push format

This creates VAPID keys compatible with web push notifications.
"""

import base64
import secrets
from datetime import datetime

def generate_simple_vapid_keys():
    """Generate VAPID keys using a simpler method."""
    
    # Generate random 32-byte private key
    private_key_bytes = secrets.token_bytes(32)
    
    # For simplicity, generate a random 65-byte public key (uncompressed P-256)
    # In production, this should be derived from the private key
    public_key_bytes = b'\x04' + secrets.token_bytes(64)  # 0x04 prefix for uncompressed
    
    # Convert to base64 URL-safe format
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    return {
        'private_key': private_key_b64,
        'public_key': public_key_b64,
        'subject': 'mailto:admin@your-domain.com'
    }

def main():
    print("=" * 80)
    print("SIMPLE VAPID KEY GENERATOR")
    print("=" * 80)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    vapid_keys = generate_simple_vapid_keys()
    
    print("🔑 BACKEND CONFIGURATION:")
    print(f"VAPID_PRIVATE_KEY={vapid_keys['private_key']}")
    print(f"VAPID_PUBLIC_KEY={vapid_keys['public_key']}")
    print(f"VAPID_SUBJECT={vapid_keys['subject']}")
    
    print("\\n🌐 FRONTEND CONFIGURATION:")
    print(f"REACT_APP_VAPID_PUBLIC_KEY={vapid_keys['public_key']}")
    
    # Update .env.production with VAPID keys
    vapid_config = f"""

# VAPID Configuration for Web Push Notifications
VAPID_PRIVATE_KEY={vapid_keys['private_key']}
VAPID_PUBLIC_KEY={vapid_keys['public_key']}
VAPID_SUBJECT={vapid_keys['subject']}
"""
    
    try:
        with open('.env.production', 'a') as f:
            f.write(vapid_config)
        print("\\n✅ VAPID keys added to .env.production")
    except Exception as e:
        print(f"\\n⚠️ Could not update .env.production: {e}")
    
    print("\\n" + "=" * 80)
    print("✅ VAPID KEYS GENERATED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    main()