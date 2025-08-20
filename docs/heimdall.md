# Heimdall Integration Requirements for Codex Pattern Collection

## Overview

This document outlines the requirements for extending Heimdall to support GitHub organization scanning and pattern collection for Codex. Heimdall will serve as the unified search and caching layer for all pattern discovery operations.

## Current Heimdall Capabilities

### Existing Features
- **Multi-provider search**: Brave, Serper, SearXNG, DuckDuckGo, GitHub Code Search
- **SQLite caching**: Comprehensive caching with TTL management
- **Async architecture**: High-performance concurrent operations
- **Rich CLI**: Beautiful terminal output and management commands
- **Error handling**: Standardized error categories with fallback

### GitHub Code Provider
- Basic code search via GitHub API
- Authentication support for higher rate limits
- Returns file paths, snippets, and repository metadata

## Requirements for GitHub Organization Scanning

### 1. Organization Discovery API

**New Provider: `GitHubOrgProvider`**

```python
class GitHubOrgProvider:
    """GitHub Organization scanner for pattern collection."""

    async def list_org_repos(org: str) -> List[RepoMetadata]
    async def get_repo_tree(owner: str, repo: str) -> List[FileEntry]
    async def get_file_content(owner: str, repo: str, path: str) -> FileContent
    async def get_files_by_pattern(org: str, patterns: List[str]) -> List[FileResult]
```

### 2. Efficient Scanning Strategy

#### Phase 1: Discovery
- List all repositories in organization
- Filter by: activity, language, size, stars
- Cache repository metadata (30-day TTL)

#### Phase 2: Pattern File Collection
- Target specific files: `pyproject.toml`, `package.json`, `.pre-commit-config.yaml`, etc.
- Use GitHub Trees API for efficient file discovery
- Batch API requests to stay within rate limits

#### Phase 3: Code Pattern Extraction
- Selective file content retrieval via API
- Pattern matching on common files
- Store results in Heimdall's cache

### 3. New Cache Models

```python
class OrganizationCache:
    """Cache for GitHub organization data."""
    org_name: str
    repos: List[RepoMetadata]
    last_scanned: datetime
    total_repos: int
    scan_status: str

class RepoPatternCache:
    """Cache for extracted patterns from repositories."""
    repo_full_name: str
    patterns: Dict[str, Any]
    files_scanned: int
    last_commit_sha: str
    extracted_at: datetime
```

### 4. Rate Limit Management

- **Authenticated**: 5,000 requests/hour
- **GraphQL**: More efficient for bulk operations
- **Request batching**: Group multiple file fetches
- **Smart scheduling**: Prioritize high-value repos

### 5. CLI Commands for Codex Integration

```bash
# Scan entire organization
heimdall github scan-org wtfoss --output patterns.json

# Scan specific file types
heimdall github scan-org wtfoss --files "*.toml,*.json,*.yaml"

# Extract patterns with caching
heimdall github extract-patterns wtfoss --cache-days 7

# Monitor scan progress
heimdall github scan-status wtfoss

# Export for Codex
heimdall github export-patterns wtfoss --format codex
```

### 6. Pattern Extraction Features

#### Target Files
- **Python**: `pyproject.toml`, `setup.py`, `requirements.txt`, `tox.ini`
- **JavaScript**: `package.json`, `tsconfig.json`, `.eslintrc`
- **General**: `.pre-commit-config.yaml`, `.github/workflows/*.yml`
- **Documentation**: `README.md`, `CONTRIBUTING.md`

#### Pattern Types to Extract
- **Dependencies**: Package names and versions
- **Tools**: Linters, formatters, testing frameworks
- **Configurations**: Tool settings and options
- **Scripts**: Common commands and workflows
- **Project Structure**: Directory layouts

### 7. Integration API for Codex

```python
# Heimdall SDK for Codex
from heimdall import GitHubScanner

scanner = GitHubScanner(token="github_token")

# Scan organization
patterns = await scanner.scan_organization(
    org="wtfoss",
    file_patterns=["*.toml", "*.json"],
    cache_days=7,
    parallel_requests=5
)

# Get cached results
cached = await scanner.get_cached_patterns("wtfoss")

# Export for Codex
codex_patterns = await scanner.export_for_codex(patterns)
```

### 8. Performance Requirements

- **Scan 100 repos**: < 30 minutes
- **Cache efficiency**: 90%+ hit rate for repeated scans
- **Memory usage**: < 500MB for large orgs
- **Parallel operations**: 5-10 concurrent API requests
- **Resume capability**: Handle interruptions gracefully

### 9. Data Export Formats

#### Codex Pattern Format
```json
{
  "organization": "wtfoss",
  "scan_date": "2024-01-15",
  "repositories_scanned": 42,
  "patterns": {
    "python": {
      "tools": {
        "ruff": { "frequency": 35, "configs": [...] },
        "mypy": { "frequency": 28, "configs": [...] }
      },
      "dependencies": {
        "pydantic": { "frequency": 40, "versions": [...] }
      }
    }
  }
}
```

