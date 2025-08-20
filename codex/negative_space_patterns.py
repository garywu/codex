"""
Negative Space Pattern Detection - Core Implementation

This module codifies the negative space methodology for identifying best practices
by analyzing what problems clean projects avoid and the structural patterns that
protect against common violations.

Philosophy:
- Best practices are often invisible (what's NOT there)
- Learn from projects that avoid common problems  
- Identify protective patterns that prevent issues
- Reverse-engineer excellence from absence of problems

Integration with Codex:
- Part of core pattern detection system
- Feeds into unified database
- Used by scanner and intelligent analysis
- Provides evidence-based recommendations
"""

from typing import Dict, List, Any, Set, Optional
from pathlib import Path
from collections import defaultdict, Counter
import json
from dataclasses import dataclass
from datetime import datetime

from .settings import settings


@dataclass
class NegativeSpacePattern:
    """A pattern identified through negative space analysis."""
    name: str
    description: str
    category: str
    protective_structures: List[str]
    problems_prevented: List[str]
    evidence_strength: int
    avoidance_rate: float
    implementation_guide: str
    examples: Dict[str, List[str]]  # clean vs problematic projects


@dataclass
class ProjectAnalysis:
    """Analysis of a single project's structure and violations."""
    name: str
    violations_by_pattern: Dict[str, int]
    structural_features: Dict[str, Any]
    files_count: int
    package_depth: int
    has_tests: bool
    has_core_package: bool
    has_api_separation: bool
    organization_score: float


