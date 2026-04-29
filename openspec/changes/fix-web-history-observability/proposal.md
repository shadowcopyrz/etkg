## Why

The Web UI currently shows successful generation logs, but users may still see an empty **Generation History** panel. This creates a trust gap: users cannot tell whether data was not saved or simply not returned.

Two backend paths can independently cause this:
- `get_history()` fetches DB rows but does not return them, so `/api/history` can return `null`.
- History persistence in `stream_output_and_parse()` is gated by regex extraction (`email` + `password`), so successful process completion does not always imply a saved history record.

## What Changes

- Fix backend history retrieval so `get_history()` always returns a JSON-serializable list of records.
- Add one explicit observability log message when parsing completes without enough fields to call `save_history(...)`.
- Keep scope minimal: no schema migration, no frontend redesign, no broad parsing refactor.

## Capabilities

### Modified Capabilities
- `web-server`: `/api/history` reliably returns list data for the history panel.
- `history-db`: save-path observability improves diagnosis of parse-gated non-persistence.

## Impact

- **Dependencies**: None.
- **Architecture**: No architectural change; targeted backend behavior correction.
- **Existing Code**: Small updates in `web.py` (`get_history`, parse/save branch logging).
