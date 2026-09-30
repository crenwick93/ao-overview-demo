# AO Overview Demo — Project Rules

## Security Rules

- **NEVER read `.env`** — it contains secrets (passwords, tokens, API keys). It is in `.gitignore` and `.cursorignore` and must not be accessed by Cursor.
- **NEVER read `*.pem` files** — private keys.
- If you need to verify a `.env` value is set, ask the user — do not read the file.

## What This Project Is

A two-part AO demo for a customer evaluating Aria → AO migration:

1. **Working workflow** — pre-imported, triggered by a real ServiceNow incident via EDA, updates SNOW work notes at every milestone
2. **Live build** — build the same workflow from scratch on the AO canvas during the session

The narrative is **Server Onboarding**. Playbooks simulate the actions (no real VMs) — the workflow structure and AO features are the star.

## Demo Flow

1. Show the working workflow executing end-to-end (create SNOW incident → EDA → AO → work notes)
2. Build a fresh workflow on the empty canvas, explaining each feature
3. Map it to the customer's Aria workflow

## Playbooks

### Reusable (from ao-baseline)
- `trigger_ao_workflow.yml` — EDA-to-AO bridge (called by EDA activation)
- `manage_snow_incident.yml` — incident lifecycle: `action: create|update|resolve`
- `manage_snow_change_request.yml` — CR lifecycle: `action: create|authorize|update|review|close`
- `bridge_ao_approval.yml` — bridges SNOW CR approval to AO approval gate
- `manage_git_repo.yml` — `action: commit_file|create_pr`

### Stubs (simulate with debug + set_stats)
- `simulate_provision.yml` — takes `server_name`, `os_type`, `environment` → publishes `server_ip`, `server_fqdn`
- `register_service.yml` — takes `service_name` (dns|monitoring|cmdb|backup), `server_name`, `server_ip` → publishes `registration_status`
- `validate_server.yml` — takes `server_name`, `server_ip` → publishes `validation_passed`, `validation_report`

## EDA

- Rulebook: `rulebooks/server_onboarding.yml`
- Polls `incident` table for short_description matching "Server Onboarding"
- Also polls `change_request` table for CR approval → AO bridge
- Requires a DE with `servicenow.itsm` (see `dependencies/de/`)

## Key Technical Decisions

### AO Workflow JSON Format
- Uses `schema_version: "2.0.0"`, `triggers` array, `edges` array, `${var}` syntax
- Node types: `aap_job_template`, `agentic`, `switch`, `approval`
- AAP job nodes use `parameters.job_template_name` and `parameters.extra_vars`
- Agentic nodes use `parameters.prompt` and `parameters.model`
- AI output is at `${node.result.content.field}` when using response schema
- Switch conditions: `${node.result.content.field} == 'value'`
- Approval nodes use `from_port: "approved"` on outgoing edges

### ServiceNow PDI Gotchas
- `close_code` must be `"Solution provided"` (not `"Solved (Permanently)"`)
- Resolving an incident is a two-step operation: add work notes first, then resolve
- Work notes must be wrapped in `[code]...[/code]` tags for proper HTML rendering
- AI output should use HTML formatting (`<h3>`, `<p>`, `<ul>`, `<code>`)

### EDA Gotchas
- **Split rulebooks by source type**: webhook sources and polling sources CANNOT share an activation
- The EDA controller credential needs host URL with `/api/controller/` path suffix
- The `webhook_path` is passed from EDA activation extra_vars → rulebook → bridge job → AO trigger
- EDA activation can't be updated by CaC while running — disable in AAP UI first
- CR approval bridge: `event.state == '-1'` is the Implement state in ServiceNow

### CaC Gotchas
- CaC cannot overwrite encrypted credential fields — delete the credential first or edit in AAP UI
- The controller project must be synced in AAP before CaC can create job templates
- The EDA project must also be synced separately for rulebook activations
- Two-pass CaC: first run creates objects with placeholder creds, second run updates with real creds
- Uses `set -a; source .env; set +a` pattern for loading env vars

### Action-Based Playbook Pattern
- `manage_snow_change_request.yml` — `action: create|authorize|update|review|close`
- `manage_git_repo.yml` — `action: commit_file|create_pr`
- The `create`/`commit_file` actions publish identifiers via `set_stats` — subsequent nodes reference them as `${node.artifacts.field}`

## Scripts
- `./dependencies/build-images.sh` — builds DE container image
- `./ansible_deployment/scripts/cac-apply.sh` — applies all AAP/EDA objects
- `./scripts/test-trigger.sh` — fires a test event to trigger the workflow
- `./scripts/test-ao-approval-api.py` — debug tool for AO approval API

## Deployment Order
1. Fill in `.env` from `.env.example`
2. Build DE image (`./dependencies/build-images.sh --push`)
3. `ansible-galaxy collection install -r ansible_deployment/cac/requirements.yml`
4. `./ansible_deployment/scripts/cac-apply.sh` (creates AAP + EDA objects)
5. Import `ao/server-onboarding.json` in AO UI, configure agentic node, publish
6. Update `.env` with AO webhook creds, re-run `cac-apply.sh`
7. Create a SNOW incident with "Server Onboarding" in the short description
