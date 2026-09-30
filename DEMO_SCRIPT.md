# AO Overview Demo — Demo Script

## Before the Customer Arrives

1. CaC is applied — all AAP job templates exist
2. ServiceNow is accessible
3. AO canvas is open and **empty**
4. This script is open on a second screen or printed

## Test Trigger Payload

When you're ready to trigger the workflow (Act 11), use this:

```bash
./scripts/test-trigger.sh '{
  "request_description": "New server needed: webserver-prod-01, RHEL 9, production environment. Needs DNS, monitoring, CMDB, and backup registration.",
  "requested_by": "Jane Smith"
}'
```

---

## Live Demo Flow (45–60 min)

### Act 1 — "Let me show you what we're building" (5 min)

**What to do:** Show the blank AO canvas.

**What to say:**
> "This is Automation Orchestrator — the visual workflow engine that sits on top of AAP.
> Same drag-and-drop model you're used to in Aria, but with Ansible underneath.
> I'm going to build a server onboarding workflow live, right now."

**Talking points:**
- "Every step calls a real AAP job template — your existing Ansible is reusable"
- "The workflow adds governance, routing, and auditability on top"

---

### Act 2 — "Start with the trigger" (3 min)

**What to do:** Add an **EDA trigger** node to the canvas.

**What to say:**
> "Every workflow starts with a trigger. In your world this would be a ServiceNow request.
> EDA — Event-Driven Ansible — polls ServiceNow for new requests and kicks off the workflow automatically.
> It supports ServiceNow, webhooks, Splunk, Insights — any event source."

**What to configure:**
- Name: `ServiceNow Request`
- Input schema: `request_description` (string), `requested_by` (string)

> 💡 **Note:** We're not running EDA live today — I'll trigger the workflow manually at the end.
> The trigger node defines *what data the workflow expects*, and EDA is one way to provide it.

---

### Act 3 — "AI classifies the request" (5 min)

**What to do:** Add an **agentic node** and connect it from the trigger.

**What to say:**
> "This is new — and there's nothing like it in Aria. An AI agent reads the ServiceNow request
> and extracts the structured data we need: server name, OS, environment, services.
> No one has to fill in a form — the AI parses natural language."

