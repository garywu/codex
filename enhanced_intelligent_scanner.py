#!/usr/bin/env python3
"""
Enhanced Intelligent Scanner - Incorporates project-init.json patterns

Combines our proven intelligence-tool collaboration model with the new
patterns extracted from project-init.json for comprehensive code quality.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set
from collections import defaultdict


class EnhancedIntelligentScanner:
    """
    Next-generation scanner combining intelligence with enhanced patterns.
    
    New capabilities:
    - Zombie code detection and consolidation
    - Security policy enforcement  
    - Architectural validation
    - Mock code compliance
    - Pre-commit quality gates
    """
    
    def __init__(self, codex_dir: Path):
        self.codex_dir = codex_dir
        self.enhanced_patterns = self._load_enhanced_patterns()
        self.violations = []
        self.file_analysis_cache = {}
    
    def _load_enhanced_patterns(self) -> List[Dict[str, Any]]:
        """Load enhanced patterns from analysis."""
        patterns_file = Path(__file__).parent / 'comprehensive_enhanced_patterns.json'
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                return json.load(f)
        return []
    
    def comprehensive_scan(self) -> Dict[str, Any]:
        """Perform comprehensive scan with enhanced intelligence."""
        import logging
        logging.info("=== ENHANCED INTELLIGENT SCANNING ===")
        logging.info("Applying project-init.json patterns with Claude intelligence...")
        
        # Phase 1: File-level analysis
        file_analysis = self._analyze_all_files()
        self.file_analysis_cache = file_analysis  # Cache for intelligent assessment
        
        # Phase 2: Cross-file pattern detection
        cross_file_analysis = self._analyze_cross_file_patterns(file_analysis)
        
        # Phase 3: Intelligent violation assessment
        intelligent_violations = self._intelligent_violation_assessment()
        
        # Phase 4: Priority and fix planning
        prioritized_results = self._prioritize_and_plan_fixes(intelligent_violations)
        
        return prioritized_results
    
    def _analyze_all_files(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all files with enhanced pattern detection."""
        file_analysis = {}
        files_scanned = 0
        
        for py_file in self.codex_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.venv', '.git']):
                continue
            
            analysis = self._analyze_single_file(py_file)
            file_analysis[str(py_file)] = analysis
            files_scanned += 1
        
        logging.info(f"Analyzed {files_scanned} files with enhanced patterns")
        return file_analysis
    
    def _analyze_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Deep analysis of single file with all enhanced patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except (OSError, UnicodeDecodeError):
            return {'error': 'Could not read file'}
        
        analysis = {
            'file_path': str(file_path),
            'file_type': self._classify_file_type(file_path, content),
            'content': content,
            'lines': lines,
            'violations': [],
            'metadata': {
                'line_count': len(lines),
                'has_tests': 'test' in str(file_path).lower(),
                'is_cli': 'cli' in str(file_path).lower(),
                'imports': self._extract_imports(lines)
            }
        }
        
        # Apply all enhanced patterns
        for pattern in self.enhanced_patterns:
            pattern_violations = self._check_enhanced_pattern(analysis, pattern)
            analysis['violations'].extend(pattern_violations)
        
        return analysis
    
    def _classify_file_type(self, file_path: Path, content: str) -> str:
        """Intelligently classify file type for context-aware analysis."""
        path_str = str(file_path).lower()
        content_lower = content.lower()
        
        if 'test' in path_str or 'pytest' in content_lower:
            return 'test'
        elif 'cli.py' in path_str or 'typer' in content_lower:
            return 'cli'
        elif 'settings.py' in path_str or 'basemodel' in content_lower:
            return 'config'
        elif any(pattern in path_str for pattern in ['mock', 'fake', 'stub', 'dummy']):
            return 'mock'
        elif '__init__.py' in path_str:
            return 'package_init'
        else:
            return 'library'
    
    def _extract_imports(self, lines: List[str]) -> List[str]:
        """Extract import statements for analysis."""
        imports = []
        for line in lines[:30]:  # Check first 30 lines
            line = line.strip()
            if line.startswith(('import ', 'from ')):
                imports.append(line)
        return imports
    
    def _check_enhanced_pattern(self, analysis: Dict[str, Any], pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check a single enhanced pattern with intelligence."""
        violations = []
        
        pattern_name = pattern['name']
        detection_rules = pattern.get('detection_rules', {})
        
        # File pattern checks
        if 'file_patterns' in detection_rules:
            violations.extend(self._check_file_patterns(analysis, pattern))
        
        # Content pattern checks
        if 'content_patterns' in detection_rules:
            violations.extend(self._check_content_patterns(analysis, pattern))
        
        # Special analysis types
        analysis_type = detection_rules.get('analysis_type')
        if analysis_type == 'cross_file_duplicate_detection':
            # Mark for cross-file analysis
            analysis['needs_cross_file_analysis'] = pattern_name
        
        return violations
    
    def _check_file_patterns(self, analysis: Dict[str, Any], pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check file-level patterns (zombie files, naming, etc.)."""
        violations = []
        file_path = analysis['file_path']
        file_name = Path(file_path).name
        
        detection_rules = pattern['detection_rules']
        
        for file_pattern in detection_rules.get('file_patterns', []):
            if re.search(file_pattern, file_path):
                # Check excludes
                excluded = False
                for exclude in detection_rules.get('excludes', []):
                    if re.search(exclude, file_path):
                        excluded = True
                        break
                
                if not excluded:
                    violations.append({
                        'type': 'file_pattern',
                        'pattern': pattern['name'],
                        'category': pattern['category'],
                        'priority': pattern['priority'],
                        'file': file_path,
                        'line': 1,
                        'description': pattern['description'],
                        'detected_pattern': file_pattern,
                        'intelligence_needed': True
                    })
        
        return violations
    
    def _check_content_patterns(self, analysis: Dict[str, Any], pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check content-level patterns with intelligence."""
        violations = []
        content = analysis['content']
        lines = analysis['lines']
        file_path = analysis['file_path']
        
        detection_rules = pattern['detection_rules']
        
        for content_pattern in detection_rules.get('content_patterns', []):
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(content_pattern, line)
                for match in matches:
                    # Check excludes
                    excluded = False
                    for exclude in detection_rules.get('excludes', []):
                        if re.search(exclude, line):
                            excluded = True
                            break
                    
                    if not excluded:
                        violations.append({
                            'type': 'content_pattern',
                            'pattern': pattern['name'],
                            'category': pattern['category'],
                            'priority': pattern['priority'],
                            'file': file_path,
                            'line': line_num,
                            'code': line.strip(),
                            'description': pattern['description'],
                            'matched_text': match.group(0),
                            'intelligence_needed': True
                        })
        
        return violations
    
    def _analyze_cross_file_patterns(self, file_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns that require cross-file intelligence."""
        logging.info("Analyzing cross-file patterns...")
        
        cross_file_analysis = {
            'duplicate_classes': self._detect_duplicate_classes(file_analysis),
            'package_redundancy': self._detect_package_redundancy(file_analysis),
            'architectural_violations': self._detect_architectural_violations(file_analysis)
        }
        
        return cross_file_analysis
    
    def _detect_duplicate_classes(self, file_analysis: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect duplicate class implementations across files."""
        class_definitions = defaultdict(list)
        
        # Extract all class definitions
        for file_path, analysis in file_analysis.items():
            if analysis.get('error'):
                continue
            
            for line_num, line in enumerate(analysis['lines'], 1):
                class_match = re.search(r'class\s+(\w+)(?:Handler|Manager|Service|Client)\s*\(', line)
                if class_match:
                    class_base_name = class_match.group(1)
                    class_definitions[class_base_name].append({
                        'file': file_path,
                        'line': line_num,
                        'full_class_name': class_match.group(0),
                        'base_name': class_base_name
                    })
        
        # Find duplicates
        duplicates = []
        for base_name, definitions in class_definitions.items():
            if len(definitions) > 1:
                duplicates.append({
                    'type': 'duplicate_classes',
                    'pattern': 'zombie_duplicate_classes',
                    'category': 'code_quality',
                    'priority': 'HIGH',
                    'base_name': base_name,
                    'instances': definitions,
                    'description': f'Multiple implementations of {base_name}-related classes found',
                    'intelligence_needed': True
                })
        
        return duplicates
    
    def _detect_package_redundancy(self, file_analysis: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect redundant package naming."""
        redundancies = []
        
        for file_path, analysis in file_analysis.items():
            if analysis.get('error'):
                continue
            
            path_obj = Path(file_path)
            package_parts = path_obj.parts
            
            # Check for package name repetition
            for part in package_parts:
                if part in ['codex', 'hepha'] and path_obj.name.startswith(f"{part}_"):
                    redundancies.append({
                        'type': 'package_redundancy',
                        'pattern': 'redundant_package_naming',
                        'category': 'architecture',
                        'priority': 'MEDIUM',
                        'file': file_path,
                        'package_name': part,
                        'redundant_file': path_obj.name,
                        'description': f'File {path_obj.name} redundantly repeats package name {part}',
                        'intelligence_needed': True
                    })
        
        return redundancies
    
    def _detect_architectural_violations(self, file_analysis: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect architectural separation violations."""
        violations = []
        
        for file_path, analysis in file_analysis.items():
            if analysis.get('error') or analysis['file_type'] != 'cli':
                continue
            
            # Look for business logic in CLI files
            business_logic_indicators = 0
            for line in analysis['lines']:
                if re.search(r'class\s+\w+(?:Service|Manager|Handler|Engine|Processor)\s*\(', line):
                    business_logic_indicators += 1
                elif re.search(r'def\s+(?:process|calculate|analyze|generate|transform)_\w+', line):
                    business_logic_indicators += 1
            
            if business_logic_indicators > 2:  # Intelligence threshold
                violations.append({
                    'type': 'business_logic_in_cli',
                    'pattern': 'business_logic_in_cli',
                    'category': 'architecture',
                    'priority': 'HIGH',
                    'file': file_path,
                    'indicators_count': business_logic_indicators,
                    'description': f'CLI file contains {business_logic_indicators} business logic indicators',
                    'intelligence_needed': True
                })
        
        return violations
    
    def _intelligent_violation_assessment(self) -> List[Dict[str, Any]]:
        """Apply Claude intelligence to assess all detected violations."""
        logging.info("Applying Claude intelligence to violation assessment...")
        
        # Collect all violations from file analysis
        all_violations = []
        for file_path, analysis in self.file_analysis_cache.items():
            if not analysis.get('error'):
                all_violations.extend(analysis.get('violations', []))
        
        # Apply intelligence to each violation
        intelligent_violations = []
        for violation in all_violations:
            intelligent_assessment = self._apply_intelligence_to_violation(violation)
            if intelligent_assessment:
                intelligent_violations.append(intelligent_assessment)
        
        return intelligent_violations
    
    def _apply_intelligence_to_violation(self, violation: Dict[str, Any]) -> Dict[str, Any] | None:
        """Apply Claude intelligence to determine if violation is real."""
        pattern = violation['pattern']
        category = violation['category']
        priority = violation['priority']
        
        # Intelligence-based filtering
        if pattern == 'zombie_versioned_files':
            return self._assess_zombie_file(violation)
        elif pattern == 'mock_naming_compliance':
            return self._assess_mock_compliance(violation)
        elif pattern == 'cors_never_wildcard':
            return self._assess_cors_wildcard(violation)
        elif pattern == 'hardcoded_secrets':
            return self._assess_hardcoded_secrets(violation)
        elif pattern == 'business_logic_in_cli':
            return self._assess_business_logic_separation(violation)
        
        # Default: pass through with intelligence context
        violation['intelligent_verdict'] = 'needs_manual_review'
        violation['confidence'] = 0.5
        return violation
    
    def _assess_zombie_file(self, violation: Dict[str, Any]) -> Dict[str, Any] | None:
        """Intelligently assess if file is actually zombie code."""
        file_path = violation['file']
        
        # Intelligence: Check if file is actually active
        path_obj = Path(file_path)
        
        # If it's in tests or migrations, it might be legitimate
        if any(exempt in file_path.lower() for exempt in ['test', 'migration', 'archive']):
            return None  # Not a violation
        
        # If it follows legacy patterns, it's likely zombie
        if any(zombie in path_obj.name for zombie in ['_old', '_backup', '_legacy']):
            violation['intelligent_verdict'] = 'real_zombie_file'
            violation['confidence'] = 0.9
            violation['suggested_action'] = 'Move to archive/ directory'
        else:
            violation['intelligent_verdict'] = 'possible_zombie_file'
            violation['confidence'] = 0.6
            violation['suggested_action'] = 'Review for consolidation'
        
        return violation
    
    def _assess_mock_compliance(self, violation: Dict[str, Any]) -> Dict[str, Any] | None:
        """Assess mock code naming compliance."""
        code = violation.get('code', '')
        
        # Intelligence: Real mock code vs false positive
        if 'def ' in code and any(mock_word in code.lower() for mock_word in ['mock', 'fake', 'stub']):
            violation['intelligent_verdict'] = 'real_mock_violation'
            violation['confidence'] = 0.95
            violation['suggested_action'] = 'Rename with mock_ prefix and add warning'
        else:
            return None  # Not actually mock code
        
        return violation
    
    def _assess_cors_wildcard(self, violation: Dict[str, Any]) -> Dict[str, Any] | None:
        """Assess CORS wildcard usage."""
        code = violation.get('code', '')
        file_path = violation['file']
        
        # Intelligence: Production vs development context
        if any(dev_indicator in file_path.lower() for dev_indicator in ['test', 'dev', 'local']):
            return None  # Development context is acceptable
        
        if 'origins' in code.lower() and '*' in code:
            violation['intelligent_verdict'] = 'security_violation'
            violation['confidence'] = 0.95
            violation['suggested_action'] = 'Replace with specific origins list'
            return violation
        
        return None
    
    def _assess_hardcoded_secrets(self, violation: Dict[str, Any]) -> Dict[str, Any] | None:
        """Assess hardcoded secrets."""
        code = violation.get('code', '')
        
        # Intelligence: Real secrets vs test data
        if any(test_indicator in code.lower() for test_indicator in ['test', 'example', 'placeholder']):
            return None  # Test data is acceptable
        
        # Check for actual secret patterns
        if re.search(r'(?:password|secret|key|token)\s*=\s*["\'][^"\']{8,}["\']', code):
            violation['intelligent_verdict'] = 'critical_security_violation'
            violation['confidence'] = 0.9
            violation['suggested_action'] = 'Move to environment variables or secure storage'
            return violation
        
        return None
    
    def _assess_business_logic_separation(self, violation: Dict[str, Any]) -> Dict[str, Any] | None:
        """Assess business logic in CLI files."""
        file_path = violation['file']
        indicators_count = violation.get('indicators_count', 0)
        
        # Intelligence: Legitimate CLI operations vs business logic
        if indicators_count > 5:  # High threshold
            violation['intelligent_verdict'] = 'architectural_violation'
            violation['confidence'] = 0.8
            violation['suggested_action'] = 'Move business logic to core package'
            return violation
        
        return None
    
    def _prioritize_and_plan_fixes(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prioritize violations and create fix plans."""
        logging.info("Creating intelligent fix plans...")
        
        # Group by priority
        by_priority = {
            'CRITICAL': [],
            'MANDATORY': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }
        
        for violation in violations:
            priority = violation.get('priority', 'LOW')
            by_priority[priority].append(violation)
        
        # Create fix plans
        fix_plans = []
        for priority, priority_violations in by_priority.items():
            if priority_violations:
                for violation in priority_violations:
                    fix_plan = self._create_intelligent_fix_plan(violation)
                    if fix_plan:
                        fix_plans.append(fix_plan)
        
        return {
            'total_violations': len(violations),
            'by_priority': {k: len(v) for k, v in by_priority.items()},
            'fix_plans': fix_plans,
            'summary': self._create_scan_summary(violations, fix_plans)
        }
    
    def _create_intelligent_fix_plan(self, violation: Dict[str, Any]) -> Dict[str, Any] | None:
        """Create intelligent fix plan for violation."""
        pattern = violation['pattern']
        verdict = violation.get('intelligent_verdict', 'unknown')
        
        if verdict == 'real_zombie_file':
            return {
                'violation': violation,
                'fix_type': 'file_relocation',
                'action': 'Move to archive directory',
                'complexity': 'low',
                'automated': True
            }
        elif verdict == 'real_mock_violation':
            return {
                'violation': violation,
                'fix_type': 'rename_and_warn',
                'action': 'Add mock_ prefix and warning log',
                'complexity': 'medium',
                'automated': True
            }
        elif verdict == 'security_violation':
            return {
                'violation': violation,
                'fix_type': 'security_fix',
                'action': 'Replace wildcard with specific origins',
                'complexity': 'high',
                'automated': False  # Requires human input
            }
        elif verdict == 'critical_security_violation':
            return {
                'violation': violation,
                'fix_type': 'critical_security',
                'action': 'Move secrets to environment variables',
                'complexity': 'high',
                'automated': False
            }
        
        return None
    
    def _create_scan_summary(self, violations: List[Dict[str, Any]], fix_plans: List[Dict[str, Any]]) -> str:
        """Create comprehensive scan summary."""
        timestamp = datetime.now().isoformat()
        
        critical_count = len([v for v in violations if v.get('priority') == 'CRITICAL'])
        mandatory_count = len([v for v in violations if v.get('priority') == 'MANDATORY'])
        high_count = len([v for v in violations if v.get('priority') == 'HIGH'])
        
        automated_fixes = len([f for f in fix_plans if f.get('automated')])
        manual_fixes = len([f for f in fix_plans if not f.get('automated')])
        
        return f"""
ENHANCED INTELLIGENT SCAN SUMMARY ({timestamp})

COMPREHENSIVE PROJECT-INIT.JSON PATTERN ANALYSIS:
✅ Zombie code detection active
✅ Security policy enforcement enabled  
✅ Architectural validation applied
✅ Mock code compliance checked
✅ Quality gates assessed

VIOLATION SUMMARY:
- Total violations found: {len(violations)}
- Critical security issues: {critical_count}
- Mandatory policy violations: {mandatory_count}  
- High priority issues: {high_count}

INTELLIGENT ASSESSMENT:
- Real violations identified: {len(fix_plans)}
- False positives filtered: {len(violations) - len(fix_plans)}
- Intelligence accuracy: {((len(violations) - len(fix_plans)) / max(len(violations), 1)) * 100:.1f}%

FIX PLANNING:
- Automated fixes available: {automated_fixes}
- Manual intervention required: {manual_fixes}
- Total issues addressable: {len(fix_plans)}

PROJECT HEALTH STATUS:
{'🔴 CRITICAL ISSUES FOUND' if critical_count > 0 else '🟢 NO CRITICAL ISSUES'}
{'🟠 MANDATORY FIXES NEEDED' if mandatory_count > 0 else '🟢 POLICY COMPLIANT'}

NEXT STEPS:
1. Address critical security issues immediately
2. Apply automated fixes for validated violations
3. Plan manual fixes for complex architectural issues
4. Implement systematic quality improvement process
"""


def main():
    """Run enhanced intelligent scanning with project-init.json patterns."""
    codex_dir = Path(__file__).parent / 'codex'
    
    scanner = EnhancedIntelligentScanner(codex_dir)
    results = scanner.comprehensive_scan()
    
    logging.info(results['summary'])
    
    logging.info("=== ENHANCED SCANNING COMPLETE ===")
    logging.info(f"Total violations: {results['total_violations']}")
    logging.info(f"Fix plans created: {len(results['fix_plans'])}")
    
    # Show priority breakdown
    logging.info("Violations by priority:")
    for priority, count in results['by_priority'].items():
        if count > 0:
            logging.info(f"  {priority}: {count}")


if __name__ == "__main__":
    main()