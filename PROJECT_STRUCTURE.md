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
