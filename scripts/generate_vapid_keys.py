#!/usr/bin/env python3
"""
VAPID Key Generator for Web Push Notifications

This script generates VAPID (Voluntary Application Server Identification) keys
for secure web push notifications in the OCR Document Scanner application.

Usage:
    python generate_vapid_keys.py
"""

import base64
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from datetime import datetime

def generate_vapid_keys():
    """Generate VAPID key pair for web push notifications."""
    
    # Generate private key using P-256 curve (required for VAPID)
    private_key = ec.generate_private_key(
        ec.SECP256R1(), 
        default_backend()
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize private key to PKCS#8 format
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key to uncompressed point format for VAPID
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # Extract raw key bytes for VAPID format
    private_key_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Convert to base64 URL-safe format (required for VAPID)
    private_key_b64 = base64.urlsafe_b64encode(private_key_raw).decode('utf-8').rstrip('=')
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    return {
        'private_key': private_key_b64,
        'public_key': public_key_b64,
        'private_key_pem': private_key_bytes.decode('utf-8'),
        'subject': 'mailto:admin@your-domain.com'
    }

def save_vapid_config(vapid_keys):
    """Save VAPID configuration to files."""
    
    # Create VAPID configuration for backend
    backend_config = f'''# VAPID Configuration for Web Push Notifications
# Add these to your .env.production file

VAPID_PRIVATE_KEY={vapid_keys['private_key']}
VAPID_PUBLIC_KEY={vapid_keys['public_key']}
VAPID_SUBJECT={vapid_keys['subject']}

# Alternative PEM format for private key
VAPID_PRIVATE_KEY_PEM="""
{vapid_keys['private_key_pem']}"""
'''
    
    # Create frontend configuration
    frontend_config = f'''// VAPID Public Key for Frontend
// Add this to your frontend environment variables or config

export const VAPID_PUBLIC_KEY = '{vapid_keys['public_key']}';

// For React .env file:
REACT_APP_VAPID_PUBLIC_KEY={vapid_keys['public_key']}

// Service Worker configuration
const applicationServerKey = '{vapid_keys['public_key']}';
'''

    # Create service worker update
    sw_config = f'''// Service Worker Push Notification Configuration
// Update your service worker with this configuration

const VAPID_PUBLIC_KEY = '{vapid_keys['public_key']}';

// Convert VAPID key for subscription
function urlB64ToUint8Array(base64String) {{
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {{
    outputArray[i] = rawData.charCodeAt(i);
  }}
  return outputArray;
}}

// Subscribe to push notifications
async function subscribeToPush() {{
  const registration = await navigator.serviceWorker.ready;
  
  const subscription = await registration.pushManager.subscribe({{
    userVisibleOnly: true,
    applicationServerKey: urlB64ToUint8Array(VAPID_PUBLIC_KEY)
  }});
  
  // Send subscription to server
  await fetch('/api/push/subscribe', {{
    method: 'POST',
    headers: {{
      'Content-Type': 'application/json'
    }},
    body: JSON.stringify(subscription)
  }});
}}
'''
    
    # Save configuration files
    with open('vapid_backend_config.txt', 'w') as f:
        f.write(backend_config)
    
    with open('vapid_frontend_config.js', 'w') as f:
        f.write(frontend_config)
        
    with open('vapid_service_worker.js', 'w') as f:
        f.write(sw_config)
    
    print("✅ VAPID configuration files created:")
    print("   - vapid_backend_config.txt")
    print("   - vapid_frontend_config.js") 
    print("   - vapid_service_worker.js")

def main():
    print("=" * 80)
    print("VAPID KEY GENERATOR FOR OCR DOCUMENT SCANNER")
    print("=" * 80)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        print("Generating VAPID key pair...")
        vapid_keys = generate_vapid_keys()
        
        print("=" * 80)
        print("VAPID KEYS GENERATED SUCCESSFULLY")
        print("=" * 80)
        
        print("\\n🔑 BACKEND CONFIGURATION:")
        print(f"VAPID_PRIVATE_KEY={vapid_keys['private_key']}")
        print(f"VAPID_PUBLIC_KEY={vapid_keys['public_key']}")
        print(f"VAPID_SUBJECT={vapid_keys['subject']}")
        
        print("\\n🌐 FRONTEND CONFIGURATION:")
        print(f"REACT_APP_VAPID_PUBLIC_KEY={vapid_keys['public_key']}")
        
        print("\\n📄 Save these to your configuration files:")
        save_vapid_config(vapid_keys)
        
        print("\\n" + "=" * 80)
        print("SECURITY NOTES:")
        print("1. Keep the private key SECRET - never expose it to the frontend")
        print("2. The public key can be safely used in frontend code")
        print("3. Update the subject email to your actual admin email")
        print("4. Store keys securely and back them up")
        print("5. These keys are used to authenticate your server with push services")
        print("=" * 80)
        
        print("\\nNext steps:")
        print("1. Add VAPID keys to your .env.production file")
        print("2. Update frontend environment with public key")
        print("3. Update service worker with push notification code")
        print("4. Test push notifications in your application")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\\nInstall required package:")
        print("pip install cryptography")
    except Exception as e:
        print(f"❌ Error generating VAPID keys: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()