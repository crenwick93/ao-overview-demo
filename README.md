# AO Overview Demo — Server Onboarding

A live-build demo that walks a customer through creating an AO workflow from scratch, hitting every AO feature along the way. The narrative is **Server Onboarding** — a new server request arrives via ServiceNow, AO orchestrates the full Day 1 readiness process.

The workflow is **built on the AO canvas during the session**. Playbooks and CaC are already in place. The demo takes 45–60 minutes.

## What the Demo Shows

| Feature | Aria Equivalent | How It's Shown |
|---------|----------------|----------------|
| Visual canvas | Schema editor | Build the workflow live |
| AAP job template nodes | JavaScript actions | Each step calls a real AAP job template |
| Agentic nodes (AI) | No equivalent | AI reads the SNOW request, classifies the server |
| Switch/condition | Decision elements | Route by environment: dev → auto, prod → approval |
| Approval gate | User interaction | Production path pauses for CAB approval |
| Parallel execution | forEach loops | DNS, monitoring, CMDB, backup run in parallel |
| Convergence | forEach completion | All registrations must complete before validation |
| ServiceNow audit trail | Aria audit | Every step writes work notes to the CR |
| Git integration | Packages/Git sync | Audit report committed to GitHub |
| set_stats artifact passing | Variable binding | Each node publishes data the next node consumes |

## Workflow

```
SNOW Request → AI Classify → Create CR → Switch (env)
                                            ├─ dev ────────→ Provision
                                            ├─ staging ───→ Provision
                                            └─ prod → Approval → Provision
                                                                    │
                                                    ┌───┬───┬───┐
                                                    DNS  Mon CMDB Bak  (parallel)
                                                    └───┴───┴───┘
                                                          │
                                                       Validate
                                                      ┌────┴────┐
                                                 Review CR   Git Commit
```

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/crenwick93/ao-overview-demo.git
cd ao-overview-demo
cp .env.example .env
# Fill in .env with your AAP, ServiceNow, GitHub, and AO credentials
```

### 2. Install collections

```bash
ansible-galaxy collection install -r ansible_deployment/cac/requirements.yml
```

### 3. Apply CaC

```bash
./ansible_deployment/scripts/cac-apply.sh
```

This creates all AAP job templates, credentials, and the project.

### 4. Build the workflow live

Open the AO canvas and follow [DEMO_SCRIPT.md](DEMO_SCRIPT.md). The workflow JSON in `ao/server-onboarding.json` is a reference — you build it on canvas during the demo.

### 5. Test

```bash
./scripts/test-trigger.sh '{"request_description":"New server: webserver-prod-01, RHEL 9, production","requested_by":"Jane Smith"}'
```

## Project Structure

```
├── .env.example                             ← Credential template
├── DEMO_SCRIPT.md                           ← Talk track and build guide
├── ao/
│   └── server-onboarding.json               ← Reference workflow (built live)
├── playbooks/
│   ├── manage_snow_change_request.yml        ← CR lifecycle (from baseline)
│   ├── bridge_ao_approval.yml                ← SNOW→AO approval bridge (from baseline)
│   ├── manage_git_repo.yml                   ← Git commits (from baseline)
│   ├── simulate_provision.yml                ← Stub: server provisioning
│   ├── register_service.yml                  ← Stub: DNS/monitoring/CMDB/backup
│   ├── validate_server.yml                   ← Stub: post-provision checks
│   └── generate_report.yml                   ← Stub: markdown report
├── ansible_deployment/cac/
│   ├── apply.yml                             ← CaC playbook
│   ├── vars.yml                              ← AAP object definitions
│   └── requirements.yml                      ← Collection dependencies
└── scripts/
    ├── test-trigger.sh                       ← Manual workflow trigger
    └── test-ao-approval-api.py               ← AO approval API debug tool
```

## Playbooks

### Reusable (from baseline)
| Playbook | Job Template | What It Does |
|----------|-------------|--------------|
| `manage_snow_change_request.yml` | Manage SNOW Change Request | CR lifecycle: create, authorize, update, review, close |
| `bridge_ao_approval.yml` | Bridge AO Approval | Bridges SNOW CR approval to AO approval gate |
| `manage_git_repo.yml` | Manage Git Repo | Commit files to GitHub via API |

### Stubs (simulate with debug + set_stats)
| Playbook | Job Template | What It Simulates |
|----------|-------------|-------------------|
| `simulate_provision.yml` | Simulate Provision | Server provisioning → publishes `server_ip`, `server_fqdn` |
| `register_service.yml` | Register Service | Service registration (called 4x in parallel) → publishes `registration_status` |
| `validate_server.yml` | Validate Server | Post-provision checks → publishes `validation_passed`, `validation_report` |
| `generate_report.yml` | Generate Report | Markdown onboarding report → publishes `report_content` |

The stubs are the point: *"You swap these for your real playbooks — the workflow stays the same."*

## Credentials Required

| Credential | Purpose |
|------------|---------|
| AAP OAuth Token | CaC deployment |
| ServiceNow credentials | CR management |
| AO Service Account | Approval bridge |
| GitHub PAT | Audit report commits |
| AO Webhook credentials | Workflow triggering (filled after publishing) |
