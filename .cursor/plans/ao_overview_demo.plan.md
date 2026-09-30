---
name: AO Overview Demo — Server Onboarding
overview: >
  A live-build demo that walks a customer through creating an AO workflow from scratch,
  hitting every AO feature along the way. The narrative is "Server Onboarding" — a new
  server request arrives via ServiceNow, AO orchestrates the full Day 1 readiness process.
  The demo is designed to be built on the canvas during the session, with playbooks and CaC
  already in place. One day to prepare, built from the ao-baseline template.
todos:
  - id: clone-setup
    content: Clone ao-baseline into ao-overview-demo, retarget origin, push baseline
    status: complete
  - id: stub-playbooks
    content: "Create stub playbooks: simulate_provision.yml, register_service.yml, validate_server.yml, generate_report.yml"
    status: complete
  - id: cac-customize
    content: Rename CaC project/templates to AO Overview Demo, add new job templates for stubs, remove EDA
    status: complete
  - id: workflow-json
    content: Build the AO workflow JSON for reference (the live demo builds this on canvas)
    status: complete
  - id: demo-script
    content: Write DEMO_SCRIPT.md — what to say, what to click, what the audience sees
    status: complete
  - id: readme-rewrite
    content: Rewrite README.md and project.md for the demo project
    status: complete
  - id: push
    content: Push to github.com/crenwick93/ao-overview-demo
    status: pending
isProject: true
---

# AO Overview Demo — Server Onboarding

## The Pitch

"I'm going to build a workflow in front of you that automates server onboarding from ServiceNow
request to production-ready. Along the way you'll see every AO feature — the visual canvas,
AAP job templates, AI agents, conditional routing, approval gates, parallel execution, convergence,
and full ITSM auditability. This maps directly to what your Aria VM workflow does today."

## Why Server Onboarding

The customer said their VM workflow in Aria is "complete and does many tasks" covering Centrify,
CyberArk, BMC, DNS/IPAM, CMDB, monitoring, backup, and patching. They care about:

- Multi-team orchestration with governance
- Self-service with guardrails
- A VM being "ready to deploy" on Day 1
- Aria → AO migration path

Server onboarding hits all of this naturally and exercises every AO feature without needing
real vSphere or OpenShift infrastructure. The playbooks simulate the actions with debug output
and set_stats, so the workflow runs end-to-end in minutes.

## AO Features Demonstrated

| # | Feature | Aria Equivalent | How the Demo Shows It |
|---|---------|-----------------|----------------------|
| 1 | **Visual canvas** | Schema editor | Build the workflow live, drag and connect nodes |
| 2 | **AAP job template nodes** | Actions in JavaScript | Each step calls a real AAP job template |
| 3 | **Agentic nodes (AI)** | No native equivalent | AI reads the SNOW request, classifies the server, recommends config |
| 4 | **Switch/condition** | Decision elements | Route by environment: dev → auto-provision, prod → approval first |
| 5 | **Approval gate** | User interaction | Production path pauses for CAB approval, bridges from ServiceNow |
| 6 | **Parallel execution** | Foreach loops | After provision: DNS, monitoring, CMDB, backup all run in parallel |
| 7 | **Convergence** | Foreach completion | All registrations must complete before validation runs |
| 8 | **EDA trigger** | Event broker | SNOW incident polling triggers the workflow |
| 9 | **ServiceNow audit trail** | Audit via Aria | Every step writes work notes — the audience follows along in SNOW |
| 10 | **Git integration** | Packages/Git sync | Final audit report committed to GitHub |
| 11 | **set_stats artifact passing** | Variable binding | Each node publishes data the next node consumes |

## Workflow Design

