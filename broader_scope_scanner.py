#!/usr/bin/env python3
"""
Broader Scope Scanner - Test enhanced patterns on wider codebase

This scanner applies our enhanced patterns to a broader scope to validate
their effectiveness across different types of projects and codebases.
"""

from pathlib import Path
from enhanced_intelligent_scanner import EnhancedIntelligentScanner


class BroaderScopeScanner:
    """Test enhanced patterns across multiple projects and directories."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.project_results = {}
    
    def scan_multiple_projects(self) -> dict:
        """Scan multiple projects to test pattern effectiveness."""
        print("=== BROADER SCOPE SCANNING ===")
        print("Testing enhanced patterns across multiple projects...")
        
        # Find potential project directories
        project_dirs = self._find_project_directories()
        
        # Scan each project
        for project_dir in project_dirs[:5]:  # Limit to first 5 for demo
            try:
                print(f"\nScanning project: {project_dir.name}")
                scanner = EnhancedIntelligentScanner(project_dir)
                results = scanner.comprehensive_scan()
                
                self.project_results[project_dir.name] = {
                    'path': str(project_dir),
                    'violations': results['total_violations'],
                    'by_priority': results['by_priority'],
                    'fix_plans': len(results['fix_plans']),
                    'summary': results['summary']
                }
                
                print(f"  Violations found: {results['total_violations']}")
                if results['total_violations'] > 0:
                    print(f"  Priority breakdown: {results['by_priority']}")
                
            except Exception as e:
                print(f"  Error scanning {project_dir.name}: {e}")
                continue
        
        return self._create_aggregate_report()
    
    def _find_project_directories(self) -> list[Path]:
        """Find directories that look like Python projects."""
        project_dirs = []
        
        for item in self.base_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check for Python project indicators
                if self._looks_like_python_project(item):
                    project_dirs.append(item)
        
        return sorted(project_dirs)
    
    def _looks_like_python_project(self, directory: Path) -> bool:
        """Check if directory looks like a Python project."""
        indicators = [
            'pyproject.toml',
            'setup.py', 
            'requirements.txt',
            'Pipfile',
            'poetry.lock',
            '__init__.py'
        ]
        
        # Check for Python files
        python_files = list(directory.glob('*.py'))
        if len(python_files) > 0:
            return True
        
        # Check for project indicators
        for indicator in indicators:
            if (directory / indicator).exists():
                return True
        
        # Check for subdirectories with Python files
        for subdir in directory.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.'):
                if list(subdir.glob('*.py')):
                    return True
        
        return False
    
    def _create_aggregate_report(self) -> dict:
        """Create aggregate report across all scanned projects."""
        total_projects = len(self.project_results)
        total_violations = sum(r['violations'] for r in self.project_results.values())
        projects_with_violations = sum(1 for r in self.project_results.values() if r['violations'] > 0)
        
        # Aggregate by priority
        aggregate_priority = {
            'CRITICAL': 0,
            'MANDATORY': 0, 
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        
        for result in self.project_results.values():
            for priority, count in result['by_priority'].items():
                aggregate_priority[priority] = aggregate_priority.get(priority, 0) + count
        
        # Find most common violation types
        violation_patterns = {}
        for result in self.project_results.values():
            # This would need more detailed violation data to implement fully
            pass
        
        report = {
            'total_projects_scanned': total_projects,
            'total_violations_found': total_violations,
            'projects_with_violations': projects_with_violations,
            'clean_projects': total_projects - projects_with_violations,
            'aggregate_priority': aggregate_priority,
            'project_details': self.project_results,
            'effectiveness_metrics': {
                'projects_clean_percentage': ((total_projects - projects_with_violations) / max(total_projects, 1)) * 100,
                'average_violations_per_project': total_violations / max(total_projects, 1),
                'critical_issues_found': aggregate_priority['CRITICAL'],
                'mandatory_issues_found': aggregate_priority['MANDATORY']
            }
        }
        
        return report


def main():
    """Run broader scope scanning to validate enhanced patterns."""
    work_dir = Path('/Users/admin/work')
    
    if not work_dir.exists():
        print(f"Work directory not found: {work_dir}")
        return
    
    scanner = BroaderScopeScanner(work_dir)
    results = scanner.scan_multiple_projects()
    
    print(f"\n=== BROADER SCOPE SCAN RESULTS ===")
    print(f"Projects scanned: {results['total_projects_scanned']}")
    print(f"Total violations found: {results['total_violations_found']}")
    print(f"Projects with violations: {results['projects_with_violations']}")
    print(f"Clean projects: {results['clean_projects']}")
    print(f"Clean project percentage: {results['effectiveness_metrics']['projects_clean_percentage']:.1f}%")
    
    if results['total_violations_found'] > 0:
        print(f"\nViolations by priority:")
        for priority, count in results['aggregate_priority'].items():
            if count > 0:
                print(f"  {priority}: {count}")
        
        print(f"\nProject details:")
        for project_name, details in results['project_details'].items():
            if details['violations'] > 0:
                print(f"  {project_name}: {details['violations']} violations")
    else:
        print(f"\n🎉 ALL SCANNED PROJECTS ARE CLEAN!")
        print(f"Enhanced patterns validate excellent code quality across all projects")
    
    print(f"\nEffectiveness metrics:")
    print(f"  Average violations per project: {results['effectiveness_metrics']['average_violations_per_project']:.1f}")
    print(f"  Critical security issues: {results['effectiveness_metrics']['critical_issues_found']}")
    print(f"  Mandatory policy violations: {results['effectiveness_metrics']['mandatory_issues_found']}")


if __name__ == "__main__":
    main()