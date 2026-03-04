# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.1.4] - 2026-03-04

### Added
- `outputSchema` field validation for MCP tools:
  - Per-tool `test_{tool}_output_schema_field_descriptions` — checks every
    `outputSchema` property (recursively) has a non-empty `description`
  - Per-tool `test_{tool}_output_schema_field_types` — checks every
    `outputSchema` property has a valid JSON Schema primitive `type`
  - Both tests are generated only when a tool declares `outputSchema.properties`;
    `outputSchema` is optional and its absence is not flagged by default
  - New `--mcp-tools-enforce-output-schema` CLI flag: when set, generates a
    failing `test_{tool}_output_schema_present` for every tool missing an
    `outputSchema`
- Three new mock servers for `outputSchema` testing:
  - `output_schema_server` — tool with a well-formed `outputSchema`
  - `output_schema_no_descriptions_server` — tool whose `outputSchema` fields
    lack `description`
  - `output_schema_invalid_types_server` — tool whose `outputSchema` fields
    use invalid or missing `type`
- Integration tests covering all `outputSchema` validation scenarios:
  - `test_output_schema_field_descriptions_passes_with_output_schema_server`
  - `test_output_schema_field_types_passes_with_output_schema_server`
  - `test_output_schema_field_descriptions_fails_without_descriptions`
  - `test_output_schema_field_types_fails_with_invalid_types`
  - `test_output_schema_not_enforced_by_default`
  - `test_output_schema_enforced_with_flag_fails`
- `inputSchema` field validation for MCP tools (per-tool, recursive):
  - Per-tool `test_{tool}_input_schema_field_descriptions`
  - Per-tool `test_{tool}_input_schema_field_types`
  - New marker `mcp_tools_input_schema` for these tests (excluded from the
    `created N tests` count for backward compatibility)
  - New marker `mcp_tools_output_schema` for `outputSchema` tests
- New mock servers for `inputSchema` testing:
  - `no_field_descriptions_server`, `invalid_field_types_server`,
    `deeply_nested_server`, `deeply_nested_invalid_type_server`
- Annotation validation for MCP tools:
  - `validate_tools_have_titles()` — checks that every tool with an
    `annotations` field includes a non-empty `title`
  - `validate_tool_annotations_are_consistent()` — checks that
    `readOnlyHint` is not `True` when `destructiveHint` or `idempotentHint`
    is also `True`
  - `test_tools_have_titles` dynamically generated test (only emitted when
    at least one tool has an `annotations` field)
  - `test_tool_annotations_are_consistent` dynamically generated test
    (only emitted when at least one tool has an `annotations` field)
- Three new mock servers for annotation testing:
  - `annotations_server` — tools with proper annotations (passing case)
  - `no_titles_server` — tools missing `title` in annotations
  - `conflicting_annotations_server` — tools with `readOnlyHint=True` and
    `destructiveHint=True` or `idempotentHint=True`
- Integration tests covering all four annotation validation scenarios
- Restored `validate_tools_have_names()` and `test_tools_have_names` to
  the HTTP-only test path (regression fix from STDIO refactor)
- Restored `test_tools_have_unique_names` to the HTTP-only test path

### Fixed
- `validate_tools_have_names` and its generated test were missing from the
  HTTP-only branch of the plugin after the STDIO support refactor
- `test_tools_have_unique_names` was only generated for hybrid
  (HTTP + STDIO) servers; now generated for all servers with HTTP endpoints

### Changed
- `test_tools_have_unique_names` moved from STDIO+HTTP branch to the
  HTTP-only branch so it runs regardless of STDIO availability


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

[0.1.4]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/sinan-ozel/pytest-mcp-tools/releases/tag/v0.1.1
