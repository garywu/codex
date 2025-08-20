#!/bin/bash
# Codex Project Organization Cleanup Script
# This script reorganizes the project structure to follow best practices

set -e  # Exit on error

echo "🧹 Codex Project Organization Cleanup"
echo "======================================"
echo ""

# Create standard directories
echo "📁 Creating standard project directories..."
mkdir -p tests
mkdir -p docs
mkdir -p examples
mkdir -p scripts
mkdir -p experiments

# Move test files to tests/
echo "🧪 Moving test files to tests/..."
for file in test_*.py; do
    if [ -f "$file" ]; then
        echo "  Moving $file to tests/"
        mv "$file" tests/
    fi
done

# Move documentation to docs/
echo "📚 Moving documentation to docs/..."
for file in *.md; do
    if [ -f "$file" ] && [ "$file" != "README.md" ]; then
        echo "  Moving $file to docs/"
        mv "$file" docs/
    fi
done

# Move demo files to examples/
echo "📝 Moving demo/example files to examples/..."
for file in demo_*.py example_*.py; do
    if [ -f "$file" ]; then
        echo "  Moving $file to examples/"
        mv "$file" examples/
    fi
done

# Move experimental scanners and fixers
echo "🔬 Moving experimental implementations to experiments/..."
for file in intelligent_scanner.py smart_scanner.py enhanced_intelligent_scanner.py \
           final_intelligent_scanner.py best_practices_scanner.py broader_scope_scanner.py \
           detailed_violation_scanner.py simple_scanner.py \
           intelligent_fixer.py comprehensive_fixer.py simple_fixer.py; do
    if [ -f "$file" ]; then
        echo "  Moving $file to experiments/"
        mv "$file" experiments/
    fi
done

# Move utility scripts
echo "🔧 Moving utility scripts to scripts/..."
for file in import_patterns*.py update_patterns*.py extract_*.py; do
    if [ -f "$file" ]; then
        echo "  Moving $file to scripts/"
        mv "$file" scripts/
    fi
done

# Move analyzer tools to experiments/
echo "🔍 Moving analyzers to experiments/..."
for file in *_analyzer.py; do
    if [ -f "$file" ]; then
        echo "  Moving $file to experiments/"
        mv "$file" experiments/
    fi
done

# Move pattern JSON files to data directory
echo "📊 Organizing data files..."
mkdir -p data
for file in *.json; do
    if [ -f "$file" ] && [[ "$file" == *"pattern"* ]]; then
        echo "  Moving $file to data/"
        mv "$file" data/
    fi
done

# Clean up old/deprecated files
echo "🗑️  Removing old/deprecated files..."
for file in *_OLD.py *_DEPRECATED.py *.bak *.tmp; do
    if [ -f "$file" ]; then
        echo "  Removing $file"
        rm "$file"
    fi
done

# Remove backup directories
echo "🗑️  Removing backup directories..."
for dir in *_backup_*; do
    if [ -d "$dir" ]; then
        echo "  Removing backup directory: $dir"
        rm -rf "$dir"
    fi
done

# Remove build artifacts
echo "🗑️  Removing build artifacts..."
if [ -d "build" ]; then
    echo "  Removing build/"
    rm -rf build
fi
if [ -d "codex.egg-info" ]; then
    echo "  Removing codex.egg-info/"
    rm -rf codex.egg-info
fi

# Move remaining Python files that don't belong in root
echo "📦 Organizing remaining Python files..."
for file in *.py; do
    if [ -f "$file" ]; then
        # Skip setup.py if it exists
        if [ "$file" == "setup.py" ]; then
            continue
        fi

        # Categorize and move
        if [[ "$file" == *"scanner"* ]] || [[ "$file" == *"fixer"* ]]; then
            echo "  Moving $file to experiments/"
            mv "$file" experiments/
        elif [[ "$file" == *"test"* ]]; then
            echo "  Moving $file to tests/"
            mv "$file" tests/
        else
            echo "  Moving $file to scripts/"
            mv "$file" scripts/
        fi
    fi
done

# Create a project structure file
echo "📝 Creating project structure documentation..."
cat > PROJECT_STRUCTURE.md << 'EOF'
# Codex Project Structure

After cleanup, the project follows this standard structure:

```
codex/
├── codex/              # Main package source code
├── tests/              # All test files
├── docs/               # Documentation
├── examples/           # Example usage and demos
├── scripts/            # Utility scripts
├── experiments/        # Experimental implementations
├── data/               # Data files (patterns, etc.)
├── config/             # Configuration files
├── fixers/             # Specialized fixers
├── .codex.toml         # Project configuration
├── pyproject.toml      # Build configuration
└── README.md           # Main documentation
```

## Directory Purposes

- **codex/**: Production code only
- **tests/**: All test files (test_*.py)
- **docs/**: All markdown documentation except README
- **examples/**: Demo scripts and usage examples
- **scripts/**: Utility and migration scripts
- **experiments/**: Experimental implementations (to be consolidated)
- **data/**: JSON patterns and data files
- **config/**: Configuration templates
- **fixers/**: Specialized fixer implementations
EOF

echo ""
echo "✅ Cleanup Complete!"
echo ""
echo "📊 Summary:"
echo "  - Created standard project directories"
echo "  - Moved test files to tests/"
echo "  - Moved documentation to docs/"
echo "  - Moved demos to examples/"
echo "  - Moved experiments to experiments/"
echo "  - Removed backup directories"
echo "  - Removed build artifacts"
echo "  - Created PROJECT_STRUCTURE.md"
echo ""
echo "⚠️  Note: Review the experiments/ directory to consolidate duplicate implementations"
echo ""
echo "Run 'python -m codex.organization_scanner' to verify the cleanup"
