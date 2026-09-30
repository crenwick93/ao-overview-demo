# AO Overview Demo — Demo Script

## Before the Customer Arrives

1. CaC is applied — all AAP + EDA objects exist
2. Working workflow is imported, published, and tested
3. EDA activation is running (polling ServiceNow)
4. ServiceNow PDI is up and accessible
5. AO canvas has **two tabs**: the working workflow, and an empty canvas for the live build
6. This script is open on a second screen or printed

---

## Part 1: The Working Workflow (15–20 min)

> "Before I build one from scratch, let me show you the finished product."

### Step 1 — Show the working workflow on canvas (2 min)

**What to do:** Open the imported Server Onboarding workflow in AO.

**What to say:**
> "This is a server onboarding workflow. A ServiceNow request comes in,
> AI classifies it, a change request tracks governance, the server gets provisioned,
> four teams register it in parallel, validation runs, and an audit report goes to Git.
> Every step updates ServiceNow work notes. Let me trigger it."

### Step 2 — Create a ServiceNow incident (2 min)

**What to do:** In ServiceNow, create a new incident:
- **Short description:** `Server Onboarding: webserver-prod-01, RHEL 9, production environment. Needs DNS, monitoring, CMDB, and backup registration.`
- **Caller:** any user
- Submit

**What to say:**
> "This is your self-service entry point. Someone submits a request in ServiceNow —
> just free text, they don't fill in forms. EDA is watching for it."

### Step 3 — Watch EDA pick it up (2 min)

**What to do:** Switch to AAP → Event-Driven Ansible → Activations. Show the event arriving.

**What to say:**
> "EDA polls ServiceNow every 10 seconds. It just picked up the incident,
> matched the 'Server Onboarding' pattern, and fired the AO workflow trigger.
> This is the same model as your Aria event broker — but it covers ServiceNow, webhooks,
> Splunk, Insights, anything with an EDA source plugin."

### Step 4 — Watch the workflow execute (10 min)

**What to do:** Switch to the AO canvas. Watch nodes light up as they execute.

**Narrate each step as it runs:**

> **AI Classify:** "The AI is reading the request... it's extracted the server name, OS, and environment.
> No one had to fill in a structured form — the AI parsed natural language."

> **Create CR:** "A change request just opened in ServiceNow. Let me flip to SNOW..."
> *(Show the CR with the first work note)*

> **Classification note:** "Work note updated — the AI classification is now in the CR audit trail."

> **Switch:** "It detected production — so it's routing to the approval gate."

> **Approval:** "The workflow is paused. In the real world, EDA bridges this from SNOW — when
> the CR is approved in ServiceNow, it automatically approves here. For now I'll click approve."
> *(Click approve in AO UI)*

> **Provision:** "Server provisioning is running. This is a stub — in your world, this calls
> your vSphere or OpenShift provisioning playbook."

> **Provision note:** "SNOW updated — IP address and FQDN are now in the CR."

> **Parallel registrations:** "Four jobs just kicked off simultaneously — DNS, monitoring, CMDB, backup.
> Same playbook, different parameters. Like your Aria forEach loops. Each team owns their playbook."

> **Validate:** "All four finished. Validation is checking everything registered correctly."

> **Validated note:** "SNOW updated again — all services confirmed."

> **Review CR + Git commit:** "The CR moves to review, and the full onboarding report is committed to Git."

### Step 5 — Show the ServiceNow audit trail (2 min)

**What to do:** Open the CR in ServiceNow. Scroll through the work notes.

**What to say:**
> "Every single step is here. AI classification, provisioning details, service registrations,
> validation results. Your CAB doesn't need to ask 'what happened?' — it's all in the CR.
> This is your single pane of glass."

---

## Part 2: Build It Live (25–30 min)

> "Now let me show you how easy that was to build. I'm going to recreate it from scratch."

### Act 1 — Empty canvas (2 min)

**What to do:** Switch to the empty canvas tab.

**What to say:**
> "This is where you build workflows. Same drag-and-drop model as Aria.
> I'm going to build the server onboarding workflow you just saw, live."

### Act 2 — EDA trigger (3 min)

**What to do:** Add an **EDA trigger** node.

**What to configure:**
- Name: `ServiceNow Request`
- Input schema: `request_description` (string), `requested_by` (string)

**What to say:**
> "Every workflow starts with a trigger. EDA watches ServiceNow for new incidents.
> The trigger defines what data the workflow receives."

