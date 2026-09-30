# AO Overview Demo — Project Rules

## Security Rules

- **NEVER read `.env`** — it contains secrets (passwords, tokens, API keys). It is in `.gitignore` and `.cursorignore` and must not be accessed by Cursor.
- **NEVER read `*.pem` files** — private keys.
- If you need to verify a `.env` value is set, ask the user — do not read the file.

## What This Project Is

A live-build demo for Automation Orchestrator. The narrative is **Server Onboarding** — a ServiceNow request triggers an AO workflow that orchestrates provisioning, parallel service registrations, validation, and audit trail.

The workflow is built on the AO canvas during the demo. Playbooks and CaC are pre-deployed.

## Playbooks

### Reusable (from ao-baseline)
- `manage_snow_change_request.yml` — CR lifecycle: `action: create|authorize|update|review|close`
- `bridge_ao_approval.yml` — bridges SNOW CR approval to AO approval gate
- `manage_git_repo.yml` — `action: commit_file|create_pr`

### Stubs (simulate with debug + set_stats)
- `simulate_provision.yml` — takes `server_name`, `os_type`, `environment` → publishes `server_ip`, `server_fqdn`
- `register_service.yml` — takes `service_name` (dns|monitoring|cmdb|backup), `server_name`, `server_ip` → publishes `registration_status`
- `validate_server.yml` — takes `server_name`, `server_ip` → publishes `validation_passed`, `validation_report`
- `generate_report.yml` — takes all prior artifacts → publishes `report_content`, `report_file_path`

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

### CaC Gotchas
- CaC cannot overwrite encrypted credential fields — delete the credential first or edit in AAP UI
- The controller project must be synced in AAP before CaC can create job templates referencing its playbooks
- Uses `set -a; source .env; set +a` pattern for loading env vars

### Action-Based Playbook Pattern
- `manage_snow_change_request.yml` — `action: create|authorize|update|review|close`
- `manage_git_repo.yml` — `action: commit_file|create_pr`
- AO workflow nodes call the same job template with different `action` values in extra_vars
- The `create`/`commit_file` actions publish identifiers via `set_stats` — subsequent nodes reference them as `${node.artifacts.field}`

### GitHub Integration
- Uses GitHub REST API (Contents API for commits, Pulls API for PRs)
- `GITHUB_TOKEN` is injected as env var by the "GitHub API Token" credential type
- `GITHUB_REPO` is set in `.env` and read by playbooks via `lookup('env', ...)`

## Scripts
- `./ansible_deployment/scripts/cac-apply.sh` — applies all AAP objects
- `./scripts/test-trigger.sh` — fires a test event to trigger the workflow
- `./scripts/test-ao-approval-api.py` — debug tool for AO approval API

## Deployment Order
1. Fill in `.env` from `.env.example`
2. `ansible-galaxy collection install -r ansible_deployment/cac/requirements.yml`
3. `./ansible_deployment/scripts/cac-apply.sh` (creates AAP objects)
4. Build workflow live on AO canvas (reference: `ao/server-onboarding.json`)
5. Publish workflow in AO UI
6. Update `.env` with AO webhook creds, re-run `cac-apply.sh` if needed
7. `./scripts/test-trigger.sh` (verify the pipeline)