**What to configure:**
- Name: `AI: Classify Request`
- Model: granite-3.3-8b (or whatever's available)
- Prompt:
  > "Read this ServiceNow request and extract: server_name, os_type, environment (dev/staging/prod), services_needed. Request: ${trigger_snow_request.request_description}"
- Response schema: `server_name`, `os_type`, `environment`, `services_needed`

**Talking points:**
- "The AI reasoning is fully audited — you can see exactly why it classified the server this way"
- "It's behind approval gates — AI doesn't act without oversight"
- "You could also give it MCP tools to look up data in your CMDB or Insights"

---

### Act 4 — "Open a change request for governance" (3 min)

**What to do:** Add an **AAP job template node** → `Manage SNOW Change Request`. Connect from AI node.

**What to say:**
> "Before we touch anything, we open a change request in ServiceNow.
> Every step from here writes work notes back to this CR.
> Your CAB sees exactly what happened, when, and why."

**What to configure:**
- Name: `Create Tracking CR`
- Job template: `Manage SNOW Change Request`
- Extra vars:
  - `action`: `create`
  - `short_description`: `Server Onboarding: ${ai_classify.result.content.server_name}`

**Talking points:**
- "This is the same playbook with different action values — create, update, review, close"
- "ServiceNow is the single pane of glass. AO handles the orchestration behind it."

---

### Act 5 — "Route by environment" (5 min)

**What to do:** Add a **switch node**. Connect from the CR node.

**What to say:**
> "Now we route based on what the AI extracted. Dev goes straight through.
> Production needs approval first. Same concept as Aria decision elements."

**What to configure:**
- Name: `Route by Environment`
- Cases:
  - `Development` → `${ai_classify.result.content.environment} == 'dev'`
  - `Staging` → `${ai_classify.result.content.environment} == 'staging'`
  - `Production` → `${ai_classify.result.content.environment} == 'prod'`

---

### Act 6 — "Production needs approval" (5 min)

**What to do:** Add an **approval node** on the production path only.

**What to say:**
> "Production requests pause here. Named approvers, decision windows — or you can bridge this
> from ServiceNow so approving the CR in SNOW automatically approves the workflow step.
> Dev and staging skip straight to provisioning."

**What to configure:**
- Name: `CAB Approval`
- Connect from switch → `Production` port
- Dev and Staging ports connect directly to the next node (provision)

**Talking points:**
- "In Aria you had user interaction elements — this is the same concept, but integrated with SNOW"
- "The bridge playbook uses the AO API — it's a real AAP job template your team can customise"

---

### Act 7 — "Provision the server" (3 min)

**What to do:** Add an **AAP job template node** → `Simulate Provision`. Connect all three paths here.

**What to say:**
> "All paths converge here. Dev came straight through. Staging came straight through.
> Production waited for approval. Now they all hit the same provisioning step."

**What to configure:**
- Name: `Provision Server`
- Job template: `Simulate Provision`
- Extra vars:
  - `server_name`: `${ai_classify.result.content.server_name}`
  - `os_type`: `${ai_classify.result.content.os_type}`
  - `environment`: `${ai_classify.result.content.environment}`

> 💡 **Key point:** "This is a stub — it simulates provisioning. In your world, you swap this
> for your vSphere provisioning playbook. The workflow structure stays exactly the same."

---

### Act 8 — "Parallel Day 1 registrations" (5 min)

**What to do:** Add **4 parallel AAP job template nodes** from the provision node.

**What to say:**
> "After provisioning, we need DNS, monitoring, CMDB, and backup — all at the same time.
> These are four separate AAP jobs running in parallel. Like your Aria forEach loops."

**What to configure:**
All four use the same job template: `Register Service`. Each has different `service_name`:
- `Register DNS` → `service_name: dns`
- `Register Monitoring` → `service_name: monitoring`
- `Register CMDB` → `service_name: cmdb`
- `Register Backup` → `service_name: backup`

All share: `server_name` and `server_ip` from the provision node's artifacts.

**Talking points:**
- "Same playbook, four times, with different parameters — each team owns their registration logic"
- "These run simultaneously, not sequentially — AO handles the parallelism"
- "In your world: Centrify, CyberArk, BMC, DNS/IPAM — same pattern"

---

### Act 9 — "Converge and validate" (3 min)

**What to do:** Add **Validate Server** AAP node. Connect all 4 registration nodes to it.

**What to say:**
> "Nothing moves forward until all four registrations complete. This is convergence.
> Then we run post-checks — DNS resolves, monitoring agent responds, CMDB record exists, backup scheduled."

**What to configure:**
- Name: `Validate Server`
- Job template: `Validate Server`
- Extra vars: `server_name`, `server_ip`

---

### Act 10 — "Close the loop" (3 min)

**What to do:** Add two final nodes from validation: `Update CR (Review)` and `Commit Audit Report`.

**What to say:**
> "Two things happen at the end. The change request moves to review — your CAB sees the full history.
> And the onboarding report is committed to Git — versions, rollback, export/import, controlled promotion."

**What to configure:**
- `Update CR (Review)` → `Manage SNOW Change Request`, `action: review`
- `Commit Audit Report` → `Manage Git Repo`, `action: commit_file`

---

### Act 11 — "Publish and trigger" (5 min)

**What to do:** Publish the workflow. Trigger a test event.

**What to say:**
> "That's the workflow built. Let me publish it and trigger a test request."

**What to do:**
1. Click Publish in AO
2. Run `./scripts/test-trigger.sh` with the payload above (or trigger from SNOW)
3. Watch the workflow execute in real-time on the canvas
4. Show ServiceNow work notes building up as each step completes

---

### Act 12 — "Tie it to your world" (5 min)

**What to say:**
> "Let's map this to your Aria workflow:
> - Replace Simulate Provision with your vSphere provisioning playbook
> - Replace Register Service with your Centrify, CyberArk, BMC, DNS/IPAM playbooks
> - The workflow structure stays the same — you're swapping the AAP actions
>
> Your teams own the playbooks. AO owns the orchestration.
> ServiceNow is the audit trail. AI handles the classification.
> Day 2 operations use the same model — swap the trigger, reuse the playbooks."

**Key closing points:**
- "Your Ansible is already reusable. AO gives it governance and orchestration."
- "AI decisions are audited and behind approval gates — not a black box."
- "ServiceNow is the single pane of glass — every step writes work notes."
- "Teams trigger via self-service in SNOW. AO handles the task switching."

---

## Workflow Node Summary (Cheat Sheet)

| # | Node | Type | Job Template | Key Extra Vars |
|---|------|------|-------------|----------------|
| 1 | ServiceNow Request | EDA trigger | — | `request_description`, `requested_by` |
| 2 | AI: Classify Request | Agentic | — | Prompt extracts `server_name`, `os_type`, `environment` |
| 3 | Create Tracking CR | AAP job | Manage SNOW Change Request | `action: create` |
| 4 | Route by Environment | Switch | — | dev / staging / prod |
| 5 | CAB Approval | Approval | — | prod path only |
| 6 | Provision Server | AAP job | Simulate Provision | `server_name`, `os_type`, `environment` |
| 7 | Register DNS | AAP job | Register Service | `service_name: dns` |
| 8 | Register Monitoring | AAP job | Register Service | `service_name: monitoring` |
| 9 | Register CMDB | AAP job | Register Service | `service_name: cmdb` |
| 10 | Register Backup | AAP job | Register Service | `service_name: backup` |
| 11 | Validate Server | AAP job | Validate Server | `server_name`, `server_ip` |
| 12 | Update CR (Review) | AAP job | Manage SNOW Change Request | `action: review` |
| 13 | Commit Audit Report | AAP job | Manage Git Repo | `action: commit_file` |

**Total: 13 nodes** — ~15 minutes to build at talking pace.
