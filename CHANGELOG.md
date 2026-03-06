# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.1.6] - 2026-03-05

### Changed
- **Examples read from `inputSchema.examples`** — the plugin now reads per-tool
  examples from `tool["inputSchema"]["examples"]` (standard JSON Schema location)
  instead of `tool["examples"]` (non-standard tool-level key). Each example is a
  plain dict of input arguments rather than a `{"input": {...}}` wrapper. This
  aligns with the JSON Schema specification and real-world MCP server behaviour.
- **All mock servers updated** — the six test servers
  (`examples_server`, `output_schema_type_error_server`,
  `read_only_examples_server`, `example_missing_required_server`,
  `example_wrong_type_server`, `example_wrong_format_server`) have had their
  examples moved from the tool level into `inputSchema.examples` with the plain
  dict format.
- **`--mcp-tools-strict` `has_examples` check updated** — strict-mode now
  checks `inputSchema.examples` for presence of at least one example.
- **Documentation updated** — `docs/index.md` now shows the correct
  `inputSchema.examples` format in the feature table, section descriptions, and
  JSON example snippet.


## [0.1.5] - 2026-03-05

### Added
- **Example input validation** — before calling a tool with an example, the
  plugin now validates the example's `input` against the tool's `inputSchema`:
  - All fields listed in `required` must be present; missing required fields
    cause the generated test to fail immediately (no network call is made).
  - Every provided field value must match the declared JSON Schema `type`
    (`string`, `integer`, `number`, `boolean`, `array`, `object`, `null`).
  - String fields with a `format` keyword (`email`, `uri`, `date`, `date-time`,
    `time`) must match the expected pattern.
  - Failure messages clearly identify which field violated which constraint
    (`missing required field`, `type`, or `format`), satisfying the test
    assertions in the integration suite.
- **`collect_example_input_violations()` helper** — new public function that
  implements the input-validation logic and returns a list of violation strings.
- **`_FORMAT_VALIDATORS` dict** — maps JSON Schema `format` keywords to
  compiled regex patterns used by `collect_example_input_violations`.
- **Three new mock servers** for the integration test suite:
  - `example_missing_required_server` — `send_message` tool whose example
    omits the required `recipient` field.
  - `example_wrong_type_server` — `set_count` tool whose example supplies the
    string `"five"` for an `integer`-typed field.
  - `example_wrong_format_server` — `notify_user` tool whose example supplies
    `"not-an-email"` for a field declared with `format: "email"`.
- **Three new integration tests** exercising the above scenarios:
  - `test_example_fails_validation_when_required_field_missing`
  - `test_example_fails_validation_when_field_has_wrong_type`
  - `test_example_fails_validation_when_field_has_wrong_format`
- **`mkdocs.yml` placeholder values replaced** — `<MODULE-NAME>`,
  `<ORGANIZATION>`, and `<AUTHOR-NAME>` replaced with real values so deployed
  documentation has correct site URL and repository links.

### Changed
- `make_example_test` now accepts an `inputSchema` argument and calls
  `collect_example_input_violations` before making any `tools/call` request.

---

## [0.1.4] - 2026-03-04

### Added
- **`--mcp-tools-strict` CLI flag** — when set, generates two per-tool compliance
  tests (marked `mcp_tools_strict`) for every tool in the server:
  - `test_{tool}_has_examples`: fails if the tool has no `examples` list.
  - `test_{tool}_has_output_schema`: fails if the tool has no `outputSchema`.
- **Three new integration tests** covering strict mode: passes when all tools
  are compliant, fails when a tool is missing examples, fails when a tool is
  missing `outputSchema`. No new mock servers were added; existing
  `read_only_examples_server`, `basic_server`, and `examples_server` are reused.
- **Example-based live call tests** — for every tool that declares an `examples`
  list, the plugin now generates one test per example (marked `mcp_tools_examples`).
  Each test calls the tool via `tools/call` with the example input, asserts no
  JSON-RPC error, and — when the tool has an `outputSchema` — validates that
  every field in `structuredContent` matches the declared JSON Schema type.
  Generated tests are named `test_{tool_name}_example_{n}` (0-based index).
- **`--mcp-tools-production` CLI flag** — when set, example tests are only
  generated for tools where `annotations.readOnlyHint` is `true`. Useful for
  safe smoke tests against live production or staging environments.
- **`--mcp-tools-read-only` CLI flag** — alias for `--mcp-tools-production`,
  providing the same read-only filtering behaviour.
- **`collect_output_schema_type_mismatches()` helper** — validates that
  `structuredContent` values match their declared `outputSchema` types,
  recursing into nested `properties` objects.
- **`_post_tools_call()` helper** — sends a `tools/call` JSON-RPC request with
  session initialisation support (MCP Streamable HTTP spec 2025-03-26).
- **Three new test servers** added to the integration test suite:
  - `examples_server` — tools with `examples` and `outputSchema` (happy path)
  - `output_schema_type_error_server` — tool returns wrong type for
    `outputSchema`-declared field (expected failure)
  - `read_only_examples_server` — mixed `readOnlyHint` tools for verifying
    production/read-only filter behaviour
- **Five new integration tests** covering the above scenarios.

### Removed
- **STDIO transport support** — the plugin now only tests HTTP (`/mcp`)
  endpoints. Servers that only respond over STDIO will no longer produce
  passing tests; the plugin will generate a failing test when `/mcp` is
  unreachable, which is the correct behaviour for HTTP-first servers.
  - Removed `list_tools_stdio()` and `list_tools_stdio_subprocess()` functions
  - Removed `stdio://` URL scheme support
  - Removed automatic STDIO detection via `docker run -i`
  - Removed hybrid HTTP+STDIO test generation
  - Removed `config._mcp_tools_stdio` and related internal attributes

### Changed
- Failing test ID renamed from `test_mcp_tools[NO TRANSPORT FOUND]` to
  `test_mcp_tools[NO ENDPOINT FOUND]` to reflect HTTP-only scope
- Error messages updated to describe HTTP-only failure modes

---

## [0.1.4] - 2026-03-01

### Added
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
