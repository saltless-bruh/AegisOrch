#!/usr/bin/env python3
"""
AegisOrch Wrapper
Running this script invokes the aegisorch package.
"""
import sys
import os

# Ensure the current directory is in sys.path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aegisorch.cli import main

if __name__ == '__main__':
    main()
