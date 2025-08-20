"""
Main client for Codex operations.

Integrates pattern database, Farm SDK agents, and CookieCutter templates.
"""

from pathlib import Path
from typing import Any

from cookiecutter.main import cookiecutter
from farm_sdk import FarmClient, TrainingExample

from .database import Database
from .exceptions import AnalysisError, FarmAgentError, TemplateError
from .models import (
    AnalysisResult,
    CodeContext,
    PatternCategory,
    PatternMatch,
)


class CodexClient:
    """Main client for Codex operations."""

    def __init__(
        self,
        db_path: str | None = None,
        farm_url: str = "http://localhost:8001",
    ):
        """Initialize Codex client."""
        self.db = Database(Path(db_path) if db_path else None)
        self.farm_url = farm_url
        self.farm_client: FarmClient | None = None
        self.trained_agents: dict[str, str] = {}

    async def test_farm_connection(self) -> bool:
        """Test Farm SDK connection."""
        try:
            self.farm_client = FarmClient(self.farm_url)
            return self.farm_client.health_check()
        except Exception:
            return False

    async def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a file for pattern violations and best practices."""
        path = Path(file_path)
        if not path.exists():
            raise AnalysisError(file_path, "File not found")

        try:
            with open(path) as f:
                content = f.read()

            context = CodeContext(
                project_root=str(path.parent),
                file_path=file_path,
                content=content,
                language=self._detect_language(path),
            )

            # Get all patterns from database
            patterns = self.db.get_all_patterns()

            # Initialize result
            result = AnalysisResult(
                file_path=file_path,
                matches=[],
                applied_patterns=[],
                missing_patterns=[],
                violations=[],
                score=1.0,
                suggestions=[],
            )

            # Check each pattern
            for pattern in patterns:
                match = await self._check_pattern(pattern, context)
                if match:
                    if match.confidence > 0.7:
                        result.applied_patterns.append(pattern.name)
                    else:
                        result.violations.append(match)
                        # Map priority to numeric value
                        priority_scores = {
                            "MANDATORY": 10,
                            "CRITICAL": 8,
                            "HIGH": 6,
                            "MEDIUM": 4,
                            "LOW": 2,
                            "OPTIONAL": 1,
                        }
                        priority_value = priority_scores.get(match.priority.value, 4)
                        result.score *= 1 - priority_value / 10
                elif pattern.priority in ["MANDATORY", "CRITICAL"]:
                    result.missing_patterns.append(pattern.name)
                    result.score *= 0.9

            # Use Farm agent if available
            if self.farm_client and context.language == "python":
                farm_results = await self._analyze_with_farm(context)
                result.matches.extend(farm_results)

            return result

        except Exception as e:
            raise AnalysisError(file_path, str(e)) from e

    async def _check_pattern(self, pattern: Any, context: CodeContext) -> PatternMatch | None:
        """Check if a pattern is present in the code."""
        # Simple detection based on rules
        if pattern.detection_rules:
            # Check for required imports
            if "imports" in pattern.detection_rules:
                for import_name in pattern.detection_rules["imports"]:
                    if import_name in context.content:
                        return PatternMatch(
                            pattern_id=pattern.id,
                            pattern_name=pattern.name,
                            category=pattern.category,
                            priority=pattern.priority,
                            file_path=context.file_path,
                            matched_code=import_name,
                            confidence=0.9,
                        )

            # Check for forbidden patterns
            if "forbidden" in pattern.detection_rules:
                for forbidden in pattern.detection_rules["forbidden"]:
                    if forbidden in context.content:
                        return PatternMatch(
                            pattern_id=pattern.id,
                            pattern_name=pattern.name,
                            category=pattern.category,
                            priority=pattern.priority,
                            file_path=context.file_path,
                            matched_code=forbidden,
                            confidence=0.8,
                            suggestion=f"Remove {forbidden} - {pattern.description}",
                            auto_fixable=bool(pattern.fix_template),
                            fix_code=pattern.fix_template,
                        )

        return None

    async def _analyze_with_farm(self, context: CodeContext) -> list[PatternMatch]:
        """Analyze code using Farm SDK agents."""
        matches = []

        # Use trained agents for pattern detection
        for agent_name in self.trained_agents.values():
            try:
                result = self.farm_client.run_agent(  # type: ignore[union-attr]
                    agent_name,
                    {"code": context.content, "file_path": context.file_path},
                )

                if result.output.get("violations"):
                    for violation in result.output["violations"]:
                        matches.append(
                            PatternMatch(
                                pattern_id=0,
                                pattern_name=violation.get("pattern", "unknown"),
                                category=PatternCategory.QUALITY_TOOLS,
                                priority="HIGH",  # type: ignore[arg-type]
                                file_path=context.file_path,
                                line_number=violation.get("line"),
                                matched_code=violation.get("code", ""),
                                confidence=violation.get("confidence", 0.5),
                                suggestion=violation.get("suggestion"),
                            )
                        )
            except Exception:
                # Continue if agent fails
                pass

        return matches

    async def apply_fixes(self, file_path: str, violations: list[PatternMatch]) -> int:
        """Apply automatic fixes for violations."""
        fixed_count = 0
        path = Path(file_path)

        if not path.exists():
            return 0

        with open(path) as f:
            content = f.read()

        for violation in violations:
            if violation.auto_fixable and violation.fix_code:
                # Simple replacement
                if violation.matched_code in content:
                    content = content.replace(violation.matched_code, violation.fix_code)
                    fixed_count += 1

        if fixed_count > 0:
            with open(path, "w") as f:
                f.write(content)

        return fixed_count

    async def train_pattern_agent(self, name: str, category: PatternCategory) -> str:
        """Train a Farm agent for pattern detection."""
        if not self.farm_client:
            self.farm_client = FarmClient(self.farm_url)

        # Get patterns from category
        patterns = self.db.get_patterns_by_category(category)

        if not patterns:
            raise FarmAgentError(name, f"No patterns found for category {category}")

        # Create training examples
        training_examples = []
        for pattern in patterns:
            # Create positive example
            if pattern.pattern_code:
                training_examples.append(
                    TrainingExample(
                        input={"code": pattern.pattern_code},
                        output={
                            "has_pattern": True,
                            "pattern_name": pattern.name,
                            "confidence": 1.0,
                        },
                    )
                )

            # Create negative example
            if pattern.anti_pattern:
                training_examples.append(
                    TrainingExample(
                        input={"code": pattern.anti_pattern},
                        output={
                            "has_pattern": False,
                            "violations": [
                                {
                                    "pattern": pattern.name,
                                    "code": pattern.anti_pattern,
                                    "suggestion": pattern.description,
                                    "confidence": 0.9,
                                }
                            ],
                        },
                    )
                )

        # Train agent
        try:
            agent_name = self.farm_client.quick_train(
                examples=training_examples,
                requirements=f"Detect {category} patterns in code",
            )
            self.trained_agents[category] = agent_name
            return agent_name
        except Exception as e:
            raise FarmAgentError(name, str(e)) from e

    async def generate_from_template(self, template: str, output_dir: str, context: dict[str, Any]) -> str:
        """Generate project from CookieCutter template."""
        try:
            # Add Codex patterns to context
            patterns = self.db.get_all_patterns()
            context["codex_patterns"] = [p.name for p in patterns[:10]]

            project_path = cookiecutter(
                template,
                output_dir=output_dir,
                extra_context=context,
                no_input=True,
            )

            return project_path
        except Exception as e:
            raise TemplateError(template, str(e)) from e

    def _detect_language(self, path: Path) -> str | None:
        """Detect programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
        }
        return extension_map.get(path.suffix, None)

    async def close(self) -> None:
        """Close connections."""
        self.db.close()
