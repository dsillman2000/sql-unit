# Tasks for p4-sql-unit-release

## Prerequisite: Phase 1, Phase 2, Phase 3, and Phase 4's Documentation Complete
- All Phase 1, Phase 2, Phase 3 changes must be complete
- p4-sql-unit-documentation must be complete

## Version Management

### Semantic Versioning Setup
- [ ] Define version in single source of truth
  - Update pyproject.toml with version field
  - Document version location
- [ ] Document versioning policy
  - MAJOR version: incompatible API changes
  - MINOR version: new features (backwards compatible)
  - PATCH version: bug fixes (backwards compatible)
  - Examples of each
- [ ] Create version bumping procedure
  - How to bump major version
  - How to bump minor version
  - How to bump patch version
  - Automation (optional)

### First Release Preparation
- [ ] Determine first release version
  - v0.1.0 (pre-release) or v1.0.0?
  - Document decision
- [ ] Finalize API and features
  - No breaking changes after first release
  - Feature complete for 1.0.0
  - Review API for stability
- [ ] Document breaking changes
  - List any known limitations
  - Document workarounds

## Changelog Management

### CHANGELOG.md Creation
- [ ] Create CHANGELOG.md file
  - Follow "Keep a Changelog" format
  - Include unreleased section
  - Include version sections with dates
  - Link to release tags
- [ ] Document changelog format
  - Added section (new features)
  - Changed section (changes)
  - Deprecated section (deprecations)
  - Removed section (removals)
  - Fixed section (bug fixes)
  - Security section (security fixes)
- [ ] Populate initial changelog
  - Document Phase 1 features
  - Document Phase 2 features
  - Document Phase 3 changes
  - Document Phase 4 changes

### Changelog Maintenance Process
- [ ] Document changelog update procedure
  - Update with each feature/fix
  - Keep "Unreleased" section updated
  - Link to pull requests
  - Include contributor names (optional)
- [ ] Create template for changelog entries
  - How to describe changes
  - How to link PRs/issues
  - Level of detail

## Release Notes

### Release Notes Template
- [ ] Create release notes template
  - Highlight major features
  - List breaking changes
  - Provide upgrade instructions
  - Thank contributors
  - Link to documentation
- [ ] Document release notes process
  - When to create release notes
  - How to write release notes
  - Approval process

### Release Notes Examples
- [ ] Create example release notes for 1.0.0
- [ ] Create example release notes for 1.1.0 (minor)
- [ ] Create example release notes for 1.0.1 (patch)
- [ ] Document release notes locations
  - GitHub releases
  - PyPI release page
  - Announcement blog post

## PyPI Publishing

### PyPI Configuration
- [ ] Create PyPI account (if not exists)
- [ ] Create API token on PyPI
  - Generate token for publishing
  - Store as GitHub secret
  - Document token rotation policy
- [ ] Configure pyproject.toml
  - Verify package metadata complete
  - Add project name, description, version
  - Add author information
  - Add license information
  - Add keywords/classifiers
  - Add project URLs
  - Add dependencies
  - Add development dependencies
  - Add Python version requirement
- [ ] Create setup.cfg or pyproject.toml with build config
  - Build tool configuration
  - Package discovery
  - Include/exclude patterns

### Package Contents Verification
- [ ] Verify package includes all necessary files
  - Source code
  - License file
  - Changelog
  - README
  - pyproject.toml
- [ ] Verify package excludes unwanted files
  - .git directory
  - __pycache__ directories
  - .env files
  - Test databases
  - CI/CD files
- [ ] Create MANIFEST.in if needed
  - Include non-Python files
  - Exclude test databases
  - Exclude temporary files

### Local Package Building
- [ ] Setup build tools
  - Install build, twine
  - Document build process
- [ ] Build distribution packages
  - Create wheel (.whl file)
  - Create source distribution (.tar.gz)
  - Verify build succeeds locally
- [ ] Test package locally
  - Install from wheel
  - Run basic smoke tests
  - Verify CLI works
- [ ] Verify package contents
  - List files in wheel
  - Verify version correct
  - Verify metadata correct

### Test PyPI Publishing
- [ ] Create test PyPI account
- [ ] Configure test PyPI in .pypirc
- [ ] Upload to test PyPI
  - Use twine upload
  - Verify upload succeeds
- [ ] Test installation from test PyPI
  - Install from test PyPI
  - Run smoke tests
  - Verify all features work

### Production PyPI Publishing
- [ ] Create release process documentation
  - Prerequisite checks (all tests pass, changelog updated, etc.)
  - Build command
  - Publish command
  - Verify publication
- [ ] Document deployment checklist
  - All changes merged and tested
  - Version bumped
  - Changelog updated
  - Release notes written
  - GitHub release created
  - Documentation updated
- [ ] Implement publishing automation (optional)
  - GitHub Actions workflow
  - Trigger on git tag
  - Build and publish automatically
  - Verify publication
  - Create GitHub release