```
SNOW Request (EDA trigger)
  │
  ▼
┌─────────────────────────┐
│ AI: Classify Request     │  ← Agentic node: reads description, extracts
│                          │    server_name, os_type, environment, services_needed
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Create Tracking CR       │  ← manage_snow_change_request.yml (action: create)
│                          │    Publishes cr_sys_id, cr_number
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Switch: Environment      │  ← dev / staging / prod
└───┬─────────┬───────┬───┘
    │         │       │
    ▼         ▼       ▼
  [dev]    [staging] [prod]
    │         │       │
    │         │       ▼
    │         │   ┌───────────┐
    │         │   │ Approval  │  ← Approval gate (manual or SNOW CR bridge)
    │         │   └─────┬─────┘
    │         │         │
    ▼         ▼         ▼
┌─────────────────────────┐
│ Simulate Provision       │  ← Converge point. All paths arrive here.
│                          │    simulate_provision.yml
└────────────┬────────────┘
             │
     ┌───────┼───────┬──────────┐
     ▼       ▼       ▼          ▼
  [DNS]  [Monitor] [CMDB]   [Backup]   ← Parallel AAP jobs (register_service.yml)
     │       │       │          │         Each with service_name=dns|monitoring|cmdb|backup
     └───────┼───────┴──────────┘
             │
             ▼  (converge)
┌─────────────────────────┐
│ Validate Server          │  ← validate_server.yml — checks all registrations
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Update CR (review)       │  ← manage_snow_change_request.yml (action: review)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Commit Audit to Git      │  ← manage_git_repo.yml (action: commit_file)
│                          │    Full onboarding report committed as evidence
└─────────────────────────┘
```

**Total nodes: ~14** (manageable to build live in 15-20 minutes on the canvas)

## Playbooks Needed

### Already in baseline (reuse as-is)
- `trigger_ao_workflow.yml` — EDA-to-AO bridge
- `manage_snow_incident.yml` — incident lifecycle (may use for initial trigger tracking)
- `manage_snow_change_request.yml` — CR lifecycle (create, authorize, update, review, close)
- `bridge_ao_approval.yml` — SNOW CR → AO approval gate
- `manage_git_repo.yml` — commit audit trail to GitHub

### New stub playbooks (simulate with debug + set_stats)

**`playbooks/simulate_provision.yml`**
- Takes: `server_name`, `os_type`, `environment`
- Simulates: "Provisioning server..." with a pause
- Publishes via set_stats: `server_ip`, `server_fqdn`, `provision_status`
- Shows: AAP job template node, artifact passing

**`playbooks/register_service.yml`**
- Takes: `service_name` (dns | monitoring | cmdb | backup), `server_name`, `server_ip`
- Simulates: "Registering {{ server_name }} in {{ service_name }}..."
- Publishes via set_stats: `registration_status`, `registration_details`
- Shows: same playbook called 4x in parallel with different extra_vars (like the action pattern)

**`playbooks/validate_server.yml`**
- Takes: `server_name`, `server_ip`, `services_registered` (list)
- Simulates: checking each registered service
- Publishes via set_stats: `validation_passed` (true/false), `validation_report`
- Shows: converge point — only runs after all parallel paths complete

**`playbooks/generate_report.yml`** (optional — could be done by agentic node instead)
- Takes: all prior artifacts
- Generates a markdown summary
- Publishes: `report_content` for the Git commit

## CaC Changes

### Rename
- Project: "AO Baseline" → "AO Overview Demo"
- Activation: "ao-baseline-events" → "ao-overview-demo-events"
- Git repo URL: crenwick93/ao-overview-demo

### New Job Templates
- "Simulate Provision" → `playbooks/simulate_provision.yml`
- "Register Service" → `playbooks/register_service.yml` (called 4x with different vars)
- "Validate Server" → `playbooks/validate_server.yml`

### Keep As-Is
- All credential types (ServiceNow, AO Webhook, AO API, GitHub API Token)
- All existing credentials
- All baseline job templates (AO Workflow Bridge, Manage SNOW Incident, etc.)
- EDA objects (just rename the project/activation)

## Demo Script (High Level)

### Setup (before the customer arrives)
1. CaC is applied, AAP objects exist
2. EDA activation is running
3. SNOW is accessible
4. The AO canvas is open and empty

### Live Demo Flow (45-60 min)

**Act 1: "Let me show you what we're building" (5 min)**
- Show the blank AO canvas
- Explain: "This is where you build workflows — same drag-and-drop model as Aria"
- Show the Aria comparison table on a slide
- "I'm going to build a server onboarding workflow live"

**Act 2: "Start with the trigger" (5 min)**
- Add EDA trigger node
- Explain: "ServiceNow, webhooks, Insights — any event source, not just Aria"
- Show the trigger schema

**Act 3: "AI classifies the request" (5 min)**
- Add agentic node
- Write the prompt live: "Read this SNOW request, extract server name, OS, environment..."
- Explain: "This is new — AI with audited reasoning, behind approval gates"
- Connect model credential and MCP tools if relevant

**Act 4: "Open a change request for governance" (3 min)**
- Add AAP job template node → Manage SNOW Change Request (create)
- Show how extra_vars pass AI output to the playbook
- "Every step tracked in ServiceNow — full audit trail"

