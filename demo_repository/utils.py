
import os
import hashlib
import logging

# Good: Proper logging setup
logger = logging.getLogger(__name__)

def hash_password(password):
    # Security issue: weak hashing
    return hashlib.md5(password.encode()).hexdigest()

def read_config_file(filename):
    # Path traversal vulnerability
    with open(filename, 'r') as f:
        return f.read()

def validate_email(email):
    # Weak validation
    return '@' in email and '.' in email

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_item(self, item):
        print(f"Adding item: {item}")  # Should use logger
        self.data.append(item)
    
    def process_all(self):
        logger.info(f"Processing {len(self.data)} items")  # Good logging
        for item in self.data:
            self.process_item(item)
    
    def process_item(self, item):
        # Missing error handling
        result = item.upper()
        return result
