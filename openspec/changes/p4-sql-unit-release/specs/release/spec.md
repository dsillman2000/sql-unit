## ADDED Requirements

### Requirement: Semantic versioning
The system SHALL follow semantic versioning (MAJOR.MINOR.PATCH).

#### Scenario: Major version increment
- **WHEN** breaking changes are made to API
- **THEN** major version is incremented (e.g., 1.0.0 → 2.0.0)

#### Scenario: Minor version increment
- **WHEN** new features are added (backwards compatible)
- **THEN** minor version is incremented (e.g., 1.0.0 → 1.1.0)

#### Scenario: Patch version increment
- **WHEN** bug fixes are released
- **THEN** patch version is incremented (e.g., 1.0.0 → 1.0.1)

#### Scenario: Pre-release version
- **WHEN** alpha/beta releases are needed
- **THEN** version includes pre-release suffix (e.g., 1.0.0-alpha.1)

#### Scenario: Version in package metadata
- **WHEN** package is built
- **THEN** version from pyproject.toml is used consistently

### Requirement: Changelog management
The system SHALL maintain a CHANGELOG.md file.

#### Scenario: Changelog format
- **WHEN** CHANGELOG.md is viewed
- **THEN** it follows "Keep a Changelog" format with Added/Changed/Removed/Fixed sections

#### Scenario: Unreleased section
- **WHEN** changes are made
- **THEN** changes are added to Unreleased section

#### Scenario: Release section creation
- **WHEN** release is created
- **THEN** Unreleased section becomes versioned section with date

#### Scenario: Changelog entry examples
- **WHEN** changelog is read
- **THEN** entries clearly describe changes with issue/PR references

### Requirement: Release notes generation
The system SHALL generate release notes for each release.

#### Scenario: Release notes content
- **WHEN** release is published
- **THEN** release notes include summary of major features/fixes

#### Scenario: Breaking changes documentation
- **WHEN** breaking changes are released
- **THEN** release notes clearly highlight and explain migration path

#### Scenario: Release notes publish location
- **WHEN** release is created
- **THEN** release notes are published on GitHub Releases page

### Requirement: PyPI package publishing
The system SHALL publish releases to Python Package Index.

#### Scenario: Package metadata completeness
- **WHEN** package is built
- **THEN** pyproject.toml includes name, description, version, author, license

#### Scenario: Distribution package building
- **WHEN** release is prepared
- **THEN** wheel and source distributions are built successfully

#### Scenario: PyPI upload
- **WHEN** release is ready
- **THEN** distributions are uploaded to PyPI

#### Scenario: Installation from PyPI
- **WHEN** user runs `pip install sql-unit`
- **THEN** package is installed from PyPI with all dependencies

#### Scenario: Package verification
- **WHEN** package is published
- **THEN** PyPI package page shows correct version, metadata, and documentation link

#### Scenario: Test PyPI verification
- **WHEN** release is being prepared
- **THEN** package is first tested on Test PyPI before production upload

### Requirement: Release automation via CI/CD
The system SHALL automate release process through GitHub Actions.

#### Scenario: Release trigger on version tag
- **WHEN** git tag matching v*.*.* is pushed
- **THEN** CI/CD workflow is triggered

#### Scenario: Release workflow steps
- **WHEN** release workflow runs
- **THEN** it runs tests, builds distributions, uploads to PyPI, creates GitHub release

#### Scenario: Release verification
- **WHEN** release workflow completes
- **THEN** package is verified available on PyPI

#### Scenario: Release workflow failure
- **WHEN** release workflow fails (tests fail, upload fails)
- **THEN** workflow stops and logs error details

#### Scenario: Release rollback capability
- **WHEN** released package has critical issue
- **THEN** system can yank version from PyPI and release patch

### Requirement: GitHub releases
The system SHALL create GitHub releases with artifacts.

#### Scenario: GitHub release creation
- **WHEN** version is tagged and pushed
- **THEN** GitHub release is automatically created

#### Scenario: Release download artifacts
- **WHEN** GitHub release is viewed
- **THEN** wheel and source distributions are available as downloads

#### Scenario: Release notes in GitHub
- **WHEN** release is created
- **THEN** release notes from CHANGELOG are included in GitHub release

### Requirement: Release checklist
The system SHALL document pre-release validation steps.

#### Scenario: All tests pass
- **WHEN** release is prepared
- **THEN** full test suite passes on all supported Python versions

#### Scenario: Code coverage adequate
- **WHEN** release is prepared
- **THEN** code coverage is >= 90%

#### Scenario: Documentation updated
- **WHEN** release is prepared
- **THEN** documentation is updated for new features/changes

#### Scenario: Changelog updated
- **WHEN** release is prepared
- **THEN** CHANGELOG.md Unreleased section is populated

#### Scenario: No security issues
- **WHEN** release is prepared
- **THEN** security scanning finds no vulnerabilities

#### Scenario: Dependencies compatible
- **WHEN** release is prepared
- **THEN** all dependencies have compatible versions (no conflicts)

### Requirement: Version support policy
The system SHALL clearly communicate version support.

#### Scenario: Current version support
- **WHEN** release is made
- **THEN** current version receives bug fixes and security updates

#### Scenario: Previous version support
- **WHEN** new major version is released
- **THEN** previous major version receives critical security fixes only

#### Scenario: End of life announcement
- **WHEN** version reaches end of support
- **THEN** users are notified with clear timeline
