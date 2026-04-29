## Context

`web.py` serves history through `/api/history` and stores generated credentials when `stream_output_and_parse()` extracts required values from subprocess logs. The UI (`static/index.html`) already refreshes history on load and on WebSocket close, so backend correctness and observability are the key reliability points.

## Goals / Non-Goals

**Goals:**
- Ensure `get_history()` returns a list payload consistently.
- Make parse-gated non-save behavior visible in logs for fast diagnosis.
- Preserve existing generation flow and output parsing rules.

**Non-Goals:**
- No overhaul of regex parsing strategy.
- No frontend behavior change.
- No DB schema change.

## Decisions

### 1. Return concrete list from `get_history()`
**Rationale:** The endpoint contract expected by the frontend is an array. Returning `None` breaks rendering and masks existing DB data.
**Alternatives considered:** Returning raw SQLite rows directly from endpoint (rejected: less explicit and potentially non-serializable in future changes).

### 2. Add explicit parse-failure observability log
**Rationale:** Current success criteria for save are strict (`email` and `password`). When parsing fails, no history row is written and the operator lacks a definitive reason. A single structured log line closes this observability gap without changing behavior.
**Alternatives considered:** Persist partial rows (rejected for minimal-fix scope and data quality concerns).

## Risks / Trade-offs

- **Risk: Increased log noise**
  Added parse-failure message may appear for runs that intentionally do not produce account/password output.
  **Mitigation:** Keep message concise and condition-specific.

- **Risk: Hidden serialization assumptions in future fields**
  Returning list of dicts now is stable, but future schema additions should remain JSON-safe.
  **Mitigation:** Keep conversion explicit in `get_history()`.
