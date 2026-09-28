- [ ] Add stdio support - WON'T DO
- [x] Check that the tool has `name`.
- [x] Check that the `name`s are unique
- [x] Check annotation: `title`
- [x] Check annotation: expect `readOnlyHint`==`false` if `idempotentHint`
- [x] Check annotation: expect `readOnlyHint`==`false` if `destructiveHint`
- [x] Check `inputSchema`.
- [x] Check that `inputSchema` has examples for all fields/properties
- [x] Check an example (optional with kwarg)
- [x] Check examples against schema. Do they have all required fields?
- [x] Check `outputSchema`.
- [x] Add tool calls: `--mcp-tools-production`/`--mcp-tools-read-only` limit these to `readOnlyHint`==`true`
- [x] Add tool calls based on examples
- [ ] Add tool calls based on descriptions
- [x] Check `outputSchema` after tool calls.
- [ ] Check that the `description` is meaningful with LLM as Judge methodology.
- [x] Add --mcp-tools-strict. Do all have outputSchema and examples?
- [ ] tool calls: correct combinations (fields that are only valid together)
- [x] tool calls: missing fields, expect a tool execution error (`isError: true`,
      per MCP spec 2025-11-25); `-32602` under `--mcp-tools-legacy-invalid-params`
      for pre-spec servers. Reports clearly on which field is missing.
- [x] tool calls: fields with wrong type, same expectation as above. Reports
      clearly on which field/type failed.
- [x] tool calls: more detailed examples using format for strings (email, uri,
      date, date-time, time — schema-driven tests)