class NegativeSpaceDetector:
    """
    Core implementation of negative space pattern detection.
    
    This class implements the methodology for identifying best practices
    by comparing projects that avoid problems with those that have them.
    """
    
    def __init__(self):
        self.known_patterns = self._load_known_negative_space_patterns()
        self.project_analyses = {}
        
    def _load_known_negative_space_patterns(self) -> List[NegativeSpacePattern]:
        """Load previously identified negative space patterns."""
        patterns_file = settings.data_dir / 'negative_space_patterns.json'
        
        if not patterns_file.exists():
            return self._initialize_base_patterns()
        
        try:
            with open(patterns_file, 'r') as f:
                data = json.load(f)
                return [NegativeSpacePattern(**pattern) for pattern in data]
        except (json.JSONDecodeError, TypeError):
            return self._initialize_base_patterns()
    
    def _initialize_base_patterns(self) -> List[NegativeSpacePattern]:
        """Initialize base set of negative space patterns."""
        return [
            NegativeSpacePattern(
                name="core_package_separation",
                description="Projects with core/ packages avoid business logic in CLI",
                category="architecture",
                protective_structures=["core/", "api/", "cli/"],
                problems_prevented=["core_business_logic_separation", "cli_as_thin_layer"],
                evidence_strength=0,
                avoidance_rate=0.0,
                implementation_guide="Create core/ package for business logic, separate from CLI and API layers",
                examples={"clean": [], "problematic": []}
            ),
            NegativeSpacePattern(
                name="settings_consolidation_pattern",
                description="Projects with unified settings avoid configuration chaos",
                category="configuration",
                protective_structures=["settings.py", "BaseSettings", "pydantic"],
                problems_prevented=["settings_consolidation", "hardcoded_secrets"],
                evidence_strength=0,
                avoidance_rate=0.0,
                implementation_guide="Use single Pydantic BaseSettings class with environment variable integration",
                examples={"clean": [], "problematic": []}
            ),
            NegativeSpacePattern(
                name="package_depth_optimization",
                description="Projects with optimal package depth avoid complexity issues",
                category="organization",
                protective_structures=["moderate_nesting", "clear_hierarchy"],
                problems_prevented=["redundant_package_naming", "package_based_architecture"],
                evidence_strength=0,
                avoidance_rate=0.0,
                implementation_guide="Maintain 2-4 levels of package nesting for clarity without over-complexity",
                examples={"clean": [], "problematic": []}
            ),
            NegativeSpacePattern(
                name="comprehensive_testing_pattern",
                description="Projects with proper test structure avoid quality issues",
                category="quality",
                protective_structures=["tests/", "test_*.py", "pytest.ini"],
                problems_prevented=["mock_naming_compliance", "pre_commit_skip_usage"],
                evidence_strength=0,
                avoidance_rate=0.0,
                implementation_guide="Maintain tests/ directory with proper naming and pytest configuration",
                examples={"clean": [], "problematic": []}
            )
        ]
    
    def analyze_project_negative_space(self, project_path: Path, violation_data: Dict[str, Any]) -> ProjectAnalysis:
        """Analyze a single project for negative space patterns."""
        structural_features = self._extract_structural_features(project_path)
        
        # Count violations by pattern
        violations_by_pattern = {}
        for fix_plan in violation_data.get('fix_plans', []):
            violation = fix_plan.get('violation', {})
            pattern = violation.get('pattern', 'unknown')
            violations_by_pattern[pattern] = violations_by_pattern.get(pattern, 0) + 1
        
        # Calculate organization score
        organization_score = self._calculate_organization_score(structural_features)
        
        analysis = ProjectAnalysis(
            name=project_path.name,
            violations_by_pattern=violations_by_pattern,
            structural_features=structural_features,
            files_count=len(list(project_path.rglob('*.py'))),
            package_depth=structural_features.get('package_depth', 0),
            has_tests=structural_features.get('has_tests', False),
            has_core_package=structural_features.get('has_core_package', False),
            has_api_separation=structural_features.get('has_api_separation', False),
            organization_score=organization_score
        )
        
        self.project_analyses[project_path.name] = analysis
        return analysis
    
    def _extract_structural_features(self, project_path: Path) -> Dict[str, Any]:
        """Extract structural features that might be protective."""
        features = {}
        
        # Package structure
        features['has_core_package'] = (project_path / 'core').is_dir()
        features['has_api_package'] = (project_path / 'api').is_dir()
        features['has_cli_package'] = (project_path / 'cli').is_dir()
        features['has_models_package'] = (project_path / 'models').is_dir()
        features['has_services_package'] = (project_path / 'services').is_dir()
        
        # Testing structure
        features['has_tests'] = (project_path / 'tests').is_dir() or bool(list(project_path.rglob('test_*.py')))
        features['has_pytest_config'] = (project_path / 'pytest.ini').exists() or (project_path / 'pyproject.toml').exists()
        
        # Configuration structure
        features['has_settings_file'] = bool(list(project_path.rglob('*settings*.py')))
        features['has_config_file'] = bool(list(project_path.rglob('*config*.py')))
        features['has_pyproject'] = (project_path / 'pyproject.toml').exists()
        
        # Package organization
        init_files = list(project_path.rglob('__init__.py'))
        features['init_files_count'] = len(init_files)
        features['package_depth'] = max((len(f.relative_to(project_path).parts) - 1 for f in init_files), default=0)
        
        # File organization patterns
        py_files = list(project_path.rglob('*.py'))
        features['total_py_files'] = len(py_files)
        
        # Check for monolithic patterns
        large_files = []
        for py_file in py_files:
            try:
                if py_file.stat().st_size > 15000:  # > 15KB
                    large_files.append(str(py_file.relative_to(project_path)))
            except OSError:
                continue
        features['large_files'] = large_files
        features['has_monolithic_files'] = len(large_files) > 0
        
        # Import patterns (sample a few files)
        sample_files = py_files[:5]
        features['uses_relative_imports'] = self._check_relative_imports(sample_files)
        features['uses_absolute_imports'] = self._check_absolute_imports(sample_files, project_path.name)
        
        return features
    
    def _check_relative_imports(self, files: List[Path]) -> bool:
        """Check if project uses relative imports."""
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'from .' in content or 'from ..' in content:
                        return True
            except (OSError, UnicodeDecodeError):
                continue
        return False
    
    def _check_absolute_imports(self, files: List[Path], project_name: str) -> bool:
        """Check if project uses absolute imports."""
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if f'from {project_name}.' in content or f'import {project_name}.' in content:
                        return True
            except (OSError, UnicodeDecodeError):
                continue
        return False
    
    def _calculate_organization_score(self, features: Dict[str, Any]) -> float:
        """Calculate a score for how well-organized the project is."""
        score = 0.0
        max_score = 0.0
        
        # Package separation (0.3 weight)
        if features.get('has_core_package'):
            score += 0.1
        if features.get('has_api_package'):
            score += 0.1
        if features.get('has_cli_package'):
            score += 0.1
        max_score += 0.3
        
        # Testing (0.2 weight)
        if features.get('has_tests'):
            score += 0.15
        if features.get('has_pytest_config'):
            score += 0.05
        max_score += 0.2
        
        # Configuration (0.2 weight)
        if features.get('has_settings_file'):
            score += 0.1
        if features.get('has_pyproject'):
            score += 0.1
        max_score += 0.2
        
        # Package organization (0.2 weight)
        package_depth = features.get('package_depth', 0)
        if 2 <= package_depth <= 4:  # Optimal depth
            score += 0.1
        if features.get('init_files_count', 0) > 0:
            score += 0.1
        max_score += 0.2
        
        # File organization (0.1 weight)
        if not features.get('has_monolithic_files'):
            score += 0.05
        if features.get('uses_relative_imports'):
            score += 0.05
        max_score += 0.1
        
        return score / max_score if max_score > 0 else 0.0
    
    def identify_negative_space_patterns(self, all_analyses: Dict[str, ProjectAnalysis]) -> List[NegativeSpacePattern]:
        """Identify negative space patterns from multiple project analyses."""
        # Get all violation patterns
        all_violation_patterns = set()
        for analysis in all_analyses.values():
            all_violation_patterns.update(analysis.violations_by_pattern.keys())
        
        discovered_patterns = []
        
        for violation_pattern in all_violation_patterns:
            # Split projects into clean vs problematic
            clean_projects = []
            problematic_projects = []
            
            for analysis in all_analyses.values():
                if violation_pattern in analysis.violations_by_pattern:
                    problematic_projects.append(analysis)
                else:
                    clean_projects.append(analysis)
            
            # Only analyze if we have both clean and problematic projects
            if len(clean_projects) >= 1 and len(problematic_projects) >= 1:
                pattern = self._extract_protective_pattern(
                    violation_pattern, clean_projects, problematic_projects
                )
                if pattern:
                    discovered_patterns.append(pattern)
        
        return discovered_patterns
    
    def _extract_protective_pattern(self, violation_pattern: str, 
                                  clean_projects: List[ProjectAnalysis],
                                  problematic_projects: List[ProjectAnalysis]) -> Optional[NegativeSpacePattern]:
        """Extract protective pattern from clean vs problematic project comparison."""
        
        protective_structures = []
        
        # Find structural differences that correlate with cleanliness
        for feature in ['has_core_package', 'has_api_package', 'has_cli_package', 
                       'has_tests', 'has_settings_file', 'has_pyproject']:
            
            clean_rate = sum(1 for p in clean_projects 
                           if p.structural_features.get(feature, False)) / len(clean_projects)
            problem_rate = sum(1 for p in problematic_projects 
                             if p.structural_features.get(feature, False)) / len(problematic_projects)
            
            # If clean projects have this feature significantly more often
            if clean_rate - problem_rate > 0.4:  # 40% difference threshold
                protective_structures.append(feature)
        
        # Check organization scores
        clean_org_scores = [p.organization_score for p in clean_projects]
        problem_org_scores = [p.organization_score for p in problematic_projects]
        
        clean_avg = sum(clean_org_scores) / len(clean_org_scores)
        problem_avg = sum(problem_org_scores) / len(problem_org_scores)
        
        if clean_avg - problem_avg > 0.2:  # 20% organization score difference
            protective_structures.append("high_organization_score")
        
        # Only create pattern if we found protective structures
        if not protective_structures:
            return None
        
        avoidance_rate = len(clean_projects) / (len(clean_projects) + len(problematic_projects))
        
        return NegativeSpacePattern(
            name=f"avoid_{violation_pattern}",
            description=f"Structural patterns that prevent {violation_pattern} violations",
            category="negative_space_derived",
            protective_structures=protective_structures,
            problems_prevented=[violation_pattern],
            evidence_strength=len(clean_projects) + len(problematic_projects),
            avoidance_rate=avoidance_rate,
            implementation_guide=self._generate_implementation_guide(protective_structures),
            examples={
                "clean": [p.name for p in clean_projects],
                "problematic": [p.name for p in problematic_projects]
            }
        )
    
    def _generate_implementation_guide(self, protective_structures: List[str]) -> str:
        """Generate implementation guide from protective structures."""
        guides = []
        
        for structure in protective_structures:
            if structure == "has_core_package":
                guides.append("Create core/ package for business logic")
            elif structure == "has_api_package":
                guides.append("Separate API layer in api/ package")
            elif structure == "has_cli_package":
                guides.append("Organize CLI as package in cli/ directory")
            elif structure == "has_tests":
                guides.append("Maintain comprehensive test suite in tests/")
            elif structure == "has_settings_file":
                guides.append("Use dedicated settings module for configuration")
            elif structure == "has_pyproject":
                guides.append("Use pyproject.toml for project configuration")
            elif structure == "high_organization_score":
                guides.append("Maintain high overall project organization")
        
        return "; ".join(guides)
    
    def save_patterns(self, patterns: List[NegativeSpacePattern]) -> None:
        """Save discovered patterns to persistent storage."""
        patterns_file = settings.data_dir / 'negative_space_patterns.json'
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        patterns_data = []
        for pattern in patterns:
            patterns_data.append({
                'name': pattern.name,
                'description': pattern.description,
                'category': pattern.category,
                'protective_structures': pattern.protective_structures,
                'problems_prevented': pattern.problems_prevented,
                'evidence_strength': pattern.evidence_strength,
                'avoidance_rate': pattern.avoidance_rate,
                'implementation_guide': pattern.implementation_guide,
                'examples': pattern.examples
            })
        
        with open(patterns_file, 'w') as f:
            json.dump(patterns_data, f, indent=2)
    
    def generate_best_practices_report(self, patterns: List[NegativeSpacePattern]) -> str:
        """Generate comprehensive best practices report."""
        timestamp = datetime.now().isoformat()
        
        # Sort patterns by evidence strength
        patterns.sort(key=lambda x: x.evidence_strength, reverse=True)
        
        report = f"""
NEGATIVE SPACE BEST PRACTICES REPORT
Generated: {timestamp}

METHODOLOGY:
Evidence-based best practices identified by analyzing structural patterns
that correlate with avoiding common code quality violations.

DISCOVERED PATTERNS ({len(patterns)} total):
"""
        
        for i, pattern in enumerate(patterns, 1):
            report += f"""
{i}. {pattern.name.upper()}
   Description: {pattern.description}
   Evidence Strength: {pattern.evidence_strength} projects analyzed
   Avoidance Rate: {pattern.avoidance_rate:.1%}
   
   Protective Structures:
   {chr(10).join(f'   • {structure}' for structure in pattern.protective_structures)}
   
   Prevents: {', '.join(pattern.problems_prevented)}
   
   Implementation: {pattern.implementation_guide}
   
   Examples:
   ✅ Clean projects: {', '.join(pattern.examples['clean'])}
   ❌ Problematic projects: {', '.join(pattern.examples['problematic'])}
"""
        
        report += f"""
INTEGRATION GUIDANCE:
• Incorporate these patterns into code review checklists
• Use as architectural decision guidelines for new projects
• Implement as automated checks in CI/CD pipelines
• Train development teams on evidence-based best practices

VALIDATION:
• All patterns backed by comparative analysis across multiple projects
• Evidence strength indicates statistical confidence
• Avoidance rates show effectiveness in real codebases
"""
        
        return report


def integrate_negative_space_with_scanner():
    """Integration point for main scanner system."""
    detector = NegativeSpaceDetector()
    
    # This function would be called by the main scanner
    # to incorporate negative space patterns into violation detection
    
    return detector.known_patterns