### Act 3 — AI classification (5 min)

**What to do:** Add an **agentic node**. Connect from trigger.

**What to configure:**
- Name: `AI: Classify Request`
- Prompt: "Read this request and extract: server_name, os_type, environment, services_needed"
- Response schema: `server_name`, `os_type`, `environment`, `services_needed`

**What to say:**
> "No Aria equivalent. The AI reads natural language and extracts structured data.
> The reasoning is fully audited — you can see exactly why it classified the server this way."

### Act 4 — Create CR (3 min)

**What to do:** Add **AAP job template node** → `Manage SNOW Change Request`. Connect from AI.

**What to configure:**
- Extra vars: `action: create`, `short_description: Server Onboarding: ${ai_classify.result.content.server_name}`

**What to say:**
> "Every step tracked in ServiceNow. Same playbook, different action values — create, update, review, close."

### Act 5 — Route by environment (3 min)

**What to do:** Add a **switch node**. Connect from CR.

**What to configure:**
- Cases: `dev`, `staging`, `prod` based on `${ai_classify.result.content.environment}`

**What to say:**
> "Same as Aria decision elements — condition-based routing."

### Act 6 — Production approval (3 min)

**What to do:** Add an **approval node** on the prod path. Dev/staging skip to provision.

**What to say:**
> "Named approvers, decision windows — or bridged from ServiceNow."

### Act 7 — Provision (2 min)

**What to do:** Add **Simulate Provision** AAP node. All three paths converge here.

**What to say:**
> "All paths arrive here. Dev went straight, prod waited for approval. In your world,
> swap this stub for your vSphere playbook."

### Act 8 — Parallel registrations (5 min)

**What to do:** Add **4 parallel AAP nodes** from provision: DNS, Monitoring, CMDB, Backup.

**What to say:**
> "Four jobs running simultaneously. Same playbook, different service_name.
> In your world: Centrify, CyberArk, BMC, DNS/IPAM — same pattern."

### Act 9 — Validate (2 min)

**What to do:** Add **Validate Server** node. Connect all 4 registrations to it.

**What to say:**
> "Nothing moves until all four complete. Post-checks catch failures before we call it done."

### Act 10 — Close the loop (2 min)

**What to do:** Add **Review CR** and **Git commit** nodes from validation.

**What to say:**
> "CR moves to review, audit report committed to Git. Full traceability."

---

## Closing (5 min)

**What to say:**
> "You've now seen it running and seen it built. Let's map this to your world:
>
> - Replace Simulate Provision with your vSphere provisioning playbook
> - Replace Register Service with your Centrify, CyberArk, BMC, DNS/IPAM playbooks
> - The workflow structure stays the same — you're swapping the AAP actions
>
> Your teams own the playbooks. AO owns the orchestration.
> ServiceNow is the audit trail. AI handles the classification.
> Day 2 operations use the same model — swap the trigger, reuse the playbooks."

---

## Cheat Sheet — Working Workflow Nodes

| # | Node | Type | Job Template | Key Config |
|---|------|------|-------------|------------|
| 1 | ServiceNow Request | EDA trigger | — | Polls incidents matching "Server Onboarding" |
| 2 | AI: Classify Request | Agentic | — | Extracts server_name, os_type, environment |
| 3 | Create Tracking CR | AAP job | Manage SNOW Change Request | `action: create` |
| 4 | CR Note: AI Classification | AAP job | Manage SNOW Change Request | `action: update` |
| 5 | Route by Environment | Switch | — | dev / staging / prod |
| 6 | CAB Approval | Approval | — | prod path only |
| 7 | Provision Server | AAP job | Simulate Provision | `server_name`, `os_type`, `environment` |
| 8 | CR Note: Provisioned | AAP job | Manage SNOW Change Request | `action: update` |
| 9 | Register DNS | AAP job | Register Service | `service_name: dns` |
| 10 | Register Monitoring | AAP job | Register Service | `service_name: monitoring` |
| 11 | Register CMDB | AAP job | Register Service | `service_name: cmdb` |
| 12 | Register Backup | AAP job | Register Service | `service_name: backup` |
| 13 | Validate Server | AAP job | Validate Server | `server_name`, `server_ip` |
| 14 | CR Note: Validated | AAP job | Manage SNOW Change Request | `action: update` |
| 15 | Review CR | AAP job | Manage SNOW Change Request | `action: review` |
| 16 | Commit Audit Report | AAP job | Manage Git Repo | `action: commit_file` |
