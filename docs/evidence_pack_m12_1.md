# SurFit AI — Tamper-Proof Evidence Pack (M12.1)

## Scope
This evidence pack focuses specifically on tamper-evident integrity in SurFit AI after M12 and M12.1.

## Claim
SurFit can detect post-run mutation of execution records using a per-run cryptographic hash chain, and can validate run integrity programmatically.

## What Is Implemented
1. Per-event hash chain in `execution_log`
- `prev_hash`
- `event_hash`
- Hash input fields (canonical JSON):
  - `run_id`
  - `node_id`
  - `tool_name`
  - `decision`
  - `latency_ms`
  - `error`
  - `timestamp`

2. Canonical hashing utilities
- Deterministic JSON serialization (`sort_keys=True`, compact separators)
- SHA256 hashing
- Payload normalization for LLM artifacts (`\r\n -> \n`, trim trailing whitespace)

3. Integrity verifier
- `verify_run_integrity(conn, run_id)` recomputes chain ordered by `(timestamp_iso, id)`
- Returns:
  - `valid`
  - `first_mismatch_index`
  - `expected_hash`
  - `found_hash`

4. LLM integrity anchors
- `llm_invocations` table stores:
  - model/provider metadata
  - `raw_tool_input_hash`
  - `sanitized_prompt_input_hash`
  - `llm_output_text_hash`

5. Audit output includes integrity evidence
- `INTEGRITY CHECK`
- `LLM INVOCATION HASHES`

## Tamper Test Artifacts (M12.1)
1. CLI utility
- File: `tamper_test.py`
- Behavior:
  - run baseline SAW on isolated test DB
  - assert integrity pass
  - mutate one non-genesis execution row
  - assert integrity fail
  - print mismatch details

2. Automated test
- File: `test_tamper_integrity.py`
- Command:
```bash
python -m pytest -q test_tamper_integrity.py
```
- Expected outcome: pass

## Recorded Test Evidence
### CLI Tamper Test Output
```text
PASS
Run ID: tamper_test_run_001
Mismatch index: 3
Expected hash: fc753d16a7d60645622e15f7a9a94c7c5a934b2be8913195c954f09f74ab4985
Found hash: 107cde2486e7f85d0eedb5d12b5749fa9660e69a60549dc22731f26dc6d52f2f
```

Interpretation:
- Baseline run integrity validated before mutation.
- After mutating one row, verifier fails at earliest corrupted point (`index=3`).
- Expected and stored hashes diverge as designed.

### Pytest Output
```text
1 passed in 0.57s
```

Interpretation:
- Tamper detection is automated and repeatable.

## Production Audit Evidence (Example)
Observed in exported audit card for a completed run:
- `INTEGRITY CHECK: Valid: True`
- `First Mismatch Index: None`
- LLM invocation hash fields present:
  - `raw_tool_input_hash`
  - `sanitized_prompt_input_hash`
  - `llm_output_text_hash`

Interpretation:
- Fresh, untampered runs verify cleanly.
- LLM lineage is hash-anchored.

## Reproduction Steps
### A) Run tamper CLI utility
```bash
cd /Users/andreasaltamirano/Desktop/surfit-core
python tamper_test.py
```
Expected: `PASS` + mismatch details after mutation.

### B) Run automated tamper test
```bash
cd /Users/andreasaltamirano/Desktop/surfit-core
python -m pytest -q test_tamper_integrity.py
```
Expected: `1 passed`.

### C) Verify runtime audit integrity
1. Run a normal SAW in app.
2. Export audit card.
3. Confirm:
- `INTEGRITY CHECK` is present
- `Valid: True`
- LLM hash fields are present

## Constraints / Notes
- This is local cryptographic tamper evidence (not blockchain, not distributed consensus).
- Integrity guarantees apply to data stored in the monitored DB path and verification procedure.
- Existing cloud deploy skew was handled with startup fallbacks to avoid transient import/runtime crashes.

## File Index
- `logger.py` — hash chain, hash utilities, verifier, LLM invocation persistence
- `engine.py` — LLM invocation write hook
- `app.py` — audit export includes integrity + hashes
- `tools.py` — governed LLM tool metadata payload
- `tamper_test.py` — CLI tamper proof utility
- `test_tamper_integrity.py` — pytest tamper test
