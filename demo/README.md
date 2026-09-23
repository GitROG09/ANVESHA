# Demo assets

The actual demo scenarios are implemented in `backend/services/simulation.py`
and driven through the API (`GET /api/demo/scenarios`, `POST
/api/demo/{scenario_id}/verify`) rather than static files here, so they stay
in sync with the verification engine automatically.

See `docs/demo_guide.md` for the recommended walkthrough and script.

Scenario IDs:
- `demo_1_correct`
- `demo_2_wrong_connection`
- `demo_2b_corrected`
- `demo_3_bad_measurement`
- `demo_4_insufficient_evidence`