**Act 5: "Route by environment" (5 min)**
- Add switch node with dev/staging/prod cases
- "Same as Aria decision elements — condition-based routing"
- Draw edges from each case

**Act 6: "Production needs approval" (5 min)**
- Add approval node on the prod path
- "Named approvers, decision windows — or bridged from ServiceNow"
- Show the SNOW CR approval bridge concept
- dev and staging paths skip straight to provisioning

**Act 7: "Provision the server" (3 min)**
- Add converge point — AAP node for simulate_provision
- "All paths arrive here. Dev went straight, prod waited for approval."

**Act 8: "Parallel Day 1 registrations" (5 min)**
- Add 4 parallel AAP nodes: DNS, Monitoring, CMDB, Backup
- All call the same "Register Service" template with different service_name
- "These run simultaneously — like your Aria foreach loops"
- "Each team owns their playbook, AO orchestrates the sequence"

**Act 9: "Converge and validate" (3 min)**
- Add validation node after all 4 converge
- "Nothing moves forward until all registrations complete"
- "Post-checks catch failures before we call it done"

**Act 10: "Close the loop" (3 min)**
- Add CR review node + Git commit node
- "Change request moves to review, full audit log committed to Git"
- "Versions, rollback, export/import — controlled promotion from dev to prod"

**Act 11: "Publish and trigger" (5 min)**
- Publish the workflow
- Trigger a test event (test-trigger.sh or create a SNOW incident)
- Watch the workflow execute in real-time
- Show SNOW work notes building up as each step completes

**Act 12: "Tie it to your world" (5 min)**
- "Replace simulate_provision with your vSphere/OpenShift provisioning playbook"
- "Replace register_service with your Centrify, CyberArk, BMC, DNS/IPAM playbooks"
- "The workflow structure stays the same — you're just swapping the AAP actions"
- "Your teams own the playbooks, AO owns the orchestration"

### Key Talking Points
- "Your Ansible is already reusable. AO gives it governance and orchestration."
- "AI decisions are audited and behind approval gates — not a black box."
- "ServiceNow is the single pane of glass — every step writes work notes."
- "Teams trigger via self-service in SNOW. AO handles the task switching."
- "Day 2 operations use the same model — swap the trigger, reuse the playbooks."

## What NOT to Over-Engineer

- Don't need real DNS/CMDB/monitoring — stubs are the point ("you plug in your playbooks")
- Don't need real VM provisioning — the workflow structure is the star
- Don't need multiple EDA rules — one SNOW poll rule is enough for the demo
- Don't need the Git PR flow — a simple commit is enough to show the pattern
- Don't need loops syntax in the JSON — parallel paths visually demonstrate the concept

## File Structure (after build)

```
ao-overview-demo/
├── .env.example
├── ansible.cfg / ansible-navigator.yml
├── README.md                              ← Rewritten for this demo
├── DEMO_SCRIPT.md                         ← Detailed talk track
├── group_vars/all.yml
├── ao/
│   └── server-onboarding.json             ← Reference workflow (built live on canvas)
├── playbooks/
│   ├── trigger_ao_workflow.yml            ← From baseline
│   ├── manage_snow_incident.yml           ← From baseline
│   ├── manage_snow_change_request.yml     ← From baseline
│   ├── bridge_ao_approval.yml             ← From baseline
│   ├── manage_git_repo.yml               ← From baseline
│   ├── simulate_provision.yml             ← NEW: stub
│   ├── register_service.yml               ← NEW: stub (called 4x in parallel)
│   └── validate_server.yml                ← NEW: stub
├── rulebooks/
│   └── server_onboarding.yml              ← Customized from baseline
├── ansible_deployment/cac/
│   ├── apply.yml
│   ├── vars.yml                           ← Renamed + new templates
│   └── requirements.yml
├── dependencies/ (from baseline)
├── setup/ (from baseline)
├── scripts/
│   ├── test-trigger.sh
│   └── test-ao-approval-api.py
└── .cursor/rules/project.md               ← Rewritten for this demo
```

## Time Estimate

| Task | Time |
|------|------|
| Stub playbooks (4 files) | 30 min |
| CaC customization | 20 min |
| Workflow JSON (reference) | 30 min |
| Demo script | 30 min |
| README + project.md rewrite | 15 min |
| Test end-to-end | 30 min |
| **Total** | **~3 hours** |
