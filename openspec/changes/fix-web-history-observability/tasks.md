## 1. Backend history return contract

- [x] 1.1 Update `get_history()` in `web.py` to return a list of JSON-serializable history records.
- [ ] 1.2 Verify `/api/history` responds with array JSON (including empty array when no rows).

## 2. Parse-save observability

- [x] 2.1 In `stream_output_and_parse()` (`web.py`), add one log branch for "parse incomplete, history not saved" when save preconditions fail.
- [x] 2.2 Ensure existing successful-save log remains unchanged.

## 3. Verification

- [ ] 3.1 Run one generation scenario that saves successfully and confirm history appears.
- [ ] 3.2 Run one scenario where parse preconditions are not met and confirm the new diagnostic log appears.
- [ ] 3.3 Confirm no regression in WebSocket log streaming and stop behavior.
