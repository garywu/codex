#!/usr/bin/env python3
"""
Comprehensive Pattern Extractor for Enhanced project-init.json

Extracts patterns from the new comprehensive project-init.json structure that includes:
- Security best practices  
- Production configuration
- Code quality standards
- CI/CD workflows
- Monitoring and alerting
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def extract_security_patterns(security_section: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract patterns from security_best_practices section."""
    patterns = []
    
    # JWT Security Patterns
    if jwt_config := security_section.get("authentication_authorization", {}).get("jwt_tokens"):
        patterns.append({
            "name": "secure-jwt-storage",
            "category": "security",
            "priority": "MANDATORY",
            "description": "Store JWT secrets in secure credential manager, never hardcode",
            "rule": jwt_config.get("secure_key_storage", ""),
            "detection": {
                "regex": r"(jwt_secret|JWT_SECRET)\s*=\s*['\"][^'\"]+['\"]",
                "keywords": ["jwt_secret", "JWT_SECRET", "hardcode"],
                "confidence": 0.95
            },
            "fix": {
                "template": "Use environment variables or secure credential manager",
                "complexity": "medium",
                "auto_fixable": False,
                "suggestions": ["Use secrets manager", "Environment variables", "Vault integration"]
            },
            "examples": {
                "good": "jwt_secret = os.getenv('JWT_SECRET') or vault.get_secret('jwt_secret')",
                "bad": "jwt_secret = 'hardcoded-secret-key'"
            },
            "rationale": "Hardcoded secrets in code are a critical security vulnerability"
        })

    # CORS Security Pattern
    if cors_config := security_section.get("cors_configuration"):
        patterns.append({
            "name": "no-cors-wildcard",
            "category": "security", 
            "priority": "MANDATORY",
            "description": "NEVER use '*' in production CORS origins",
            "rule": cors_config.get("never_wildcard", ""),
            "detection": {
                "regex": r"cors.*origins.*[\[\"'][*][\"'\]]",
                "keywords": ["cors", "origins", "*", "wildcard"],
                "confidence": 0.9
            },
            "fix": {
                "template": "Replace '*' with specific allowed origins",
                "complexity": "simple",
                "auto_fixable": True,
                "suggestions": ["List specific domains", "Use environment-specific origins"]
            },
            "examples": {
                "good": "origins=['https://app.example.com', 'https://admin.example.com']",
                "bad": "origins=['*']"
            }
        })

    # Input Validation Patterns
    if validation := security_section.get("input_validation"):
        patterns.append({
            "name": "use-pydantic-validation",
            "category": "validation",
            "priority": "HIGH", 
            "description": "Use Pydantic for all API input validation",
            "rule": validation.get("validation_patterns", {}).get("pydantic_models", ""),
            "detection": {
                "regex": r"@app\.(post|put|patch).*def.*request.*:",
                "keywords": ["fastapi", "request", "validation"],
                "confidence": 0.8
            },
            "fix": {
                "template": "Create Pydantic model for request validation",
                "complexity": "medium",
                "auto_fixable": False
            }
        })

    # Error Sanitization Pattern
    if error_handling := security_section.get("error_handling"):
        patterns.append({
            "name": "sanitize-production-errors",
            "category": "security",
            "priority": "HIGH",
            "description": "Return generic error messages in production",
            "rule": error_handling.get("sanitization", {}).get("production_messages", ""),
            "detection": {
                "regex": r"raise.*Exception.*traceback|str\(e\)",
                "keywords": ["exception", "traceback", "debug"],
                "confidence": 0.75
            }
        })

    return patterns

