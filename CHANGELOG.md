# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.1.3] - 2026-03-01

### Added
- Unique name validation for MCP tools — all tool names must be distinct across the server
- `validate_tools_have_unique_names()` function to detect duplicate tool names
- `test_tools_have_unique_names` dynamically generated test for MCP servers
- New `duplicate_names_server` mock server for testing duplicate-name failure scenarios
- Integration tests for unique-name validation:
  - `test_tools_have_unique_names_passes_with_basic_server`
  - `test_tools_have_unique_names_fails_with_duplicate_names`

### Changed
- Increased test count from 4 to 5 tests per MCP server endpoint discovery


## [0.1.2] - 2026-02-26

### Added
- Name validation for MCP tools - all tools now must have a non-empty `name` field
- `validate_tools_have_names()` function to validate tool names
- `test_tools_have_names` dynamically generated test for MCP servers
- New `no_names_server` mock server for testing name validation failures
- Integration tests for name validation:
  - `test_tools_have_names_passes_with_basic_server`
  - `test_tools_have_names_fails_without_names`

### Changed
- Increased test count from 3 to 4 tests per MCP server endpoint discovery


## [0.1.1] - Previous Release
- Initial HTTP endpoint detection
- Tool listing and description validation
- Basic test generation

[0.1.3]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/sinan-ozel/pytest-mcp-tools/releases/tag/v0.1.1
