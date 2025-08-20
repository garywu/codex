#!/usr/bin/env python3
"""
Technology and Architecture Recommendation Engine

Analyzes project-level patterns and suggests appropriate technologies
based on actual code context, not just missing imports.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@dataclass
class TechRecommendation:
    """A technology recommendation with justification."""
    
    technology: str
    reason: str
    evidence: List[str]
    priority: str  # HIGH, MEDIUM, LOW
    implementation_effort: str  # 15min, 30min, 1hr, etc.
    current_pattern: str
    suggested_pattern: str


class ProjectArchitectureAnalyzer:
    """Analyzes project-level architecture and dependencies."""
    
    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        self.console = Console() if not quiet else None
        
    def analyze_project(self, project_path: Path) -> List[TechRecommendation]:
        """Analyze entire project and generate recommendations."""
        
        recommendations = []
        
        # Collect project data
        python_files = list(project_path.rglob("*.py"))
        if not python_files:
            return recommendations
            
        project_context = self._build_project_context(python_files)
        
        # Analyze for specific technology opportunities
        recommendations.extend(self._analyze_pydantic_settings_opportunity(project_context))
        recommendations.extend(self._analyze_pydantic_models_opportunity(project_context))
        recommendations.extend(self._analyze_logfire_opportunity(project_context))
        
        return recommendations
    
    def _build_project_context(self, python_files: List[Path]) -> Dict[str, Any]:
        """Build comprehensive project context."""
        
        context = {
            'total_files': len(python_files),
            'imports': set(),
            'has_config_management': False,
            'has_data_validation': False,
            'has_api_endpoints': False,
            'has_logging': False,
            'has_env_vars': False,
            'config_patterns': [],
            'validation_patterns': [],
            'logging_patterns': [],
            'architecture_patterns': set()
        }
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                context = self._analyze_file_context(content, context)
            except (UnicodeDecodeError, PermissionError):
                continue
                
        return context
    
    def _analyze_file_context(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual file and update project context."""
        
        # Extract imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        context['imports'].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        context['imports'].add(node.module)
        except SyntaxError:
            pass
        
        # Detect configuration management patterns
        if re.search(r'os\.environ\.get\(["\'][^"\']+["\']', content):
            context['has_env_vars'] = True
            env_matches = re.findall(r'os\.environ\.get\(["\']([^"\']+)["\']', content)
            context['config_patterns'].extend(env_matches)
            
        # Detect data validation patterns  
        if re.search(r'def \w+\([^)]*data: dict', content):
            context['has_data_validation'] = True
            context['validation_patterns'].append('dict_parameters')
            
        if re.search(r'isinstance\([^,]+,\s*(str|int|float|bool|list|dict)', content):
            context['has_data_validation'] = True
            context['validation_patterns'].append('manual_type_checking')
            
        # Detect API patterns
        if any(framework in content for framework in ['fastapi', 'flask', 'django']):
            context['has_api_endpoints'] = True
            
        # Detect logging patterns
        if re.search(r'(logging\.|logger\.|print\()', content):
            context['has_logging'] = True
            
        if re.search(r'logging\.(info|debug|warning|error)', content):
            context['logging_patterns'].append('basic_logging')
            
        if re.search(r'print\(f["\'][^"\']*\{[^}]+\}', content):
            context['logging_patterns'].append('formatted_print_statements')
            
        # Detect architecture patterns
        if '@' in content and 'def ' in content:
            context['architecture_patterns'].add('decorators')
            
        if re.search(r'yield\s+', content):
            context['architecture_patterns'].add('generators')
            
        if re.search(r'async\s+def', content):
            context['architecture_patterns'].add('async_patterns')
            
        return context
    
    def _analyze_pydantic_settings_opportunity(self, context: Dict[str, Any]) -> List[TechRecommendation]:
        """Analyze if project should adopt Pydantic Settings."""
        
        recommendations = []
        
        # Check if already using Pydantic Settings
        if 'pydantic_settings' in context['imports'] or 'pydantic.settings' in context['imports']:
            return recommendations
            
        # Check for configuration management opportunity
        env_var_count = len(set(context['config_patterns']))
        has_manual_config = context['has_env_vars'] and env_var_count >= 3
        
        if has_manual_config:
            recommendations.append(TechRecommendation(
                technology="Pydantic Settings",
                reason="Multiple environment variables managed manually",
                evidence=[
                    f"Found {env_var_count} environment variables",
                    "Manual os.environ.get() calls detected",
                    "No centralized configuration management"
                ],
                priority="HIGH",
                implementation_effort="20-30 minutes",
                current_pattern="Manual environment variable access with os.environ.get()",
                suggested_pattern="Centralized BaseSettings class with type validation"
            ))
            
        return recommendations
    
    def _analyze_pydantic_models_opportunity(self, context: Dict[str, Any]) -> List[TechRecommendation]:
        """Analyze if project should adopt Pydantic Models."""
        
        recommendations = []
        
        # Check if already using Pydantic
        if 'pydantic' in context['imports']:
            return recommendations
            
        # Check for data validation opportunity
        has_manual_validation = (
            context['has_data_validation'] and 
            ('manual_type_checking' in context['validation_patterns'] or
             'dict_parameters' in context['validation_patterns'])
        )
        
        if has_manual_validation and context['has_api_endpoints']:
            recommendations.append(TechRecommendation(
                technology="Pydantic Models",
                reason="Manual data validation in API endpoints",
                evidence=[
                    "Dict parameters in function signatures",
                    "Manual isinstance() type checking",
                    "API framework detected"
                ],
                priority="HIGH", 
                implementation_effort="30-45 minutes",
                current_pattern="Manual validation with isinstance() and dict parameters",
                suggested_pattern="Type-safe Pydantic BaseModel classes with automatic validation"
            ))
        elif has_manual_validation:
            recommendations.append(TechRecommendation(
                technology="Pydantic Models",
                reason="Manual data validation detected",
                evidence=[
                    "Manual type checking patterns found",
                    "Dict-based data handling"
                ],
                priority="MEDIUM",
                implementation_effort="20-30 minutes", 
                current_pattern="Manual data validation",
                suggested_pattern="Pydantic BaseModel for type safety"
            ))
            
        return recommendations
    
    def _analyze_logfire_opportunity(self, context: Dict[str, Any]) -> List[TechRecommendation]:
        """Analyze if project should adopt Logfire."""
        
        recommendations = []
        
        # Check if already using Logfire
        if 'logfire' in context['imports']:
            return recommendations
            
        # Check for observability opportunity
        has_structured_logging_need = (
            context['has_logging'] and 
            ('formatted_print_statements' in context['logging_patterns'] or
             'basic_logging' in context['logging_patterns'])
        )
        
        if has_structured_logging_need:
            priority = "HIGH" if context['has_api_endpoints'] else "MEDIUM"
            
            recommendations.append(TechRecommendation(
                technology="Logfire",
                reason="Structured logging and observability opportunity",
                evidence=[
                    "Basic logging detected",
                    "Formatted print statements found",
                    "API endpoints detected" if context['has_api_endpoints'] else "Debugging patterns found"
                ],
                priority=priority,
                implementation_effort="15-25 minutes",
                current_pattern="Basic logging and print statements",
                suggested_pattern="Structured observability with Logfire"
            ))
            
        return recommendations
    
    def print_recommendations(self, recommendations: List[TechRecommendation]) -> None:
        """Print recommendations in a user-friendly format."""
        
        if not recommendations:
            if not self.quiet:
                self.console.print("✅ No technology recommendations - project uses appropriate tools")
            return
            
        if not self.quiet:
            self.console.print("\n")
            self.console.print(Panel.fit(
                "🚀 Technology Recommendations", 
                style="bold blue"
            ))
            
            for rec in sorted(recommendations, key=lambda x: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}[x.priority], reverse=True):
                self._print_single_recommendation(rec)
    
    def _print_single_recommendation(self, rec: TechRecommendation) -> None:
        """Print a single recommendation."""
        
        priority_color = {
            "HIGH": "red",
            "MEDIUM": "yellow", 
            "LOW": "green"
        }
        
        table = Table.grid(padding=1)
        table.add_column(style="bold")
        table.add_column()
        
        table.add_row("Technology:", f"[bold cyan]{rec.technology}[/bold cyan]")
        table.add_row("Priority:", f"[{priority_color[rec.priority]}]{rec.priority}[/{priority_color[rec.priority]}]")
        table.add_row("Effort:", rec.implementation_effort)
        table.add_row("Reason:", rec.reason)
        
        table.add_row("Evidence:", "")
        for evidence in rec.evidence:
            table.add_row("", f"• {evidence}")
            
        table.add_row("Current:", rec.current_pattern)
        table.add_row("Suggested:", rec.suggested_pattern)
        
        self.console.print(Panel(table, title=f"💡 {rec.technology}", border_style="dim"))
        self.console.print()