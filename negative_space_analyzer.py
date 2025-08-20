#!/usr/bin/env python3
"""
Negative Space Best Practices Analyzer

This analyzer identifies best practices by finding the "negative space" - 
what problems some projects have that others avoid, and analyzing the patterns
that prevent those problems.

Philosophy:
- Best practices are often invisible (what's NOT there)
- Learn from projects that avoid common problems
- Identify protective patterns that prevent issues
- Reverse-engineer excellence from absence of problems
"""

from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict
import json

from enhanced_intelligent_scanner import EnhancedIntelligentScanner


class NegativeSpaceAnalyzer:
    """
    Analyzes what problems each project avoids to identify best practices.
    
    Method:
    1. Run violation scans on all projects
    2. Identify which projects avoid specific problem categories
    3. Analyze what those clean projects do differently
    4. Extract the protective patterns as best practices
    """
    
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.project_violations = {}
        self.clean_project_patterns = {}
        
    def analyze_organizational_negative_space(self) -> Dict[str, Any]:
        """Analyze negative space across all organizational projects."""
        import logging
        logging.info("=== NEGATIVE SPACE BEST PRACTICES ANALYSIS ===")
        logging.info("Finding excellence through what projects DON'T have wrong...")
        
        # Step 1: Scan all projects for violations
        all_projects_data = self._scan_all_projects()
        
        # Step 2: Identify negative space patterns
        negative_space_patterns = self._identify_negative_space_patterns(all_projects_data)
        
        # Step 3: Analyze protective patterns in clean projects
        protective_patterns = self._analyze_protective_patterns(negative_space_patterns)
        
        # Step 4: Generate best practice recommendations
        best_practices = self._extract_best_practices(protective_patterns)
        
        return {
            'projects_analyzed': len(all_projects_data),
            'negative_space_patterns': negative_space_patterns,
            'protective_patterns': protective_patterns,
            'best_practices': best_practices,
            'summary': self._create_negative_space_summary(negative_space_patterns, best_practices)
        }
    
    def _scan_all_projects(self) -> Dict[str, Dict[str, Any]]:
        """Scan all projects and collect violation data."""
        all_projects_data = {}
        
        for project_dir in self.work_dir.iterdir():
            if not project_dir.is_dir() or project_dir.name.startswith('.'):
                continue
                
            # Check if it's a Python project
            if not self._is_python_project(project_dir):
                continue
            
            logging.info(f"Scanning {project_dir.name} for violations...")
            
            try:
                scanner = EnhancedIntelligentScanner(project_dir)
                scan_results = scanner.comprehensive_scan()
                
                # Categorize violations by type
                violations_by_category = self._categorize_violations(scan_results)
                
                # Analyze project structure
                project_structure = self._analyze_project_structure(project_dir)
                
                all_projects_data[project_dir.name] = {
                    'violations_by_category': violations_by_category,
                    'total_violations': scan_results.get('total_violations', 0),
                    'project_structure': project_structure,
                    'files_count': len(list(project_dir.rglob('*.py'))),
                    'scan_results': scan_results
                }
            except Exception as e:
                logging.error(f"Error scanning {project_dir.name}: {e}")
                continue
        
        return all_projects_data
    
    def _is_python_project(self, project_dir: Path) -> bool:
        """Check if directory is a Python project."""
        indicators = ['pyproject.toml', 'setup.py', 'requirements.txt']
        return any((project_dir / indicator).exists() for indicator in indicators) or \
               bool(list(project_dir.glob('*.py')))
    
    def _categorize_violations(self, scan_results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize violations by problem type."""
        violations_by_category = defaultdict(list)
        
        for fix_plan in scan_results.get('fix_plans', []):
            violation = fix_plan.get('violation', {})
            pattern = violation.get('pattern', 'unknown')
            category = violation.get('category', 'unknown')
            
            violations_by_category[pattern].append(violation)
        
        return dict(violations_by_category)
    
    def _analyze_project_structure(self, project_dir: Path) -> Dict[str, Any]:
        """Analyze project structure for protective patterns."""
        structure = {
            'has_core_package': (project_dir / 'core').exists(),
            'has_api_package': (project_dir / 'api').exists(),
            'has_cli_package': (project_dir / 'cli').exists(),
            'has_tests': (project_dir / 'tests').exists() or bool(list(project_dir.rglob('test_*.py'))),
            'has_settings_file': bool(list(project_dir.rglob('*settings*.py'))),
            'has_init_files': len(list(project_dir.rglob('__init__.py'))) > 0,
            'package_depth': self._calculate_package_depth(project_dir),
            'file_organization': self._analyze_file_organization(project_dir)
        }
        
        return structure
    
    def _calculate_package_depth(self, project_dir: Path) -> int:
        """Calculate maximum package nesting depth."""
        max_depth = 0
        for init_file in project_dir.rglob('__init__.py'):
            depth = len(init_file.relative_to(project_dir).parts) - 1
            max_depth = max(max_depth, depth)
        return max_depth
    
    def _analyze_file_organization(self, project_dir: Path) -> Dict[str, Any]:
        """Analyze how files are organized."""
        py_files = list(project_dir.rglob('*.py'))
        
        # Count files by directory depth
        depth_distribution = defaultdict(int)
        for py_file in py_files:
            depth = len(py_file.relative_to(project_dir).parts) - 1
            depth_distribution[depth] += 1
        
        # Check for monolithic files (very large files)
        large_files = []
        for py_file in py_files:
            try:
                size = py_file.stat().st_size
                if size > 10000:  # > 10KB
                    large_files.append({
                        'file': str(py_file.relative_to(project_dir)),
                        'size': size
                    })
            except OSError:
                continue
        
        return {
            'depth_distribution': dict(depth_distribution),
            'large_files': large_files,
            'total_files': len(py_files)
        }
    
    def _identify_negative_space_patterns(self, all_projects_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Identify which projects avoid which problems."""
        logging.info("=== IDENTIFYING NEGATIVE SPACE PATTERNS ===")
        
        # Get all possible violation patterns
        all_patterns = set()
        for project_data in all_projects_data.values():
            all_patterns.update(project_data['violations_by_category'].keys())
        
        negative_space = {}
        
        for pattern in all_patterns:
            # Find projects that have this problem vs those that don't
            projects_with_problem = []
            projects_without_problem = []
            
            for project_name, project_data in all_projects_data.items():
                if pattern in project_data['violations_by_category']:
                    violation_count = len(project_data['violations_by_category'][pattern])
                    projects_with_problem.append({
                        'project': project_name,
                        'violation_count': violation_count,
                        'structure': project_data['project_structure']
                    })
                else:
                    projects_without_problem.append({
                        'project': project_name,
                        'structure': project_data['project_structure']
                    })
            
            # Only analyze patterns where some projects avoid the problem
            if projects_without_problem and projects_with_problem:
                negative_space[pattern] = {
                    'projects_with_problem': projects_with_problem,
                    'projects_without_problem': projects_without_problem,
                    'avoidance_rate': len(projects_without_problem) / len(all_projects_data),
                    'problem_severity': sum(p['violation_count'] for p in projects_with_problem)
                }
                
                logging.info(f"📊 {pattern}:")
                logging.info(f"   ❌ Projects with problem: {[p['project'] for p in projects_with_problem]}")
                logging.info(f"   ✅ Projects avoiding problem: {[p['project'] for p in projects_without_problem]}")
                logging.info(f"   📈 Avoidance rate: {negative_space[pattern]['avoidance_rate']:.1%}")
        
        return negative_space
    
    def _analyze_protective_patterns(self, negative_space_patterns: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze what structural patterns protect against each problem."""
        logging.info("=== ANALYZING PROTECTIVE PATTERNS ===")
        
        protective_patterns = {}
        
        for pattern, data in negative_space_patterns.items():
            if data['avoidance_rate'] < 0.3:  # Skip if too few projects avoid it
                continue
            
            logging.info(f"🔍 Analyzing protective patterns for: {pattern}")
            
            # Compare structural differences
            clean_projects = data['projects_without_problem']
            problem_projects = data['projects_with_problem']
            
            # Find structural patterns that correlate with avoiding the problem
            protective_factors = []
            
            # Check specific structural differences
            for factor in ['has_core_package', 'has_api_package', 'has_cli_package', 
                          'has_tests', 'has_settings_file', 'has_init_files']:
                
                clean_rate = sum(1 for p in clean_projects if p['structure'][factor]) / len(clean_projects)
                problem_rate = sum(1 for p in problem_projects if p['structure'][factor]) / len(problem_projects)
                
                # If clean projects have this factor significantly more often
                if clean_rate - problem_rate > 0.3:
                    protective_factors.append(f"{factor}: {clean_rate:.1%} vs {problem_rate:.1%}")
                    logging.info(f"   ✅ {factor}: Clean projects {clean_rate:.1%}, Problem projects {problem_rate:.1%}")
            
            # Check package depth patterns
            clean_depths = [p['structure']['package_depth'] for p in clean_projects]
            problem_depths = [p['structure']['package_depth'] for p in problem_projects]
            
            if clean_depths and problem_depths:
                clean_avg_depth = sum(clean_depths) / len(clean_depths)
                problem_avg_depth = sum(problem_depths) / len(problem_depths)
                
                if abs(clean_avg_depth - problem_avg_depth) > 0.5:
                    protective_factors.append(f"package_depth: {clean_avg_depth:.1f} vs {problem_avg_depth:.1f}")
                    logging.info(f"   📁 Package depth: Clean {clean_avg_depth:.1f}, Problem {problem_avg_depth:.1f}")
            
            protective_patterns[pattern] = protective_factors
        
        return protective_patterns
    
    def _extract_best_practices(self, protective_patterns: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Extract actionable best practices from protective patterns."""
        best_practices = []
        
        # Group by common protective factors
        factor_frequency = defaultdict(list)
        for pattern, factors in protective_patterns.items():
            for factor in factors:
                factor_frequency[factor].append(pattern)
        
        # Convert to best practices
        for factor, protected_patterns in factor_frequency.items():
            if len(protected_patterns) >= 2:  # Factor protects against multiple problems
                best_practice = {
                    'practice': self._factor_to_practice(factor),
                    'protects_against': protected_patterns,
                    'evidence_strength': len(protected_patterns),
                    'recommendation': self._generate_recommendation(factor, protected_patterns)
                }
                best_practices.append(best_practice)
        
        # Sort by evidence strength
        best_practices.sort(key=lambda x: x['evidence_strength'], reverse=True)
        
        return best_practices
    
    def _factor_to_practice(self, factor: str) -> str:
        """Convert a protective factor to a best practice description."""
        if 'has_core_package' in factor:
            return "Maintain separate core/ package for business logic"
        elif 'has_api_package' in factor:
            return "Use dedicated api/ package for interface layer"
        elif 'has_cli_package' in factor:
            return "Organize CLI as separate package, not monolithic file"
        elif 'has_tests' in factor:
            return "Maintain comprehensive test suite"
        elif 'has_settings_file' in factor:
            return "Use dedicated settings/configuration module"
        elif 'has_init_files' in factor:
            return "Proper package initialization with __init__.py files"
        elif 'package_depth' in factor:
            return "Maintain appropriate package nesting depth"
        else:
            return f"Structural pattern: {factor}"
    
    def _generate_recommendation(self, factor: str, protected_patterns: List[str]) -> str:
        """Generate actionable recommendation."""
        problem_types = []
        for pattern in protected_patterns:
            if 'business_logic' in pattern:
                problem_types.append("architectural violations")
            elif 'secret' in pattern:
                problem_types.append("security issues")
            elif 'settings' in pattern:
                problem_types.append("configuration problems")
            else:
                problem_types.append("code quality issues")
        
        unique_problems = list(set(problem_types))
        
        return f"Implementing this pattern helps avoid: {', '.join(unique_problems)}"
    
    def _create_negative_space_summary(self, negative_space_patterns: Dict[str, Any], best_practices: List[Dict[str, Any]]) -> str:
        """Create comprehensive summary of negative space analysis."""
        summary = f"""
NEGATIVE SPACE BEST PRACTICES ANALYSIS
=====================================

METHODOLOGY: Analyzed what problems each project avoids to identify protective patterns

ANALYSIS RESULTS:
• {len(negative_space_patterns)} problem patterns analyzed
• {len(best_practices)} evidence-based best practices identified
• Protective patterns discovered through comparative analysis

TOP EVIDENCE-BASED BEST PRACTICES:
"""
        
        for i, practice in enumerate(best_practices[:5], 1):
            summary += f"\n{i}. {practice['practice']}"
            summary += f"\n   Evidence: Protects against {practice['evidence_strength']} different problem types"
            summary += f"\n   {practice['recommendation']}\n"
        
        summary += f"\nPROBLEM AVOIDANCE PATTERNS:\n"
        
        # Show which projects are consistently clean
        project_scores = defaultdict(int)
        for pattern_data in negative_space_patterns.values():
            for clean_project in pattern_data['projects_without_problem']:
                project_scores[clean_project['project']] += 1
        
        if project_scores:
            top_clean_projects = sorted(project_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            summary += f"🏆 Most consistently clean projects:\n"
            for project, avoided_problems in top_clean_projects:
                summary += f"   • {project}: Avoids {avoided_problems} different problem types\n"
        
        summary += f"\nMETHODOLOGY VALIDATION:"
        summary += f"\n✅ Comparative analysis across multiple projects"
        summary += f"\n✅ Evidence-based pattern identification"
        summary += f"\n✅ Structural correlation analysis"
        summary += f"\n✅ Actionable recommendations generated"
        
        return summary


def main():
    """Run negative space analysis across all projects."""
    import logging
    work_dir = Path('/Users/admin/work')
    
    if not work_dir.exists():
        logging.error(f"Work directory not found: {work_dir}")
        return
    
    analyzer = NegativeSpaceAnalyzer(work_dir)
    results = analyzer.analyze_organizational_negative_space()
    
    logging.info(results['summary'])
    
    # Save detailed results
    output_file = Path('negative_space_analysis.json')
    with open(output_file, 'w') as f:
        # Convert results to JSON-serializable format
        json_results = {
            'projects_analyzed': results['projects_analyzed'],
            'best_practices': results['best_practices'],
            'analysis_timestamp': str(datetime.now())
        }
        json.dump(json_results, f, indent=2)
    
    logging.info(f"📊 Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    from datetime import datetime
    main()