### 10. Error Handling & Recovery

- **Rate limit backoff**: Automatic retry with exponential backoff
- **Partial results**: Save progress even if scan incomplete
- **Resume from checkpoint**: Continue interrupted scans
- **Fallback strategies**: Use cached data when API unavailable

## Implementation Priority

1. **Phase 1**: Basic org scanning and repo listing
2. **Phase 2**: File content retrieval and caching
3. **Phase 3**: Pattern extraction logic
4. **Phase 4**: Codex export format
5. **Phase 5**: Advanced features (GraphQL, sparse checkout)

## Success Metrics

- Successfully scan organizations with 100+ repos
- Extract patterns from 90%+ of active repos
- Cache hit rate > 80% for repeated operations
- Complete scan in < 30 minutes for typical org
- Zero data loss from API failures

## Security Considerations

- **Token management**: Secure storage of GitHub tokens
- **Private repos**: Respect visibility settings
- **Sensitive data**: Don't cache secrets or credentials
- **Rate limiting**: Respect GitHub's usage policies

## Resource Manager Interface

### Core Concept

Heimdall provides a resource allocation interface (like malloc/free) for materializing GitHub content to the local filesystem. Clients request resources, receive local filesystem paths, and release them when done.

### Resource Allocation API

```python
class HeimdallResourceManager:
    """Manage temporary local copies of GitHub resources."""

    async def allocate(self, github_path: str, ttl_hours: int = 24) -> Path:
        """
        Allocate a local copy of a GitHub resource.

        Args:
            github_path: "org/repo/path/to/file" or "org/repo/**/*.py"
            ttl_hours: Time-to-live before auto-cleanup (default 24h)

        Returns:
            Path to local file/directory
        """

    async def allocate_many(self, github_paths: List[str]) -> Dict[str, Path]:
        """Allocate multiple resources at once."""

    async def release(self, local_path: Path) -> None:
        """Release allocated resource (mark for cleanup)."""

    async def release_all(self) -> None:
        """Release all allocated resources."""
```

### Resource Tracking

```python
@dataclass
class AllocatedResource:
    """Track allocated resources."""
    github_path: str      # Source path in GitHub
    local_path: Path      # Local filesystem path
    size_bytes: int       # Size on disk
    allocated_at: datetime
    last_accessed: datetime
    ttl_seconds: int = 86400  # Default 24 hours
    client_id: str        # Track who allocated it

    @property
    def is_expired(self) -> bool:
        """Check if resource has exceeded TTL."""
        age = datetime.now() - self.allocated_at
        return age.total_seconds() > self.ttl_seconds
```

### Automatic Cleanup

```python
class ResourceCleaner:
    """Background cleanup of expired resources."""

    async def cleanup_expired(self):
        """Remove resources that exceeded TTL."""
        for resource in self.get_all_allocated():
            if resource.is_expired:
                logger.warning(
                    f"Auto-cleaning expired resource: {resource.local_path} "
                    f"(allocated by {resource.client_id}, age: {resource.age_hours:.1f}h)"
                )
                await self.force_release(resource)
```

### TTL Configuration

- **Default TTL**: 24 hours for most resources
- **Small files** (<1MB): 1 hour TTL
- **Medium repos** (<100MB): 12 hours TTL
- **Large datasets**: Up to 7 days TTL
- **Force cleanup**: After 48 hours regardless of TTL
- **Background check**: Every 5 minutes for expired resources

### Usage Example for Codex

```python
# Simple allocation/deallocation pattern
from heimdall import HeimdallResourceManager

async def analyze_repo():
    rm = HeimdallResourceManager()

    # Allocate - fetches from GitHub if needed, returns local path
    repo_path = await rm.allocate("wtfoss/someproject", ttl_hours=24)

    try:
        # Now use standard filesystem tools
        subprocess.run(["ruff", "check", repo_path])
        subprocess.run(["mypy", repo_path])

        # Process files
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            extract_patterns(pyproject)

    finally:
        # Release when done (or auto-cleanup after TTL)
        await rm.release(repo_path)
```

### CLI Commands for Resource Management

```bash
# Allocate resource with custom TTL
heimdall allocate wtfoss/project --ttl 6h

# Show allocated resources with age
heimdall allocated list
# Output:
# PATH                                    AGE    TTL    CLIENT
# /tmp/heimdall/allocated/wtfoss_proj1/  2.5h   24h    codex-scanner
# /tmp/heimdall/allocated/wtfoss_proj2/  18h    24h    manual-cli
# /tmp/heimdall/allocated/wtfoss_proj3/  25h    24h    [EXPIRED]

# Clean expired resources manually
heimdall cleanup --expired

# Force cleanup of old resources
heimdall cleanup --older-than 12h
```

## Future Enhancements

- **GraphQL optimization**: Use GitHub GraphQL for complex queries
- **Webhook integration**: Real-time updates on repo changes
- **Pattern learning**: ML-based pattern discovery
- **Cross-org analysis**: Compare patterns across organizations
- **Git sparse checkout**: For targeted local analysis of large repos