## GitHub Releases

### GitHub Release Automation
- [ ] Create GitHub Actions workflow
  - Trigger on version tag (v*.*.*)
  - Build distributions
  - Upload to GitHub releases
  - Create release notes
- [ ] Test release workflow
  - Create test tag
  - Verify workflow triggers
  - Verify artifacts uploaded
  - Verify release created
  - Clean up test release

### Release Checklist Automation
- [ ] Create release checklist document
  - All tests pass
  - Coverage is adequate
  - Changelog updated
  - Version bumped
  - Documentation updated
  - No security issues
  - No open breaking-change issues
- [ ] Automate checklist validation where possible
  - CI/CD checks
  - Linting
  - Security scanning

## Release Automation

### GitHub Actions Workflow
- [ ] Create release workflow
  - Trigger: push tag matching v*.*.* or manual workflow dispatch
  - Steps:
    1. Checkout code
    2. Setup Python
    3. Install dependencies
    4. Run full test suite
    5. Build distributions
    6. Upload to PyPI (or test PyPI)
    7. Create GitHub release with notes
    8. Publish documentation (if changed)
- [ ] Document workflow
  - When it triggers
  - What it does
  - How to trigger manually
  - How to debug failures
- [ ] Test workflow end-to-end
  - Create test release
  - Verify all steps succeed
  - Verify package on PyPI
  - Verify GitHub release
  - Clean up (yank from test PyPI)

### Release Secrets Management
- [ ] Configure GitHub secrets
  - PYPI_API_TOKEN
  - TEST_PYPI_API_TOKEN
  - GITHUB_TOKEN (auto-provided)
- [ ] Document secrets
  - What each is used for
  - How to rotate
  - Expiration dates
- [ ] Setup monitoring
  - Alert on token usage
  - Alert on publish failures

## Public Announcement

### Announcement Preparation
- [ ] Create announcement template
  - Project name, version
  - Key features
  - Link to docs
  - Link to PyPI
  - Link to GitHub
- [ ] Prepare announcements for different audiences
  - Twitter/social media
  - Reddit
  - Hacker News
  - Dev.to
  - Internal channels

### Social Media Announcements
- [ ] Write Twitter announcement
  - Highlight key features
  - Include link to PyPI/docs
  - Use relevant hashtags
  - Tag contributors
- [ ] Write Reddit posts (r/Python, r/SQL, etc.)
  - Explain what sql-unit is
  - Show use case
  - Link to documentation
  - Encourage feedback
- [ ] Create Hacker News post (optional)
  - Focus on novel aspects
  - Encourage community discussion

### Community Announcements
- [ ] Create Dev.to article (optional)
  - Tutorial or overview
  - Link to full documentation
- [ ] Post in relevant communities
  - Python communities
  - SQL communities
  - Database communities
- [ ] Announce in issue/discussion (if applicable)
  - Update status
  - Thank contributors
  - Link to release

## Post-Release

### Release Verification
- [ ] Verify package on PyPI
  - Check package page
  - Check version correct
  - Check metadata correct
  - Check documentation link
- [ ] Verify installation
  - Install from PyPI in clean environment
  - Run basic smoke tests
  - Verify CLI works
  - Verify all features accessible
- [ ] Verify GitHub release
  - Release created
  - Release notes present
  - Assets/distributions attached
  - Correct version tag

### Issue & Feedback Monitoring
- [ ] Monitor for post-release issues
  - Check GitHub issues
  - Check PyPI comments
  - Check social media mentions
- [ ] Have rollback plan ready
  - Yank problematic version if needed
  - Publish patch version
  - Communicate issue and fix

### Retrospective
- [ ] Document what went well
- [ ] Document what could be improved
- [ ] Update release process based on learnings
- [ ] Update documentation if needed

## Documentation Updates

### Release Documentation
- [ ] Update README.md
  - Installation instructions
  - Link to documentation
  - Link to PyPI
  - Updated feature list
- [ ] Update CONTRIBUTING.md
  - How to contribute
  - Release process (for core team)
- [ ] Update documentation site
  - Update version
  - Announce release
  - Highlight changes
- [ ] Create version-specific docs (optional)
  - Archive old version docs
  - Keep current version prominent

## Long-Term Maintenance

### Version Support Policy
- [ ] Document version support policy
  - How long versions are supported
  - When to upgrade
  - How to report security issues
- [ ] Backport policy
  - Which fixes backported to previous versions
  - Which versions receive backports

### Dependency Management
- [ ] Monitor dependencies for updates
  - Security updates
  - Major version updates
  - Deprecation warnings
- [ ] Update dependencies regularly
  - Update policy
  - Testing before/after
  - Communicate in changelog

### Maintenance Releases
- [ ] Document patch release process
  - Cherry-pick fixes
  - Test on affected versions
  - Fast-track review
  - Immediate publication