def extract_production_patterns(production_section: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract patterns from production_configuration section."""
    patterns = []

    # Database Connection Pattern
    if db_config := production_section.get("database_management"):
        patterns.append({
            "name": "use-db-context-managers",
            "category": "database",
            "priority": "HIGH",
            "description": "Always use context managers for database sessions",
            "rule": db_config.get("session_management", {}).get("context_managers", ""),
            "detection": {
                "regex": r"session\s*=.*Session\(\)(?!\s*with)",
                "keywords": ["session", "Session", "context manager"],
                "confidence": 0.85
            },
            "fix": {
                "template": "with get_db_session() as session:",
                "complexity": "simple",
                "auto_fixable": True
            },
            "examples": {
                "good": "with get_db_session() as session:\n    result = session.query(User).all()",
                "bad": "session = SessionLocal()\nresult = session.query(User).all()\nsession.close()"
            }
        })

    # Health Check Pattern
    if deployment := production_section.get("deployment"):
        patterns.append({
            "name": "implement-health-checks",
            "category": "monitoring",
            "priority": "HIGH",
            "description": "Implement /health and /ready endpoints for container orchestration",
            "rule": deployment.get("health_checks", {}).get("liveness", ""),
            "detection": {
                "regex": r"@app\.get.*['\"][^'\"]*health[^'\"]*['\"]",
                "keywords": ["health", "endpoint", "liveness"],
                "confidence": 0.8
            }
        })

    # Observability Patterns
    if observability := production_section.get("observability"):
        if logging_config := observability.get("logging"):
            patterns.append({
                "name": "structured-logging",
                "category": "logging",
                "priority": "HIGH", 
                "description": "Use JSON structured logs with consistent schema",
                "rule": logging_config.get("structured", ""),
                "detection": {
                    "regex": r"logger\.(info|debug|warning|error)\([^{]",
                    "keywords": ["logger", "logging", "structured"],
                    "confidence": 0.7
                },
                "fix": {
                    "template": "Use structured logging with JSON format",
                    "complexity": "medium",
                    "auto_fixable": False
                },
                "examples": {
                    "good": "logger.info({'event': 'user_login', 'user_id': user.id, 'timestamp': now()})",
                    "bad": "logger.info(f'User {user.id} logged in at {timestamp}')"
                }
            })

    return patterns

def extract_code_quality_patterns(quality_section: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract patterns from code_quality_standards section."""
    patterns = []

    # Type Safety Patterns
    if type_safety := quality_section.get("type_safety"):
        if mypy_config := type_safety.get("mypy_configuration"):
            patterns.append({
                "name": "strict-type-checking",
                "category": "typing",
                "priority": "HIGH",
                "description": "Enable strict type checking in production code",
                "rule": mypy_config.get("strict_mode", ""),
                "detection": {
                    "regex": r"def\s+\w+\([^)]*\)(?!\s*->)",
                    "keywords": ["function", "typing", "return type"],
                    "confidence": 0.8
                },
                "fix": {
                    "template": "Add return type annotation",
                    "complexity": "simple",
                    "auto_fixable": False
                }
            })

        patterns.append({
            "name": "avoid-any-type",
            "category": "typing",
            "priority": "HIGH",
            "description": "Avoid Any type except at boundaries",
            "rule": mypy_config.get("no_any", ""),
            "detection": {
                "regex": r":\s*Any\b|List\[Any\]|Dict\[.*Any.*\]",
                "keywords": ["Any", "typing"],
                "confidence": 0.9
            },
            "fix": {
                "template": "Use specific types instead of Any",
                "complexity": "medium",
                "auto_fixable": False
            }
        })

    # Testing Patterns
    if testing := quality_section.get("testing_standards"):
        patterns.append({
            "name": "minimum-test-coverage",
            "category": "testing",
            "priority": "HIGH",
            "description": "Maintain 80% minimum code coverage",
            "rule": testing.get("coverage_requirements", {}).get("minimum", ""),
            "detection": {
                "regex": r"def\s+(?!test_)\w+.*:",
                "keywords": ["function", "coverage", "test"],
                "confidence": 0.6
            }
        })

    # Documentation Patterns
    if docs := quality_section.get("documentation"):
        patterns.append({
            "name": "public-function-docstrings",
            "category": "documentation",
            "priority": "MEDIUM",
            "description": "All public functions need docstrings",
            "rule": docs.get("code_documentation", {}).get("docstrings", ""),
            "detection": {
                "regex": r"def\s+(?!_)\w+.*:\n(?!\s*['\"])",
                "keywords": ["function", "docstring", "documentation"],
                "confidence": 0.85
            },
            "fix": {
                "template": "Add docstring with description and parameters",
                "complexity": "simple",
                "auto_fixable": False
            }
        })

    return patterns

def extract_ci_cd_patterns(ci_section: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract patterns from continuous_integration section."""
    patterns = []

    if precommit := ci_section.get("pre_commit_workflow"):
        patterns.append({
            "name": "zero-tolerance-precommit",
            "category": "ci_cd",
            "priority": "MANDATORY",
            "description": "ALL PRE-COMMIT ERRORS MUST BE FIXED - NO EXCEPTIONS",
            "rule": precommit.get("zero_tolerance_policy", {}).get("fundamental_rule", ""),
            "detection": {
                "regex": r"SKIP=.*git commit|git commit.*--no-verify",
                "keywords": ["SKIP", "no-verify", "pre-commit"],
                "confidence": 0.95
            },
            "fix": {
                "template": "Fix all pre-commit errors before committing",
                "complexity": "simple",
                "auto_fixable": False
            },
            "examples": {
                "good": "uv run pre-commit run --all-files && git commit -m 'fix: resolved all issues'",
                "bad": "SKIP=ruff git commit -m 'quick fix'"
            }
        })

    return patterns

def extract_dependency_patterns(deps_section: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract patterns from dependency_management section."""
    patterns = []

    if modern_tools := deps_section.get("modern_tools", {}).get("python"):
        patterns.append({
            "name": "use-uv-package-manager",
            "category": "dependencies",
            "priority": "HIGH", 
            "description": "Use uv for speed and reliability",
            "rule": modern_tools.get("package_manager", ""),
            "detection": {
                "regex": r"pip install|pip freeze|requirements\.txt",
                "keywords": ["pip", "requirements", "package manager"],
                "confidence": 0.8
            },
            "fix": {
                "template": "Replace pip with uv commands",
                "complexity": "simple",
                "auto_fixable": True,
                "suggestions": ["uv pip install", "uv pip freeze", "pyproject.toml"]
            },
            "examples": {
                "good": "uv pip install package-name",
                "bad": "pip install package-name"
            }
        })

    return patterns

def extract_mock_code_patterns(mock_section: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract patterns from mock_code_policy section."""
    patterns = []

    if strict_reqs := mock_section.get("strict_requirements"):
        patterns.append({
            "name": "mock-code-naming",
            "category": "testing",
            "priority": "MANDATORY",
            "description": "Mock functions must start with mock_ prefix and log warnings",
            "rule": "Mock code must be clearly identified and include runtime warnings",
            "detection": {
                "regex": r"def\s+((?!mock_)\w+).*mock|def\s+\w+.*:\s*#.*mock",
                "keywords": ["mock", "test", "warning"],
                "confidence": 0.85
            },
            "fix": {
                "template": "Add mock_ prefix and logfire.warning('⚠️ MOCK: ...')",
                "complexity": "simple",
                "auto_fixable": True
            },
            "examples": {
                "good": "def mock_process_payment():\n    logfire.warning('⚠️ MOCK: Using mock_process_payment - not for production')",
                "bad": "def process_payment():\n    # Mock implementation\n    return True"
            }
        })

    return patterns

def main():
    """Extract comprehensive patterns from enhanced project-init.json."""
    
    # Load the project-init.json
    project_init_path = Path("/Users/admin/work/project-init.json")
    
    if not project_init_path.exists():
        print(f"❌ Error: {project_init_path} not found")
        return
    
    with open(project_init_path) as f:
        data = json.load(f)
    
    print("🚀 Comprehensive Pattern Extraction from Enhanced project-init.json")
    print("=" * 70)
    
    all_patterns = []
    
    # Extract from different sections
    sections = [
        ("security_best_practices", extract_security_patterns),
        ("production_configuration", extract_production_patterns), 
        ("code_quality_standards", extract_code_quality_patterns),
        ("continuous_integration", extract_ci_cd_patterns),
        ("dependency_management", extract_dependency_patterns),
        ("mock_code_policy", extract_mock_code_patterns),
    ]
    
    for section_name, extractor_func in sections:
        if section_data := data.get(section_name):
            patterns = extractor_func(section_data)
            all_patterns.extend(patterns)
            print(f"📦 {section_name}: {len(patterns)} patterns")
    
    # Add metadata to each pattern
    for pattern in all_patterns:
        pattern.update({
            "source": "project-init-v3-comprehensive",
            "enabled": True,
            "tags": [pattern["category"], pattern["priority"].lower()],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
    
    # Statistics
    print(f"\n📊 Total Patterns Extracted: {len(all_patterns)}")
    
    # Group by category
    by_category = {}
    by_priority = {}
    
    for pattern in all_patterns:
        cat = pattern["category"]
        pri = pattern["priority"]
        by_category[cat] = by_category.get(cat, 0) + 1
        by_priority[pri] = by_priority.get(pri, 0) + 1
    
    print("\n📁 By Category:")
    for cat, count in sorted(by_category.items()):
        print(f"  • {cat:<15} {count} patterns")
    
    print("\n🎯 By Priority:")
    for pri in ["MANDATORY", "HIGH", "MEDIUM", "LOW"]:
        if count := by_priority.get(pri, 0):
            print(f"  • {pri:<10} {count} patterns")
    
    # Save patterns
    output_file = "comprehensive_patterns_v3.json"
    with open(output_file, "w") as f:
        json.dump(all_patterns, f, indent=2)
    
    print(f"\n✅ Saved {len(all_patterns)} comprehensive patterns to {output_file}")
    
    # Show critical patterns
    mandatory_patterns = [p for p in all_patterns if p["priority"] == "MANDATORY"]
    if mandatory_patterns:
        print(f"\n🔴 MANDATORY Patterns ({len(mandatory_patterns)}):")
        for pattern in mandatory_patterns:
            print(f"  • {pattern['name']}: {pattern['description']}")
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Review patterns: cat {output_file}")
    print(f"2. Import: uv run codex pattern bulk sync --file {output_file}")
    print(f"3. Test: uv run codex pattern list --priority MANDATORY")
    print(f"4. Scan: uv run codex scan .")

if __name__ == "__main__":
    main()