#!/usr/bin/env python
"""
Generate a Django secret key for use in .env file
"""
from django.core.management.utils import get_random_secret_key

if __name__ == '__main__':
    print("Generated Django Secret Key:")
    print(get_random_secret_key())
    print("\nCopy this key to your .env file as SECRET_KEY=")


