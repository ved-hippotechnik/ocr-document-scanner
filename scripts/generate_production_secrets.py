#!/usr/bin/env python3
"""
Production Secret Generator for OCR Document Scanner

This script generates secure secrets for production deployment.
Run this script and copy the output to your .env.production file.

Usage:
    python generate_production_secrets.py
"""

import secrets
import string
import base64
import os
from datetime import datetime

def generate_secret_key(length=64):
    """Generate a secure secret key using URL-safe base64 encoding."""
    return secrets.token_urlsafe(length)

def generate_password(length=32, include_symbols=True):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    if include_symbols:
        alphabet += "!@#$%^&*"
    
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_django_secret():
    """Generate Django-style secret key."""
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

def main():
    print("=" * 80)
    print("OCR DOCUMENT SCANNER - PRODUCTION SECRETS GENERATOR")
    print("=" * 80)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nCopy these values to your .env.production file:")
    print("=" * 80)
    
    print("\n# Flask & JWT Secret Keys")
    print(f"SECRET_KEY={generate_secret_key(64)}")
    print(f"JWT_SECRET_KEY={generate_secret_key(64)}")
    
    print("\n# Database Passwords")
    print(f"POSTGRES_PASSWORD={generate_password(32)}")
    
    print("\n# Redis Password")
    print(f"REDIS_PASSWORD={generate_password(32)}")
    
    print("\n# Email Configuration")
    print(f"MAIL_PASSWORD={generate_password(24)}")
    
    print("\n# AWS Credentials (if using AWS)")
    print(f"AWS_SECRET_ACCESS_KEY={generate_secret_key(40)}")
    
    print("\n# Additional Secure Tokens")
    print(f"WEBHOOK_SECRET={generate_secret_key(32)}")
    print(f"API_SIGNING_KEY={generate_secret_key(32)}")
    
    print("\n" + "=" * 80)
    print("SECURITY NOTES:")
    print("1. Store these secrets securely (use a password manager)")
    print("2. Never commit these secrets to version control")
    print("3. Rotate secrets regularly (every 90 days minimum)")
    print("4. Use different secrets for each environment")
    print("5. Ensure secrets are backed up securely")
    print("=" * 80)
    
    print("\nNext steps:")
    print("1. Copy the above secrets to .env.production")
    print("2. Replace placeholder database and Redis connection strings")
    print("3. Configure SSL certificate paths")
    print("4. Set up proper CORS origins for your domain")
    print("5. Test the configuration in staging environment first")

if __name__ == "__main__":
    main()