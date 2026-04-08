## Why

Phase 1 provides the core SQL Unit testing capabilities. Phase 2's CLI provides a command-line interface for running tests, making the tool accessible for developers and CI/CD pipelines. The CLI enables test discovery, filtering, and verbose output for debugging.

## What Changes

- **CLI entry point** - Command-line interface for test execution
- **list command** - Discover and list all available SQL unit tests
- **run command** - Execute SQL unit tests with optional filtering
- **Output formatting** - JSON and human-readable output modes
- **Exit codes** - Proper exit codes for CI/CD integration

## Capabilities

### New Capabilities

- `cli-list`: List available SQL unit tests with filtering by directory, test name, or tags
- `cli-run`: Execute SQL unit tests with options for filtering, parallel execution, and output formatting

## Impact

- **Developer experience** - Simple command-line tool for running tests locally
- **CI/CD integration** - Proper exit codes and machine-readable output for automated testing
- **Test discovery** - Easy visibility into available tests
- **Debug output** - Verbose mode for troubleshooting test failures
