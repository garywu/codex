"""
GitIgnore Handler for Codex

Respects .gitignore patterns and provides smart exclusion logic for scanning.
"""

import os
import re
from pathlib import Path
from re import Pattern as RePattern

from .settings import settings


class GitIgnoreHandler:
    """Handle .gitignore patterns and file exclusion logic."""
    
    # Common patterns that should always be excluded from scanning
    DEFAULT_EXCLUDES = {
        # Version control
        '.git', '.gitignore', '.gitkeep', '.gitattributes',
        
        # Python
        '__pycache__', '*.pyc', '*.pyo', '*.pyd', '.Python',
        'env', 'venv', '.venv', '.env', 'ENV', 'env.bak', 'venv.bak',
        '.pytest_cache', '.mypy_cache', '.coverage', '.tox',
        'pip-log.txt', 'pip-delete-this-directory.txt',
        '.cache', 'htmlcov', '.hypothesis',
        
        # Node.js
        'node_modules', 'npm-debug.log*', 'yarn-debug.log*', 'yarn-error.log*',
        '.npm', '.yarn-integrity', '.pnp.*', '.next',
        
        # Build artifacts
        'build', 'dist', '*.egg-info', '.eggs',
        'target', 'bin', 'obj',
        
        # IDE/Editor
        '.vscode', '.idea', '*.swp', '*.swo', '*~',
        '.DS_Store', settings.database_path,
        
        # Logs and temp files
        '*.log', 'logs', '*.tmp', '*.temp',
        
        # Archives
        '*.zip', '*.tar.gz', '*.rar', '*.7z',
        
        # Media files (usually not code)
        '*.jpg', '*.jpeg', '*.png', '*.gif', '*.svg', '*.ico',
        '*.mp4', '*.avi', '*.mov', '*.mp3', '*.wav',
        
        # Documentation builds
        'docs/_build', 'site-packages', '.readthedocs.yml',
        
        # Database files
        '*.db', '*.sqlite', '*.sqlite3',
        
        # Lock files
        '*.lock', 'Pipfile.lock', 'poetry.lock', 'package-lock.json', 'yarn.lock'
    }
    
    def __init__(self, project_root: Path):
        """Initialize with project root directory."""
        self.project_root = Path(project_root).resolve()
        self.gitignore_patterns: list[str] = []
        self.compiled_patterns: list[RePattern] = []
        self._load_gitignore_patterns()
    
    def _load_gitignore_patterns(self):
        """Load patterns from .gitignore files."""
        # Load from project root .gitignore
        gitignore_file = self.project_root / '.gitignore'
        if gitignore_file.exists():
            self._parse_gitignore_file(gitignore_file)
        
        # Load from parent directories (for nested projects)
        current = self.project_root.parent
        while current != current.parent:  # Stop at filesystem root
            parent_gitignore = current / '.gitignore'
            if parent_gitignore.exists():
                self._parse_gitignore_file(parent_gitignore)
                break  # Only go up one level
            current = current.parent
        
        # Add default excludes
        self.gitignore_patterns.extend(self.DEFAULT_EXCLUDES)
        
        # Compile patterns for faster matching
        self._compile_patterns()
    
    def _parse_gitignore_file(self, gitignore_file: Path):
        """Parse a .gitignore file and extract patterns."""
        try:
            with open(gitignore_file, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Handle negation patterns (lines starting with !)
                    if line.startswith('!'):
                        # TODO: Implement negation support
                        continue
                    
                    self.gitignore_patterns.append(line)
                    
        except (OSError, UnicodeDecodeError) as e:
            # Ignore gitignore files that can't be read
            pass
    
    def _compile_patterns(self):
        """Compile gitignore patterns to regex for faster matching."""
        self.compiled_patterns = []
        
        for pattern in self.gitignore_patterns:
            try:
                # Convert gitignore pattern to regex
                regex_pattern = self._gitignore_to_regex(pattern)
                compiled = re.compile(regex_pattern, re.IGNORECASE)
                self.compiled_patterns.append(compiled)
            except re.error:
                # Skip invalid patterns
                continue
    
    def _gitignore_to_regex(self, pattern: str) -> str:
        """Convert gitignore pattern to regex pattern."""
        # Handle directory patterns (ending with /)
        is_directory = pattern.endswith('/')
        if is_directory:
            pattern = pattern[:-1]
        
        # Escape special regex characters, but preserve gitignore wildcards
        pattern = re.escape(pattern)
        
        # Convert gitignore wildcards to regex
        pattern = pattern.replace(r'\*', '.*')
        pattern = pattern.replace(r'\?', '.')
        
        # Handle directory-specific patterns
        if is_directory:
            pattern = f"{pattern}(/.*)?$"
        else:
            # Match both files and directories
            pattern = f"(^|/){pattern}(/.*)?$"
        
        return pattern
    
    def should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded from scanning."""
        try:
            # Get relative path from project root
            rel_path = file_path.relative_to(self.project_root)
            path_str = str(rel_path).replace('\\', '/')  # Normalize path separators
            
            # Check against compiled patterns
            for pattern in self.compiled_patterns:
                if pattern.search(path_str):
                    return True
            
            # Additional checks for common non-code files
            if self._is_non_code_file(file_path):
                return True
            
            return False
            
        except ValueError:
            # File is outside project root
            return True
    
    def _is_non_code_file(self, file_path: Path) -> bool:
        """Check if file is typically not a code file."""
        suffix = file_path.suffix.lower()
        
        # Binary/media files
        binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.jar', '.war',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.ico',
            '.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.dmg', '.iso'
        }
        
        return suffix in binary_extensions
    
    def get_scannable_files(self, directory: Path, extensions: set[str] = None) -> list[Path]:
        """Get list of files that should be scanned."""
        if extensions is None:
            # Default to common code file extensions
            extensions = {
                '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
                '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
                '.sh', '.bash', '.zsh', '.ps1', '.yaml', '.yml', '.json', '.toml',
                '.xml', '.html', '.css', '.scss', '.less', '.sql', '.r', '.m',
                '.dockerfile', '.tf', '.hcl'
            }
        
        scannable_files = []
        
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            
            # Filter out excluded directories in-place
            dirs[:] = [d for d in dirs if not self.should_exclude(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                
                # Skip if excluded
                if self.should_exclude(file_path):
                    continue
                
                # Skip if not a code file (unless no extension filter)
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                
                scannable_files.append(file_path)
        
        return scannable_files
    
    def validate_gitignore(self) -> list[str]:
        """Validate .gitignore file and return suggestions."""
        suggestions = []
        gitignore_file = self.project_root / '.gitignore'
        
        if not gitignore_file.exists():
            suggestions.append("No .gitignore file found. Consider creating one.")
            return suggestions
        
        try:
            with open(gitignore_file, encoding='utf-8') as f:
                content = f.read()
            
            # Check for common missing patterns
            missing_patterns = []
            
            recommended_patterns = {
                '__pycache__/': 'Python bytecode cache',
                '*.pyc': 'Python compiled files',
                '.venv/': 'Python virtual environment',
                'venv/': 'Python virtual environment (alternative)',
                '.env': 'Environment variables file',
                'node_modules/': 'Node.js dependencies',
                '.DS_Store': 'macOS system files',
                '*.log': 'Log files',
                '.coverage': 'Python coverage reports',
                '.pytest_cache/': 'Pytest cache',
                '.mypy_cache/': 'MyPy cache'
            }
            
            for pattern, description in recommended_patterns.items():
                if pattern not in content:
                    missing_patterns.append(f"Consider adding '{pattern}' for {description}")
            
            if missing_patterns:
                suggestions.append("Missing recommended patterns:")
                suggestions.extend(missing_patterns)
            
            # Check for overly broad patterns
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line == '*':
                    suggestions.append(f"Line {line_num}: Pattern '*' is too broad and will exclude everything")
                elif line == '**':
                    suggestions.append(f"Line {line_num}: Pattern '**' is too broad")
            
        except (OSError, UnicodeDecodeError):
            suggestions.append("Could not read .gitignore file")
        
        return suggestions
    
    def get_patterns_summary(self) -> dict:
        """Get summary of loaded patterns for debugging."""
        return {
            'total_patterns': len(self.gitignore_patterns),
            'compiled_patterns': len(self.compiled_patterns),
            'project_root': str(self.project_root),
            'gitignore_exists': (self.project_root / '.gitignore').exists(),
            'sample_patterns': self.gitignore_patterns[:10]  # First 10 for debugging
        }