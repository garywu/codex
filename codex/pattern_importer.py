"""
Pattern importer for extracting patterns from project-init.json and other sources.
"""

from typing import Any

from .exceptions import PatternImportError
from .models import Pattern, PatternCategory, PatternPriority
from .unified_database import UnifiedDatabase


class PatternImporter:
    """Import patterns from various sources into the database."""

    def __init__(self, database: UnifiedDatabase):
        """Initialize with unified database connection."""
        self.db = database

    async def import_from_project_init(self, data: dict[str, Any]) -> list[Pattern]:
        """Import patterns from project-init.json structure."""
        patterns = []

        try:
            template = data.get("project_initialization_template", {})

            # Import package management patterns
            if "tech_stack" in template:
                tech_stack = template["tech_stack"]

                # UV package management pattern
                if "package_management" in tech_stack:
                    uv_config = tech_stack["package_management"].get("uv", {})
                    pattern = Pattern(
                        name="uv_package_management",
                        category=PatternCategory.PACKAGE_MANAGEMENT,
                        priority=PatternPriority.MANDATORY,
                        description=uv_config.get("purpose", "Use UV for Python package management"),
                        pattern_code="uv init && uv sync",
                        anti_pattern="pip install, poetry install, conda install",
                        detection_rules={
                            "files": ["pyproject.toml", "uv.lock"],
                            "forbidden": ["requirements.txt", "poetry.lock", "Pipfile"],
                        },
                        source="project-init",
                        tags=["uv", "package-management", "python"],
                        best_practices=["Always use uv for dependency management"],
                    )
                    patterns.append(await self.db.add_pattern(pattern))

                # Core libraries patterns
                for lib in tech_stack.get("core_libraries", []):
                    pattern = Pattern(
                        name=f"use_{lib['name']}",
                        category=PatternCategory.CORE_LIBRARIES,
                        priority=self._parse_priority(lib.get("priority", "medium")),
                        description=lib.get("purpose", ""),
                        pattern_code=lib.get("integration_pattern", {}).get("usage", ""),
                        detection_rules={
                            "imports": [lib["name"]],
                            "version": lib.get("version", ""),
                        },
                        source="project-init",
                        tags=[lib["name"], "library"],
                        when_to_use=lib.get("when_to_use", []),
                        best_practices=lib.get("best_practices", []),
                    )
                    patterns.append(await self.db.add_pattern(pattern))

                # Quality tools patterns
                for tool in tech_stack.get("quality_tools", []):
                    pattern = Pattern(
                        name=f"use_{tool['name']}",
                        category=PatternCategory.QUALITY_TOOLS,
                        priority=self._parse_priority(tool.get("priority", "high")),
                        description=tool.get("purpose", ""),
                        detection_rules=tool.get("configuration", {}),
                        source="project-init",
                        tags=[tool["name"], "quality", "tooling"],
                        best_practices=tool.get("best_practices", []),
                    )
                    patterns.append(await self.db.add_pattern(pattern))

            # Import implementation patterns
            if "implementation_patterns" in template:
                for pattern_name, pattern_data in template["implementation_patterns"].items():
                    if isinstance(pattern_data, dict):
                        pattern = Pattern(
                            name=pattern_name,
                            category=self._categorize_pattern(pattern_name),
                            priority=PatternPriority.HIGH,
                            description=pattern_data.get("purpose", ""),
                            detection_rules=pattern_data.get("patterns", {}),
                            source="project-init",
                            tags=self._extract_tags(pattern_data),
                            best_practices=pattern_data.get("best_practices", []),
                        )
                        patterns.append(await self.db.add_pattern(pattern))

            # Import decorator patterns
            if "decorators" in template:
                for decorator_group in template["decorators"].get("cross_cutting_concerns", []):
                    pattern = Pattern(
                        name=decorator_group["name"],
                        category=PatternCategory.DECORATORS,
                        priority=PatternPriority.MEDIUM,
                        description=decorator_group.get("purpose", ""),
                        pattern_code=f"@{decorator_group['name']}",
                        source="project-init",
                        tags=["decorator", "cross-cutting"],
                    )
                    patterns.append(await self.db.add_pattern(pattern))

            # Import security patterns
            if "best_practices" in template:
                for security_practice in template["best_practices"].get("security", []):
                    if isinstance(security_practice, str):
                        pattern = Pattern(
                            name=f"security_{security_practice[:30].replace(' ', '_').lower()}",
                            category=PatternCategory.SECURITY,
                            priority=PatternPriority.CRITICAL,
                            description=security_practice,
                            source="project-init",
                            tags=["security", "best-practice"],
                        )
                        patterns.append(await self.db.add_pattern(pattern))

            return patterns

        except Exception as e:
            raise PatternImportError("project-init.json", str(e)) from e

    def _parse_priority(self, priority_str: str) -> PatternPriority:
        """Parse priority string to enum."""
        priority_map = {
            "mandatory": PatternPriority.MANDATORY,
            "critical": PatternPriority.CRITICAL,
            "high": PatternPriority.HIGH,
            "medium": PatternPriority.MEDIUM,
            "low": PatternPriority.LOW,
            "optional": PatternPriority.OPTIONAL,
        }
        return priority_map.get(priority_str.lower(), PatternPriority.MEDIUM)

    def _categorize_pattern(self, pattern_name: str) -> PatternCategory:
        """Categorize pattern based on name."""
        category_map = {
            "api": PatternCategory.API_DESIGN,
            "testing": PatternCategory.TESTING,
            "error": PatternCategory.ERROR_HANDLING,
            "validation": PatternCategory.VALIDATION,
            "resource": PatternCategory.RESOURCE_MANAGEMENT,
            "database": PatternCategory.DATABASE,
            "mock": PatternCategory.TESTING,
            "functional": PatternCategory.FUNCTIONAL,
            "unified": PatternCategory.API_DESIGN,
            "graceful": PatternCategory.ERROR_HANDLING,
        }

        for key, category in category_map.items():
            if key in pattern_name.lower():
                return category

        return PatternCategory.PROJECT_STRUCTURE

    def _extract_tags(self, pattern_data: dict[str, Any]) -> list[str]:
        """Extract tags from pattern data."""
        tags = []

        # Extract from various fields
        if "patterns" in pattern_data:
            tags.extend(pattern_data["patterns"][:3])
        if "libraries" in pattern_data:
            tags.extend(pattern_data["libraries"])
        if "purpose" in pattern_data:
            # Extract key words from purpose
            words = pattern_data["purpose"].lower().split()
            important_words = [w for w in words if len(w) > 4][:3]
            tags.extend(important_words)

        return list(set(tags))[:10]  # Limit to 10 unique tags
