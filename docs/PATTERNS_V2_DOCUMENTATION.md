# Codex Patterns from Project-Init v2

## Overview

These patterns enforce the organizational principles from project-init.json v2.


## Dependencies Patterns

### use-uv-not-pip

**Priority**: HIGH

**Description**: Use uv for Python package management

**Rule**: Replace pip with uv for 10-100x faster installs

**Why**: uv is significantly faster and more reliable


**Good Example**:
```python
uv add requests
```


**Bad Example**:
```python
pip install requests
```


---


### pin-production-dependencies

**Priority**: HIGH

**Description**: Pin exact versions for production

**Rule**: Use == for production, >= only for libraries

**Why**: Ensures reproducible deployments


**Good Example**:
```python
requests==2.31.0
```


**Bad Example**:
```python
requests>=2.28.0
```


---


## Error_Handling Patterns

### no-bare-except

**Priority**: MANDATORY

**Description**: Never use bare except: clauses

**Rule**: Always catch specific exception types

**Why**: Bare except catches SystemExit, KeyboardInterrupt, and hides bugs


**Good Example**:
```python
except ValueError as e:
    logger.error('Invalid value', error=e)
```


**Bad Example**:
```python
except:
    pass  # Silently swallows all errors
```


---


### no-broad-exception

**Priority**: HIGH

**Description**: Avoid catching Exception without re-raising

**Rule**: Catch specific exceptions or re-raise after logging

**Why**: Broad exception handling masks programming errors


**Good Example**:
```python
except RequestException as e:
    logger.error('Request failed', error=e)
    raise
```


**Bad Example**:
```python
except Exception:
    return None  # Hides errors
```


---


### no-silent-defaults

**Priority**: HIGH

**Description**: Don't use .get() with defaults for required config

**Rule**: Required parameters should fail if missing

**Why**: Silent defaults hide configuration errors


**Good Example**:
```python
api_key = config['api_key']  # Fails if missing
```


**Bad Example**:
```python
api_key = config.get('api_key', 'default')  # Hides missing config
```


---


## Git Patterns

### conventional-commits

**Priority**: MEDIUM

**Description**: Use conventional commit messages

**Rule**: Format: type(scope): description

**Why**: Enables automatic changelog generation


**Good Example**:
```python
feat(auth): add OAuth2 support
```


**Bad Example**:
```python
Updated authentication system
```


---


## Imports Patterns

### standard-import-order

**Priority**: LOW

**Description**: Follow standard library, third-party, local import order

**Rule**: Group imports: stdlib, third-party, local

**Why**: Consistent import order improves readability


**Good Example**:
```python
import os\nimport sys\n\nimport requests\n\nfrom .config import settings
```


**Bad Example**:
```python
from .config import settings\nimport os
```


---


### prefer-relative-imports

**Priority**: MEDIUM

**Description**: Use relative imports within packages

**Rule**: Use from . imports for internal package modules

**Why**: Makes packages more portable and refactorable


**Good Example**:
```python
from .utils import helper
```


**Bad Example**:
```python
from mypackage.utils import helper
```


---


## Logging Patterns

### no-print-production

**Priority**: HIGH

**Description**: Replace print() with proper logging

**Rule**: Use logger instead of print in all production code

**Why**: Print statements can't be controlled or filtered in production


**Good Example**:
```python
logger.info('Processing', item_id=item_id)
```


**Bad Example**:
```python
print(f'Processing {item_id}')
```


---


### use-structured-logging

**Priority**: MEDIUM

**Description**: Use key-value pairs in logging

**Rule**: Log with structured data, not string formatting

**Why**: Structured logs are searchable and parseable


**Good Example**:
```python
logger.info('user_login', user_id=123, ip=request.ip)
```


**Bad Example**:
```python
logger.info(f'User {user_id} logged in from {ip}')
```


---


### centralized-logging-config

**Priority**: HIGH

**Description**: Configure logging in one central module

**Rule**: Single logging configuration imported everywhere

**Why**: Ensures consistent logging configuration


**Good Example**:
```python
from .logging_config import logger
```


**Bad Example**:
```python
logging.basicConfig(level=logging.INFO)  # In multiple files
```


---


## Naming Patterns

### no-package-stutter

**Priority**: HIGH

**Description**: Avoid repeating package name in module or class names

**Rule**: Within heimdall package, use daemon.py not heimdall_daemon.py

**Why**: Package context is already established by import path


**Good Example**:
```python
from heimdall import Daemon  # Not HeimdallDaemon
```


**Bad Example**:
```python
from heimdall import HeimdallDaemon  # Redundant
```


---


### no-version-in-filename

**Priority**: MANDATORY

**Description**: Never use version numbers in production filenames

**Rule**: Maintain single canonical implementation without v1, v2, etc.

**Why**: Version suffixes indicate unresolved technical debt


**Good Example**:
```python
cache_manager.py
```


**Bad Example**:
```python
cache_manager_v2.py
```


---


### no-impl-details-in-name

**Priority**: HIGH

**Description**: Don't include implementation details in names

**Rule**: Use functional names, not implementation specifics

**Why**: Implementation may change but purpose remains


**Good Example**:
```python
processor.py
```


**Bad Example**:
```python
processor_simple.py
```


---


## Organization Patterns

### no-backup-files

**Priority**: MANDATORY

**Description**: Remove backup/temporary files from version control

**Rule**: No _backup, _old, _tmp, .bak files in repository

**Why**: Backup files create confusion and security risks


**Good Example**:
```python
.gitignore contains *.bak
```


**Bad Example**:
```python
config_backup.py tracked in git
```


---


### organized-documentation

**Priority**: MEDIUM

**Description**: Keep documentation in organized structure

**Rule**: Use docs/ with api/, guides/, architecture/ subdirs

**Why**: Organized docs are easier to maintain and find


**Good Example**:
```python
docs/architecture/design.md
```


**Bad Example**:
```python
README_OLD.md in root
```


---


## Testing Patterns

### test-naming-convention

**Priority**: MEDIUM

**Description**: Follow test_{component}_{aspect}.py naming

**Rule**: Test files should clearly indicate what they test

**Why**: Clear test names improve discoverability


**Good Example**:
```python
test_auth_validation.py
```


**Bad Example**:
```python
auth_tests.py
```


---


## Validation Patterns

### fail-fast-validation

**Priority**: HIGH

**Description**: Validate inputs immediately and fail with clear errors

**Rule**: Check required parameters at function entry

**Why**: Early validation prevents cascading errors


**Good Example**:
```python
if not user_id:
    raise ValueError('user_id is required')
```


**Bad Example**:
```python
if not user_id:
    return None  # Silent failure
```


---


### pydantic-validation

**Priority**: HIGH

**Description**: Use Pydantic models for data validation

**Rule**: Replace manual validation with Pydantic models

**Why**: Pydantic provides automatic validation with clear errors


**Good Example**:
```python
class UserInput(BaseModel):
    name: str
    age: int
```


**Bad Example**:
```python
if not isinstance(data, dict):
    raise ValueError
```


---
