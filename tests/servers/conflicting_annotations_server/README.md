# Conflicting Annotations Server

MCP test server with tools that have conflicting annotation hints:

- `readonly_but_destructive`: `readOnlyHint=True` and `destructiveHint=True`
- `readonly_but_idempotent`: `readOnlyHint=True` and `idempotentHint=True`

Used to verify that `test_tool_annotations_are_consistent` fails when
`readOnlyHint` is combined with `destructiveHint` or `idempotentHint`.
