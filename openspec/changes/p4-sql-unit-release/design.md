## Context

Building on Phases 1-4 (complete, tested, documented sql-unit), Phase 4's Release prepares the project for public distribution. This phase handles version management, PyPI publishing, release automation, and community announcement.

Key constraints:
- Depends on Phases 1-4 Complete
- Must follow semantic versioning
- Must automate release process via CI/CD
- Must publish to PyPI
- Must maintain release history and changelog
- Must support rollback/yanking if needed

## Goals / Non-Goals

**Goals:**
- Semantic versioning (MAJOR.MINOR.PATCH)
- Changelog/release notes
- PyPI package publishing
- GitHub releases
- Release automation via CI/CD
- Version bumping process
- Public announcement

**Non-Goals:**
- Multiple simultaneous versions (support current + 1 back)
- Security vulnerability disclosure process (separate)
- Long-term maintenance strategy (separate governance)

## Decisions

### Decision 1: Versioning Scheme

**Choice**: Semantic versioning (MAJOR.MINOR.PATCH)

**Rationale**:
- Industry standard
- Clear communication of change impact
- Compatible with package managers
- Tools support it well

**Alternatives considered**:
- Date-based versioning → Less meaning, confusing for dependencies
- Calendar versioning → Similar issues
- Single number → Not enough granularity

### Decision 2: Changelog Format

**Choice**: Keep a CHANGELOG.md file in Keep a Changelog format

**Rationale**:
- Standard format recognized by community
- Human and machine-readable
- Good for git diffs and version control
- Tools exist to help maintain it

**Alternatives considered**:
- Auto-generate from commit messages → Less curated
- Release notes only → Hard to see full history
- No changelog → Bad practice

### Decision 3: PyPI Publishing

**Choice**: Publish via GitHub Actions and PyPI API token

**Rationale**:
- Automated, no manual steps
- Secure token-based authentication
- Audit trail in CI/CD logs
- One-click release from GitHub

**Alternatives considered**:
- Manual publishing → Error-prone, requires credentials locally
- Manually creating GitHub release then publishing → Extra steps

### Decision 4: Optional Dependencies Publishing

**Choice**: Publish with optional dependencies (extras) for each backend

**Rationale**:
- pyproject.toml supports optional-dependencies for feature flags
- Users can install `sql-unit[sqlite]`, `sql-unit[mysql]`, etc.
- Base package remains lightweight
- All optional dependencies defined in one pyproject.toml

**Expected pyproject.toml structure:**
```toml
[project.optional-dependencies]
sqlite = ["<sqlite-driver-package>"]
mysql = ["pymysql"]
postgresql = ["psycopg2-binary"]
duckdb = ["duckdb"]
all = ["sql-unit[sqlite]", "sql-unit[mysql]", "sql-unit[postgresql]", "sql-unit[duckdb]"]
```

**Alternatives considered**:
- Separate packages per backend → Complicated installation, fragmented ecosystem
- All drivers in base → Bloated installation
- No extras → Users must install drivers manually

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Publishing errors** → Broken or incomplete package | Test publishing process; verify package contents; use test PyPI first |
| **Accidental major version bump** → Breaking changes marked minor | Careful review of changes before release |
| **Cannot undo published version** → Version published but has issues | Yank version from PyPI; publish patch; communicate issue |
| **Secrets exposure** → PyPI token leaked | Use GitHub secrets; rotate tokens regularly; monitor for misuse |

## Migration Plan

Phase 4 Release:
1. Setup version management in pyproject.toml
2. Create CHANGELOG.md (Keep a Changelog format)
3. Document release process
4. Setup GitHub Actions release workflow
5. Test release process (publish to test PyPI)
6. Create release checklist
7. Create first release (v1.0.0)
8. Setup release automation
9. Create announcement template

## Open Questions

- Should maintenance releases (0.x) continue after 1.0?
- Should release branches (release/1.x) be created for critical patches?
- How long to support previous major versions?
- Should pre-releases (alpha, beta, rc) be published to PyPI or test PyPI only?
