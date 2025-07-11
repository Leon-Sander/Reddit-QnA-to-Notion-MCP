#!/usr/bin/env python3
"""
Simple script to generate secure API keys for the YouTube Transcript MCP server.
"""

import secrets
import string
import argparse

def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key."""
    # Include letters, digits, and safe special characters
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    parser = argparse.ArgumentParser(description="Generate secure API keys for MCP server")
    parser.add_argument("--length", type=int, default=32, help="Length of API key (default: 32)")
    parser.add_argument("--count", type=int, default=1, help="Number of API keys to generate (default: 1)")
    
    args = parser.parse_args()
    
    print(f"Generating {args.count} API key(s) with length {args.length}:")
    print()
    
    keys = []
    for i in range(args.count):
        key = generate_api_key(args.length)
        keys.append(key)
        print(f"Key {i+1}: {key}")
    
    print()
    print("For your .env file, use:")
    print(f"VALID_API_KEYS={','.join(keys)}")
    print()
    print("Keep these keys secure and don't share them publicly!")

if __name__ == "__main__":
    main() 