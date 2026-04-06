## Context

Building on Phases 1-3 (complete, tested sql-unit implementation), Phase 4 creates comprehensive documentation for users. The mkdocs-based documentation site makes sql-unit discoverable, learnable, and usable for developers and teams.

Key constraints:
- Depends on Phases 1-3 Complete
- Must cover all features and capabilities
- Must include practical examples
- Must be easy to navigate and search
- Must be maintainable as project evolves
- Should be published to public URL (GitHub Pages, etc.)

## Goals / Non-Goals

**Goals:**
- Getting started guide for new users
- Detailed documentation for all features
- API reference (auto-generated from docstrings)
- Real-world examples and tutorials
- Database-specific setup guides
- Troubleshooting and FAQ sections
- Best practices and design patterns
- Professional, accessible site design

**Non-Goals:**
- Video tutorials (text-based docs only)
- Interactive code playground
- Community forum/discussion (GitHub Issues)
- API versioning documentation (single version)

## Decisions

### Decision 1: Documentation Framework

**Choice**: Use mkdocs for documentation

**Rationale**:
- Simple Markdown-based docs
- Built-in material theme looks professional
- Easy to customize
- Good search functionality
- Supports versioning if needed later
- Easy to deploy to GitHub Pages

**Alternatives considered**:
- Sphinx → More complex; oriented toward Python packages
- Docusaurus → Requires Node.js; overkill for current needs
- Static HTML → No build tooling; harder to maintain

### Decision 2: Documentation Organization

**Choice**: Hierarchical structure with main sections

**Rationale**:
- Clear logical flow for users
- Easy to navigate
- Supports different user levels (beginner to advanced)

**Alternatives considered**:
- Flat structure → Confusing with many pages
- Single long page → Not searchable; hard to skim

### Decision 3: API Reference

**Choice**: Auto-generate from docstrings using pdoc or sphinx

**Rationale**:
- Stays in sync with code
- No duplication
- Single source of truth

**Alternatives considered**:
- Manual documentation → High maintenance burden
- Inline code documentation → Not suitable for full site

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Docs lag behind code** → Features added but not documented | Require docs update as part of PR review; include in release checklist |
| **Too much detail** → Site becomes hard to navigate | Organize hierarchically; distinguish beginner vs. advanced content |
| **Examples become outdated** → Examples don't work with new version | Regular testing of examples; include version compatibility notes |

## Migration Plan

Phase 4 Documentation:
1. Setup mkdocs project
2. Create site structure and navigation
3. Write getting started guide
4. Write feature documentation
5. Create examples and tutorials
6. Setup auto-generated API reference
7. Write database setup guides
8. Write troubleshooting section
9. Create contributing guide
10. Setup GitHub Pages deployment
11. Publish and promote

## Open Questions

- Should documentation support multiple language translations?
- Should old versions of documentation be kept accessible?
- Where should documentation be deployed (GitHub Pages, Read the Docs, custom domain)?
- Should documentation include blog/changelog or just reference docs?
