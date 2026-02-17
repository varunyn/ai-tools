# E2E Testing (pytest + Playwright)

This repo includes opt in end to end (E2E) tests under `tests/e2e/`. The suite drives the Streamlit UI with Playwright.

## What these tests cover

- Prompt save and persistence flows
- File upload flows, including oversize rejection

Useful UI strings for debugging selectors and failures:

- "Choose a text file"
- "AI Model"
- "Select a Prompt"
- "Prompt Name"
- "💾 Save Prompt"

Known app messages asserted by tests:

- Prompt toast contains `saved` (example: `Prompt '<name>' saved!`)
- Oversize upload error contains `File is too large` and `Max allowed`

## Prerequisites

1. **Python 3.11+** and `uv` available.
2. **OCI auth and config works**.
   - Smoke test first:

     ```bash
     python scripts/test-oci-config.py
     ```

3. **Network access**. Real OCI calls can be slow and can cost money.

## Install (dev)

1. Install dev dependencies:

   ```bash
   uv pip install -e ".[dev]"
   ```

2. Install Playwright browsers:

   ```bash
   python -m playwright install
   ```

## Run

The E2E suite is opt in.

1. Dry run (expected to skip):

   ```bash
   E2E_REAL_OCI=0 pytest -m e2e -q
   ```

2. Real run (makes real OCI calls):

   ```bash
   E2E_REAL_OCI=1 pytest -m e2e -q
   ```

## Test isolation

E2E tests start Streamlit via the test harness and isolate app state so you can run them locally without touching your real app data.

- The harness launches Streamlit in a subprocess.
- It sets `APP_CONFIG_PATH` and `APP_DATA_DIR` to point at temporary paths.
- Your real `config.toml` and `data/` are not modified.

## Evidence output

When tests take screenshots, they are saved under:

`test-results/e2e/` (relative to repo root)

You can override this location by setting the `E2E_ARTIFACTS_DIR` environment variable:

```bash
E2E_ARTIFACTS_DIR=/tmp/my-artifacts E2E_REAL_OCI=1 pytest -m e2e -q
```

## Troubleshooting

### Playwright browsers missing

Symptoms:

- Errors about missing browser executables

Fix:

```bash
python -m playwright install
```

### Port in use, or Streamlit health check fails

Symptoms:

- Harness times out waiting for `/_stcore/health`
- Streamlit fails to start

Fix ideas:

- Stop other `streamlit run ...` processes.
- Re run the test, the harness picks a free port but can still lose a race if something else grabs it.

### OCI auth or policy errors

Symptoms:

- 401, 403, or policy related errors from OCI
- Errors mentioning config profiles, key files, compartments, or permissions

Fix ideas:

1. Re run the smoke test:

   ```bash
   python scripts/test-oci-config.py
   ```

2. Confirm your OCI profile, compartment OCID, and IAM policies allow Generative AI calls.
3. If you are on VPN or a restricted network, confirm outbound access to OCI endpoints.

### OCI throttling or timeouts

Symptoms:

- 429 throttling responses
- Requests that hang or time out

Fix ideas:

- Re run the test, transient throttling happens.
- Expect higher latency during peak hours.
- If failures are consistent, check tenancy limits and service quotas.
