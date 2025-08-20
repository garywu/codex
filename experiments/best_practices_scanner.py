#!/usr/bin/env python3
"""
Best Practices Scanner - Recognize and learn from excellent implementations

This scanner identifies positive patterns and best practices across projects
to establish organizational standards and learning opportunities.
"""

import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class BestPracticesScanner:
    """
    Scanner that identifies and recognizes best practices across projects.

    Philosophy:
    - Learn from what's working well
    - Identify positive patterns to replicate
    - Establish organizational excellence standards
    - Recognize good architectural decisions
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.project_name = project_dir.name
        self.best_practices = []
        self.excellence_patterns = self._load_excellence_patterns()

    def _load_excellence_patterns(self) -> list[dict[str, Any]]:
        """Load patterns that identify best practices."""
        return [
            {
                "name": "pydantic_settings_usage",
                "category": "configuration_excellence",
                "description": "Proper use of Pydantic BaseSettings for configuration",
                "detection_rules": {
                    "content_patterns": [
                        "class\\s+\\w*Settings\\s*\\(\\s*BaseSettings\\s*\\)",
                        "from\\s+pydantic\\s+import\\s+.*BaseSettings",
                        "Field\\s*\\([^)]*description\\s*=",
                        "model_config\\s*=\\s*SettingsConfigDict",
                    ],
                    "file_patterns": [".*settings\\.py$", ".*config\\.py$"],
                },
                "excellence_indicators": [
                    "Environment variable integration",
                    "Type validation with Pydantic",
                    "Clear field descriptions",
                    "Proper defaults and validation",
                ],
            },
            {
                "name": "structured_api_responses",
                "category": "api_design_excellence",
                "description": "Use of Pydantic models for structured API responses",
                "detection_rules": {
                    "content_patterns": [
                        "class\\s+\\w*Response\\s*\\(\\s*BaseModel\\s*\\)",
                        "class\\s+\\w*Request\\s*\\(\\s*BaseModel\\s*\\)",
                        "->\\s*\\w*Response:",
                        "response_model\\s*=\\s*\\w*Response",
                    ]
                },
                "excellence_indicators": [
                    "Type-safe API contracts",
                    "Structured response formats",
                    "Clear data validation",
                    "OpenAPI schema generation",
                ],
            },
            {
                "name": "comprehensive_type_hints",
                "category": "type_safety_excellence",
                "description": "Comprehensive type hints throughout codebase",
                "detection_rules": {
                    "content_patterns": [
                        "def\\s+\\w+\\([^)]*\\)\\s*->\\s*\\w+:",
                        "from\\s+typing\\s+import",
                        "from\\s+typing_extensions\\s+import",
                        "\\w+:\\s*\\w+\\s*=",
                        "List\\[\\w+\\]",
                        "Dict\\[\\w+,\\s*\\w+\\]",
                        "Optional\\[\\w+\\]",
                        "Union\\[\\w+,\\s*\\w+\\]",
                    ]
                },
                "excellence_indicators": [
                    "Return type annotations",
                    "Parameter type hints",
                    "Variable type annotations",
                    "Generic type usage",
                ],
            },
            {
                "name": "proper_error_handling",
                "category": "reliability_excellence",
                "description": "Comprehensive and specific error handling",
                "detection_rules": {
                    "content_patterns": [
                        "except\\s+\\w+Error\\s+as\\s+\\w+:",
                        "except\\s+\\(\\w+,\\s*\\w+\\)\\s+as\\s+\\w+:",
                        "raise\\s+\\w+Error\\s*\\(",
                        "logger\\.(?:error|warning|exception)\\(",
                        "logging\\.(?:error|warning|exception)\\(",
                        "finally:",
                        "raise\\s+\\w+\\s+from\\s+\\w+",
                    ],
                    "anti_patterns": ["except:", "except Exception:", "pass  # ignore"],
                },
                "excellence_indicators": [
                    "Specific exception handling",
                    "Proper error logging",
                    "Exception chaining with 'from'",
                    "Resource cleanup with 'finally'",
                ],
            },
            {
                "name": "security_best_practices",
                "category": "security_excellence",
                "description": "Implementation of security best practices",
                "detection_rules": {
                    "content_patterns": [
                        "os\\.environ\\.get\\(['\"]\\w*(?:SECRET|KEY|TOKEN|PASSWORD)",
                        "secrets\\.token_\\w+\\(",
                        "bcrypt\\.hashpw\\(",
                        "Fernet\\(",
                        "allow_origins\\s*=\\s*\\[[^*]",
                        "rate_limit\\s*=",
                        "validate_\\w+\\(",
                        "@require_auth",
                        "@rate_limited",
                    ]
                },
                "excellence_indicators": [
                    "Environment variable usage for secrets",
                    "Cryptographically secure random generation",
                    "Password hashing",
                    "Encryption at rest",
                    "Specific CORS origins",
                    "Rate limiting implementation",
                    "Input validation",
                    "Authentication decorators",
                ],
            },
            {
                "name": "testing_excellence",
                "category": "testing_excellence",
                "description": "Comprehensive testing practices",
                "detection_rules": {
                    "content_patterns": [
                        "def\\s+test_\\w+\\(",
                        "@pytest\\.mark\\.\\w+",
                        "@pytest\\.fixture",
                        "assert\\s+\\w+",
                        "mock\\.patch\\(",
                        "TestClient\\(",
                        "pytest\\.raises\\(",
                        "parametrize\\(",
                    ],
                    "file_patterns": ["test_.*\\.py$", ".*_test\\.py$", "tests/.*\\.py$"],
                },
                "excellence_indicators": [
                    "Comprehensive test coverage",
                    "Fixture usage for setup",
                    "Parametrized tests",
                    "Mock usage for isolation",
                    "API testing with TestClient",
                    "Exception testing",
                ],
            },
            {
                "name": "documentation_excellence",
                "category": "documentation_excellence",
                "description": "Comprehensive code documentation",
                "detection_rules": {
                    "content_patterns": [
                        '"""[^"]{50,}"""',
                        'def\\s+\\w+\\([^)]*\\):[^:]*?\\n\\s*"""',
                        'class\\s+\\w+:[^:]*?\\n\\s*"""',
                        "Args:",
                        "Returns:",
                        "Raises:",
                        "Example:",
                        "Note:",
                    ]
                },
                "excellence_indicators": [
                    "Detailed docstrings",
                    "Parameter documentation",
                    "Return value documentation",
                    "Exception documentation",
                    "Usage examples",
                    "Implementation notes",
                ],
            },
            {
                "name": "lazy_loading_patterns",
                "category": "performance_excellence",
                "description": "Proper lazy loading and performance optimization",
                "detection_rules": {
                    "content_patterns": [
                        "@property",
                        "@cached_property",
                        "@lru_cache",
                        "functools\\.lru_cache",
                        "if\\s+self\\._\\w+\\s+is\\s+None:",
                        "\\.__getattr__\\(",
                        "lazy_import\\(",
                        "importlib\\.import_module",
                    ]
                },
                "excellence_indicators": [
                    "Property-based lazy loading",
                    "Cached computations",
                    "Conditional initialization",
                    "Dynamic imports",
                    "Memory-efficient patterns",
                ],
            },
            {
                "name": "dependency_injection",
                "category": "architecture_excellence",
                "description": "Proper dependency injection patterns",
                "detection_rules": {
                    "content_patterns": [
                        "def\\s+\\w+\\([^)]*:\\s*\\w+Protocol",
                        "def\\s+\\w+\\([^)]*\\w+Interface",
                        "@inject",
                        "Depends\\(",
                        "def\\s+get_\\w+\\(",
                        "app\\.dependency_overrides",
                    ]
                },
                "excellence_indicators": [
                    "Protocol-based interfaces",
                    "Dependency injection decorators",
                    "FastAPI dependency system",
                    "Testable architecture",
                    "Loose coupling",
                ],
            },
            {
                "name": "observability_integration",
                "category": "monitoring_excellence",
                "description": "Comprehensive logging and monitoring",
                "detection_rules": {
                    "content_patterns": [
                        "logfire\\.",
                        "structlog\\.",
                        "logging\\.getLogger\\(",
                        "logger\\s*=\\s*logging\\.getLogger",
                        "metrics\\.",
                        "prometheus_client",
                        "trace\\(",
                        "@timed",
                        "health_check",
                    ]
                },
                "excellence_indicators": [
                    "Structured logging",
                    "Modern logging libraries",
                    "Metrics collection",
                    "Distributed tracing",
                    "Health checks",
                    "Performance monitoring",
                ],
            },
            {
                "name": "async_best_practices",
                "category": "async_excellence",
                "description": "Proper async/await usage and patterns",
                "detection_rules": {
                    "content_patterns": [
                        "async\\s+def\\s+\\w+\\(",
                        "await\\s+\\w+\\(",
                        "asyncio\\.gather\\(",
                        "asyncio\\.create_task\\(",
                        "async\\s+with\\s+\\w+",
                        "aiohttp\\.",
                        "httpx\\.AsyncClient",
                    ]
                },
                "excellence_indicators": [
                    "Proper async function definitions",
                    "Correct await usage",
                    "Concurrent execution with gather",
                    "Async context managers",
                    "Async HTTP clients",
                ],
            },
            {
                "name": "package_organization",
                "category": "architecture_excellence",
                "description": "Well-organized package structure",
                "detection_rules": {
                    "file_patterns": [
                        "core/.*\\.py$",
                        "api/.*\\.py$",
                        "cli/.*\\.py$",
                        "models/.*\\.py$",
                        "services/.*\\.py$",
                    ],
                    "content_patterns": [
                        "__all__\\s*=\\s*\\[",
                        "from\\s+\\.\\w+\\s+import",
                        "from\\s+\\.\\.\\w+\\s+import",
                    ],
                },
                "excellence_indicators": [
                    "Clear package separation",
                    "Proper import structure",
                    "Explicit exports with __all__",
                    "Relative imports within packages",
                ],
            },
        ]

    def scan_project_excellence(self) -> dict[str, Any]:
        """Scan project for best practices and excellence patterns."""
        print(f"=== SCANNING {self.project_name.upper()} FOR BEST PRACTICES ===")

        # Analyze all Python files
        file_analysis = self._analyze_files()

        # Detect best practices
        practices_found = self._detect_best_practices(file_analysis)

        # Calculate excellence metrics
        excellence_metrics = self._calculate_excellence_metrics(practices_found)

        # Generate recommendations
        recommendations = self._generate_excellence_recommendations(practices_found)

        return {
            "project_name": self.project_name,
            "files_analyzed": len(file_analysis),
            "best_practices": practices_found,
            "excellence_metrics": excellence_metrics,
            "recommendations": recommendations,
            "summary": self._create_excellence_summary(practices_found, excellence_metrics),
        }

    def _analyze_files(self) -> dict[str, dict[str, Any]]:
        """Analyze all Python files in the project."""
        file_analysis = {}

        for py_file in self.project_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ["__pycache__", ".venv", ".git"]):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                relative_path = py_file.relative_to(self.project_dir)
                file_analysis[str(relative_path)] = {
                    "content": content,
                    "lines": lines,
                    "size": len(content),
                    "line_count": len(lines),
                    "type": self._classify_file_type(py_file, content),
                }
            except (OSError, UnicodeDecodeError):
                continue

        return file_analysis

    def _classify_file_type(self, file_path: Path, content: str) -> str:
        """Classify the type of file for targeted analysis."""
        path_str = str(file_path).lower()
        content_lower = content.lower()

        if "test" in path_str or "pytest" in content_lower:
            return "test"
        elif "cli.py" in path_str or "typer" in content_lower or "click" in content_lower:
            return "cli"
        elif "api" in path_str or "fastapi" in content_lower or "router" in content_lower:
            return "api"
        elif "settings.py" in path_str or "config.py" in path_str:
            return "config"
        elif "models" in path_str or "basemodel" in content_lower:
            return "models"
        elif "__init__.py" in path_str:
            return "package_init"
        else:
            return "core"

    def _detect_best_practices(self, file_analysis: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect best practices across all files."""
        practices_found = []

        for pattern in self.excellence_patterns:
            pattern_matches = self._find_pattern_matches(file_analysis, pattern)
            if pattern_matches:
                practices_found.append(
                    {
                        "pattern": pattern,
                        "matches": pattern_matches,
                        "strength": len(pattern_matches),
                        "excellence_score": self._calculate_pattern_excellence(pattern_matches),
                    }
                )

        return practices_found

    def _find_pattern_matches(
        self, file_analysis: dict[str, dict[str, Any]], pattern: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Find matches for a specific excellence pattern."""
        matches = []
        detection_rules = pattern.get("detection_rules", {})

        for file_path, analysis in file_analysis.items():
            file_matches = []

            # Check content patterns
            for content_pattern in detection_rules.get("content_patterns", []):
                for line_num, line in enumerate(analysis["lines"], 1):
                    if re.search(content_pattern, line):
                        file_matches.append(
                            {"type": "content", "line": line_num, "code": line.strip(), "pattern": content_pattern}
                        )

            # Check file patterns
            for file_pattern in detection_rules.get("file_patterns", []):
                if re.search(file_pattern, file_path):
                    file_matches.append({"type": "file", "pattern": file_pattern})

            # Check for anti-patterns (negative indicators)
            anti_pattern_count = 0
            for anti_pattern in detection_rules.get("anti_patterns", []):
                for line in analysis["lines"]:
                    if re.search(anti_pattern, line):
                        anti_pattern_count += 1

            if file_matches and anti_pattern_count == 0:
                matches.append(
                    {
                        "file": file_path,
                        "file_type": analysis["type"],
                        "matches": file_matches,
                        "match_count": len(file_matches),
                        "excellence_indicators": self._extract_excellence_indicators(file_matches, pattern),
                    }
                )

        return matches

    def _extract_excellence_indicators(self, matches: list[dict[str, Any]], pattern: dict[str, Any]) -> list[str]:
        """Extract specific excellence indicators from matches."""
        indicators = []
        excellence_indicators = pattern.get("excellence_indicators", [])

        # Simple mapping - could be more sophisticated
        if len(matches) >= 3:
            indicators.extend(excellence_indicators[:2])
        elif len(matches) >= 1:
            indicators.extend(excellence_indicators[:1])

        return indicators

    def _calculate_pattern_excellence(self, matches: list[dict[str, Any]]) -> float:
        """Calculate excellence score for a pattern (0.0 to 1.0)."""
        if not matches:
            return 0.0

        # Factors: file coverage, match frequency, file type diversity
        file_count = len(matches)
        total_matches = sum(m["match_count"] for m in matches)
        file_types = len(set(m["file_type"] for m in matches))

        # Normalize scores
        file_coverage_score = min(file_count / 10.0, 1.0)  # Max at 10 files
        match_frequency_score = min(total_matches / 50.0, 1.0)  # Max at 50 matches
        diversity_score = min(file_types / 5.0, 1.0)  # Max at 5 different types

        return (file_coverage_score + match_frequency_score + diversity_score) / 3.0

    def _calculate_excellence_metrics(self, practices_found: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate overall excellence metrics for the project."""
        if not practices_found:
            return {"overall_score": 0.0, "category_scores": {}}

        # Group by category
        category_scores = defaultdict(list)
        for practice in practices_found:
            category = practice["pattern"]["category"]
            category_scores[category].append(practice["excellence_score"])

        # Calculate category averages
        category_averages = {category: sum(scores) / len(scores) for category, scores in category_scores.items()}

        # Overall score
        overall_score = sum(category_averages.values()) / len(category_averages)

        return {
            "overall_score": overall_score,
            "category_scores": category_averages,
            "practices_count": len(practices_found),
            "excellence_level": self.get_excellence_level(overall_score),
        }

    def get_excellence_level(self, score: float) -> str:
        """Get excellence level description."""
        if score >= 0.8:
            return "EXCEPTIONAL"
        elif score >= 0.6:
            return "EXCELLENT"
        elif score >= 0.4:
            return "GOOD"
        elif score >= 0.2:
            return "DEVELOPING"
        else:
            return "NEEDS_IMPROVEMENT"

    def _generate_excellence_recommendations(self, practices_found: list[dict[str, Any]]) -> list[str]:
        """Generate recommendations to improve excellence."""
        recommendations = []

        # Find missing categories
        found_categories = set(p["pattern"]["category"] for p in practices_found)
        all_categories = set(p["category"] for p in self.excellence_patterns)
        missing_categories = all_categories - found_categories

        for category in missing_categories:
            if category == "security_excellence":
                recommendations.append("🔒 Implement security best practices (environment variables, rate limiting)")
            elif category == "testing_excellence":
                recommendations.append("🧪 Add comprehensive testing (fixtures, mocks, parametrized tests)")
            elif category == "documentation_excellence":
                recommendations.append("📚 Improve documentation (docstrings, examples, type hints)")
            elif category == "monitoring_excellence":
                recommendations.append("📊 Add observability (structured logging, metrics, health checks)")

        # Find weak areas
        weak_practices = [p for p in practices_found if p["excellence_score"] < 0.3]
        for practice in weak_practices:
            category = practice["pattern"]["category"]
            recommendations.append(f"⚡ Strengthen {category.replace('_', ' ')}")

        return recommendations[:5]  # Top 5 recommendations

    def _create_excellence_summary(self, practices_found: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
        """Create human-readable excellence summary."""
        timestamp = datetime.now().isoformat()

        # Top practices
        top_practices = sorted(practices_found, key=lambda x: x["excellence_score"], reverse=True)[:3]

        summary = f"""
BEST PRACTICES ANALYSIS for {self.project_name.upper()} ({timestamp})

EXCELLENCE LEVEL: {metrics.get('excellence_level', 'UNKNOWN')} ({metrics.get('overall_score', 0):.1%})

TOP STRENGTHS:
"""

        for i, practice in enumerate(top_practices, 1):
            pattern = practice["pattern"]
            score = practice["excellence_score"]
            summary += f"{i}. {pattern['description']} ({score:.1%})\n"
            for indicator in practice["matches"][0]["excellence_indicators"][:2]:
                summary += f"   ✅ {indicator}\n"

        summary += f"\nCATEGORY BREAKDOWN:\n"
        for category, score in metrics.get("category_scores", {}).items():
            level = self._get_excellence_level(score)
            summary += f"  {category.replace('_', ' ').title()}: {level} ({score:.1%})\n"

        summary += f"\nFILES ANALYZED: {metrics.get('practices_count', 0)} patterns found across {self.project_name}\n"
        summary += f"EXCELLENCE PRACTICES: {len(practices_found)} different best practices identified\n"

        return summary


def main():
    """Scan multiple projects for best practices."""
    work_dir = Path("/Users/admin/work")

    if not work_dir.exists():
        print(f"Work directory not found: {work_dir}")
        return

    print("=== ORGANIZATIONAL BEST PRACTICES ANALYSIS ===")
    print("Identifying excellence patterns across all projects...\n")

    all_results = []

    # Scan each project
    for project_dir in work_dir.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith("."):
            # Check if it looks like a Python project
            if any(
                (project_dir / indicator).exists() for indicator in ["pyproject.toml", "setup.py", "requirements.txt"]
            ) or list(project_dir.glob("*.py")):
                scanner = BestPracticesScanner(project_dir)
                result = scanner.scan_project_excellence()
                all_results.append(result)

                print(result["summary"])
                print("-" * 80)

    # Cross-project analysis
    print("\n=== CROSS-PROJECT EXCELLENCE ANALYSIS ===")

    if all_results:
        # Find organization-wide patterns
        all_practices = []
        for result in all_results:
            all_practices.extend(result["best_practices"])

        # Excellence leaders
        project_scores = [(r["project_name"], r["excellence_metrics"]["overall_score"]) for r in all_results]
        project_scores.sort(key=lambda x: x[1], reverse=True)

        print("\n🏆 EXCELLENCE LEADERBOARD:")
        for i, (project, score) in enumerate(project_scores, 1):
            level = BestPracticesScanner(Path(".")).get_excellence_level(score)
            print(f"  {i}. {project}: {level} ({score:.1%})")

        # Best practices to replicate
        practice_frequency = Counter()
        for result in all_results:
            for practice in result["best_practices"]:
                practice_frequency[practice["pattern"]["name"]] += 1

        print("\n🌟 MOST COMMON BEST PRACTICES:")
        for practice_name, count in practice_frequency.most_common(5):
            print(f"  • {practice_name}: {count}/{len(all_results)} projects")

        print("\n💡 ORGANIZATIONAL RECOMMENDATIONS:")
        print("  • Replicate excellence patterns from top-performing projects")
        print("  • Establish organization-wide standards based on best practices")
        print("  • Create learning sessions to share architectural insights")
        print("  • Implement excellence patterns as code review guidelines")


if __name__ == "__main__":
    main()
