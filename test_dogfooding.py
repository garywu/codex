#!/usr/bin/env python3
"""
Test dogfooding setup - Codex scanning itself.

This file intentionally contains patterns that Codex should detect.
"""

import requests  # Should trigger: use-httpx-not-requests
import os

def bad_function():
    print("This should trigger no-print-statements")  # Bad: print statement
    
    config = {"port": 8080, "host": "localhost"}
    
    # Bad: using .get() with default for required parameter
    port = config.get("port", 8080)
    
    try:
        # Some code
        data = process_data()
    except:  # Bad: bare except clause
        pass
    
    return port

def another_bad_function():
    try:
        result = 10 / 0
    except Exception:  # Bad: broad exception
        return None

class HeimdallDaemon:  # Bad: redundant prefix if in heimdall package
    pass

# Bad: version suffix
def process_data_v2():
    pass

# File with backup suffix would be bad: config_backup.py