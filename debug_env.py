#!/usr/bin/env python3
"""
Debug script to check environment variables
"""

import os
from dotenv import load_dotenv

def debug_env_vars():
    """Debug environment variable loading"""
    print("🔍 Environment Variable Debug")
    print("=" * 50)
    
    # Check system environment variables BEFORE loading .env
    print("🖥️  System environment variables (before .env):")
    email_vars = ['EMAIL_USER', 'EMAIL_PASSWORD', 'EMAIL_HOST', 'EMAIL_PORT']
    for var in email_vars:
        value = os.environ.get(var)
        if value:
            print(f"  {var}: '{value}' (from system)")
        else:
            print(f"  {var}: Not set in system")
    
    # Load .env file
    print("\n📁 Loading .env file...")
    load_dotenv(override=True)  # Force override system variables
    
    # Check all email-related environment variables AFTER loading .env
    print("\n📧 Environment variables (after .env):")
    for var in email_vars:
        value = os.getenv(var)
        print(f"{var}: '{value}' (length: {len(value) if value else 'None'})")
        
        # Check for hidden characters
        if value:
            print(f"  Repr: {repr(value)}")
            print(f"  Bytes: {value.encode('utf-8')}")
    
    print("\n📄 Raw .env file content:")
    try:
        with open('.env', 'r') as f:
            content = f.read()
            print(repr(content))
    except Exception as e:
        print(f"Error reading .env: {e}")
    
    # Try to load .env manually
    print("\n🔧 Manual .env parsing:")
    try:
        with open('.env', 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith('EMAIL_USER='):
                    print(f"Line {line_num}: {repr(line)}")
                    email_part = line.split('=', 1)[1]
                    print(f"Email value: {repr(email_part)}")
    except Exception as e:
        print(f"Error manually parsing .env: {e}")

if __name__ == "__main__":
    debug_env_vars()
