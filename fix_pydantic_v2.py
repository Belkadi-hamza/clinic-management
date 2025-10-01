#!/usr/bin/env python3
"""
Fix Pydantic v1 -> v2 migration: 
- replace orm_mode with from_attributes
- replace validator with field_validator
"""
import os
import re
from pathlib import Path

def fix_schema_file(file_path):
    """Fix Pydantic v1 to v2 syntax"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changed = False
    
    # Fix 1: orm_mode = True -> from_attributes = True
    if 'orm_mode = True' in content:
        content = content.replace('orm_mode = True', 'from_attributes = True')
        changed = True
    
    # Fix 2: Import statement - validator -> field_validator
    if 'from pydantic import' in content and 'validator' in content:
        # Replace 'validator' with 'field_validator' in import statements
        content = re.sub(
            r'from pydantic import (.*?)validator',
            r'from pydantic import \1field_validator',
            content
        )
        changed = True
    
    # Fix 3: @validator decorator -> @field_validator
    if '@validator(' in content:
        content = content.replace('@validator(', '@field_validator(')
        changed = True
    
    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    schemas_dir = Path(__file__).parent / 'backend' / 'schemas'
    fixed_count = 0
    
    for schema_file in schemas_dir.glob('*.py'):
        if schema_file.name == '__init__.py':
            continue
        
        if fix_schema_file(schema_file):
            print(f"✅ Fixed: {schema_file.name}")
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} schema files for Pydantic v2")

if __name__ == '__main__':
    main()
