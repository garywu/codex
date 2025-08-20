"""
Extract patterns from project-init.json files for FTS database.
"""

import json
from typing import Any

from .pattern_models import Pattern


class PatternExtractor:
    """Extract patterns from various sources."""

    def extract_from_project_init(self, file_path: str) -> list[Pattern]:
        """Extract patterns from project-init.json structure."""
        patterns = []

        with open(file_path) as f:
            data = json.load(f)

        # Handle main project-init.json format
        if "project_initialization_template" in data:
            patterns.extend(self._extract_from_main_format(data, file_path))

        # Handle updated project-init.json format
        elif "project_initialization" in data:
            patterns.extend(self._extract_from_updated_format(data, file_path))

        return patterns

    def _extract_from_main_format(self, data: dict[str, Any], file_path: str) -> list[Pattern]:
        """Extract from main project-init.json format."""
        patterns = []
        tech_stack = data.get("project_initialization_template", {}).get("tech_stack", {})

        # Package management patterns
        if "package_management" in tech_stack:
            uv_data = tech_stack["package_management"].get("uv", {})
            if uv_data:
                patterns.append(
                    FTSPattern(
                        name="use-uv-not-pip",
                        category="package_management",
                        priority=uv_data.get("priority", "MANDATORY"),
                        description=uv_data.get("purpose", ""),
                        detection_pattern="pip install|poetry add|conda install|pipenv install",
                        fix_template="uv add {package}",
                        rationale=f"UV replaces {', '.join(uv_data.get('replaces', []))}. {uv_data.get('purpose', '')}",
                        example_good="uv add httpx\nuv sync\nuv run pytest",
                        example_bad="pip install httpx\npoetry add httpx\nconda install httpx",
                        replaces=json.dumps(uv_data.get("replaces", [])),
                        source_file=file_path,
                        full_context=json.dumps(uv_data),
                    )
                )

        # Core libraries patterns
        for lib in tech_stack.get("core_libraries", []):
            lib_name = lib["name"]

            # Main library pattern
            patterns.append(
                FTSPattern(
                    name=f"use-{lib_name}",
                    category="core_libraries",
                    priority=lib.get("priority", "HIGH"),
                    description=lib.get("purpose", ""),
                    detection_pattern=lib.get("replaces", ""),
                    fix_template=f"uv add {lib_name}",
                    rationale=lib.get("purpose", ""),
                    example_good=json.dumps(lib.get("best_practices", [])[:3]),
                    example_bad="",
                    replaces=lib.get("replaces", ""),
                    source_file=file_path,
                    full_context=json.dumps(lib),
                )
            )

            # Best practices as separate patterns
            for i, practice in enumerate(lib.get("best_practices", [])):
                patterns.append(
                    FTSPattern(
                        name=f"{lib_name}-practice-{i}",
                        category=f"{lib_name}_best_practices",
                        priority="RECOMMENDED",
                        description=practice,
                        detection_pattern="",
                        fix_template="",
                        rationale=practice,
                        example_good="",
                        example_bad="",
                        replaces="",
                        source_file=file_path,
                        full_context=practice,
                    )
                )

            # Special handling for Pydantic patterns
            if lib_name == "pydantic":
                when_to_use = lib.get("when_to_use", {})

                for use_case, scenarios in when_to_use.items():
                    if isinstance(scenarios, list):
                        for scenario in scenarios:
                            patterns.append(
                                FTSPattern(
                                    name=f"pydantic-{use_case}-{len(patterns)}",
                                    category="pydantic_usage",
                                    priority="HIGH",
                                    description=f"Use {use_case}: {scenario}",
                                    detection_pattern="",
                                    fix_template="",
                                    rationale=f"Pydantic {use_case} appropriate for: {scenario}",
                                    example_good="",
                                    example_bad="",
                                    replaces="",
                                    source_file=file_path,
                                    full_context=scenario,
                                )
                            )

        # Quality tools patterns
        for tool in tech_stack.get("quality_tools", []):
            tool_name = tool["name"]

            # Main tool pattern
            patterns.append(
                FTSPattern(
                    name=f"use-{tool_name}",
                    category="quality_tools",
                    priority=tool.get("priority", "HIGH"),
                    description=tool.get("purpose", ""),
                    detection_pattern="|".join(tool.get("replaces", [])),
                    fix_template=f"uv add --dev {tool_name}",
                    rationale=f"{tool_name} replaces {', '.join(tool.get('replaces', []))}",
                    example_good=json.dumps(tool.get("commands", {})),
                    example_bad="",
                    replaces=json.dumps(tool.get("replaces", [])),
                    source_file=file_path,
                    full_context=json.dumps(tool),
                )
            )

            # Ruff error patterns
            if tool_name == "ruff":
                for error_code, details in tool.get("critical_error_patterns", {}).items():
                    patterns.append(
                        FTSPattern(
                            name=f"ruff-{error_code}",
                            category="ruff_errors",
                            priority="HIGH",
                            description=details.get("error", ""),
                            detection_pattern=details.get("pattern", ""),
                            fix_template=details.get("fix", ""),
                            rationale=details.get("explanation", ""),
                            example_good=details.get("fix", ""),
                            example_bad=details.get("pattern", ""),
                            replaces="",
                            source_file=file_path,
                            full_context=json.dumps(details),
                        )
                    )

                # Exception handling patterns
                for pattern_name, pattern_data in tool.get("exception_handling_patterns", {}).items():
                    patterns.append(
                        FTSPattern(
                            name=f"exception-{pattern_name}",
                            category="exception_handling",
                            priority="HIGH",
                            description=pattern_data.get("reason", ""),
                            detection_pattern=pattern_data.get("incorrect", ""),
                            fix_template=pattern_data.get("correct", ""),
                            rationale=pattern_data.get("reason", ""),
                            example_good=pattern_data.get("correct", ""),
                            example_bad=pattern_data.get("incorrect", ""),
                            replaces="",
                            source_file=file_path,
                            full_context=json.dumps(pattern_data),
                        )
                    )

        return patterns

    def _extract_from_updated_format(self, data: dict[str, Any], file_path: str) -> list[Pattern]:
        """Extract from updated project-init.json format."""
        patterns = []
        init_data = data.get("project_initialization", {})

        # Core dependencies
        core_deps = init_data.get("tech_stack_2024", {}).get("core_dependencies", {})
        for dep_name, version in core_deps.items():
            patterns.append(
                FTSPattern(
                    name=f"use-{dep_name.replace('_', '-')}",
                    category="core_dependencies_2024",
                    priority="MANDATORY",
                    description=f"Use {dep_name} version {version}",
                    detection_pattern="",
                    fix_template=f"uv add {dep_name.replace('_', '-')}",
                    rationale="Required dependency for 2024 stack",
                    example_good="",
                    example_bad="",
                    replaces="",
                    source_file=file_path,
                    full_context=f"{dep_name}: {version}",
                )
            )

        # Dependency injection patterns
        mandatory_reqs = init_data.get("mandatory_requirements", {})
        if "dependency_injection" in mandatory_reqs:
            di_data = mandatory_reqs["dependency_injection"]

            for pattern in di_data.get("patterns", []):
                patterns.append(
                    FTSPattern(
                        name=f"di-pattern-{len(patterns)}",
                        category="dependency_injection",
                        priority="MANDATORY",
                        description=pattern,
                        detection_pattern="",
                        fix_template="",
                        rationale="Required for testability and clean architecture",
                        example_good="",
                        example_bad="",
                        replaces="",
                        source_file=file_path,
                        full_context=pattern,
                    )
                )

        # Architecture layer patterns
        if "architecture_layers" in mandatory_reqs:
            for layer_name, layer_data in mandatory_reqs["architecture_layers"].items():
                # Layer constraints
                for constraint in layer_data.get("constraints", []):
                    patterns.append(
                        FTSPattern(
                            name=f"{layer_name}-constraint-{len(patterns)}",
                            category=f"architecture_{layer_name}",
                            priority="MANDATORY",
                            description=constraint,
                            detection_pattern="",
                            fix_template="",
                            rationale=layer_data.get("description", ""),
                            example_good="",
                            example_bad="",
                            replaces="",
                            source_file=file_path,
                            full_context=json.dumps(layer_data),
                        )
                    )

                # Layer patterns
                for pattern in layer_data.get("patterns", []):
                    patterns.append(
                        FTSPattern(
                            name=f"{layer_name}-pattern-{len(patterns)}",
                            category=f"architecture_{layer_name}",
                            priority="MANDATORY",
                            description=pattern,
                            detection_pattern="",
                            fix_template="",
                            rationale=layer_data.get("description", ""),
                            example_good="",
                            example_bad="",
                            replaces="",
                            source_file=file_path,
                            full_context=pattern,
                        )
                    )

        return patterns
