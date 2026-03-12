# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.2.0] - 2026-03-10

### Added
- **Invalid-input error tests (`mcp_tools_invalid_input`)** — for tools that
  declare `inputSchema` with at least one non-trivially-typed required field
  (integer, boolean, enum, or string with a format keyword) and no `outputSchema`,
  the plugin now generates:
  - `test_{tool}_missing_{field}` — omits one required field per test and
    asserts the server returns JSON-RPC error `-32602` (Invalid Params).
  - `test_{tool}_wrong_type_{field}` — sends an invalid-typed value for each
    field and asserts `-32602`.  Invalid values: integer → `"not-a-number"`,
    plain string → `42`, email → `"claude@ai"`, uri → `"not-a-url"`,
    enum → `"__invalid__"`, boolean → `"not-a-boolean"`.
- **Protocol-error tests (`mcp_tools_protocol`)** — always generated when an
  `/mcp` endpoint is found:
  - `test_invalid_request` — sends `tools/call` with `params: null` and asserts
    the server returns `-32600` (Invalid Request).
  - `test_method_not_found` — sends the unknown method `tools/execute` and
    asserts `-32601` (Method Not Found); only generated for servers that
    are probed to return `-32601` for unknown methods.
- **`_field_is_non_trivially_typed(field_schema)`** — helper that returns `True`
  when a field has a type beyond a plain string (integer, boolean, enum, or
  string-with-format).  Used to filter which tools receive invalid-input tests.
- **`_invalid_value_for_field(field_schema)`** — helper that returns the
  wrong-type test value for a given JSON Schema field descriptor.
- **`_post_raw_request(base_url, body, endpoint)`** — sends a raw JSON-RPC POST
  without calling `raise_for_status()`, enabling callers to inspect error
  responses with 4xx HTTP status codes.
- **Two new pytest markers**: `mcp_tools_invalid_input` and `mcp_tools_protocol`.
- **Two new mock servers** for integration testing:
  - `strict_validation_server` — validates all inputs and returns proper error
    codes (`-32602`, `-32601`, `-32600`).
  - `no_validation_server` — same schema but accepts any arguments without
    validation (used to test that missing-field/wrong-type tests correctly fail
    when the server does not validate).

### Tests added
- `test_missing_required_field_tests_generated_and_pass` — strict server.
- `test_missing_required_field_tests_fail_on_nonvalidating_server` — no-validation server.
- `test_wrong_type_tests_generated_and_pass` — strict server.
- `test_wrong_type_tests_fail_on_nonvalidating_server` — no-validation server.
- `test_invalid_request_test_generated_and_pass` — strict server.
- `test_method_not_found_test_generated_and_pass` — strict server.

### Docs updated
- `docs/index.md`: added "Invalid-Input Error Tests" and "Protocol-Error Tests"
  sections; updated generated-test table with four new rows.

## [0.1.9] - 2026-03-09

### Added
- **Schema-driven live call tests** — for every tool that declares
  `inputSchema.properties` the plugin now auto-generates a set of valid
  inputs derived entirely from the schema and calls the tool with each,
  asserting a valid (non-error) response.  If the tool also declares an
  `outputSchema`, the response is additionally validated against its
  declared field types.  Tests are named `test_{tool_name}_schema_{n}`
  and marked `mcp_tools_schema`.
- **`generate_schema_cases(input_schema)`** — new public helper that turns a
  JSON Schema `inputSchema` into a list of valid input dicts.  One *basic*
  case uses the simplest valid value for every required field; subsequent
  cases vary one field at a time.
- **`_field_values(field_schema)`** — new helper that returns the list of
  valid values for a single JSON Schema field, covering all type/format/enum
  combinations.
- **`_STRING_VARIANTS`** — 8-element list of string test values: ASCII,
  UTF-8 Chinese, UTF-8 Turkish, emoji, single-quote, double-quote,
  SQL injection, HTML injection.
- **`_FORMAT_SAMPLES`** — dict mapping JSON Schema `format` keywords
  (`email`, `uri`, `date`, `date-time`, `time`) to lists of valid sample
  strings.
- **`schema_driven_server` mock server** — new Starlette server with six
  tools covering every supported field type: `echo_string` (plain string),
  `compute` (unconstrained number), `bounded_count` (integer with
  minimum/maximum), `toggle` (boolean), `pick` (enum), `check_contact`
  (email, uri, date format fields).
- **6 new integration tests** exercising each field-type category:
  `test_schema_driven_string_tests_generated_and_pass`,
  `test_schema_driven_number_tests_generated_and_pass`,
  `test_schema_driven_integer_with_constraints_tests_generated_and_pass`,
  `test_schema_driven_boolean_tests_generated_and_pass`,
  `test_schema_driven_enum_tests_generated_and_pass`,
  `test_schema_driven_format_tests_generated_and_pass`.
- **`mcp_tools_schema` pytest marker** registered for schema-driven tests.
- **`_SESSION_CACHE`** — module-level dict that caches MCP session headers
  per `(base_url, endpoint)` pair, eliminating redundant `initialize`
  handshakes within a single pytest run.
- **`docs/index.md`** updated with a *Schema-Driven Live Call Tests* section
  and an updated test-generation table.

### Fixed
- Optional `enum` fields (not in `required`) are now included in schema test
  variation — previously, only required fields were exercised, causing tests
  with a constant non-enum value to be sent for optional enum parameters.
- `object`-typed fields that declare `required` sub-fields are now skipped
  during schema case generation instead of generating an empty `{}` value
  that most servers reject as invalid.


## [0.1.8] - 2026-03-05

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

### Note
The version numbers between 0.1.6 to 0.1.9 are missing because I used them
to test and fix the automated document publishing pipeline.


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

[0.1.9]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.4...v0.1.6
[0.1.4]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/sinan-ozel/pytest-mcp-tools/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/sinan-ozel/pytest-mcp-tools/releases/tag/v0.1.1
