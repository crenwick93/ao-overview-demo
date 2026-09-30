# AO Overview Demo — Demo Script

## Before the Customer Arrives

1. CaC is applied — all AAP + EDA objects exist
2. Working workflow is imported, published, and tested
3. EDA activation is running (polling ServiceNow)
4. ServiceNow PDI is up and accessible
5. AO canvas has **two tabs**: the working workflow, and an empty canvas for the live build
6. AWS credentials are configured and working (test with a quick EC2 launch if needed)
7. This script is open on a second screen or printed

---

## Part 1: The Working Workflow (15–20 min)

> "Before I build one from scratch, let me show you the finished product."

### Step 1 — Show the working workflow on canvas (2 min)

**What to do:** Open the imported Server Onboarding workflow in AO.

**What to say:**
> "This is a server onboarding workflow. A ServiceNow request comes in,
> we route by environment — dev goes straight through, prod needs approval —
> then we provision a real EC2 instance, wait until it's reachable,
> four teams register services in parallel, validation runs, and an audit report goes to Git.
> Every step updates work notes on the ServiceNow request. Let me trigger it."

### Step 2 — Create a ServiceNow request (2 min)

**What to do:** In ServiceNow, create a new **service request item** (RITM):
- **Short description:** `Server Onboarding: webserver-prod-01`
- Submit

**What to say:**
> "This is your self-service entry point. Someone raises a service request in ServiceNow.
> EDA is watching for it."

### Step 3 — Watch EDA pick it up (2 min)

**What to do:** Switch to AAP → Event-Driven Ansible → Activations. Show the event arriving.

**What to say:**
> "EDA polls ServiceNow every 10 seconds. It just picked up the request,
> matched the 'Server Onboarding' pattern, and fired the AO workflow.
> This is the same model as your Aria event broker — but it covers ServiceNow, webhooks,
> Splunk, Insights, anything with an EDA source plugin."

### Step 4 — Watch the workflow execute (10 min)

**What to do:** Switch to the AO canvas. Watch nodes light up as they execute.

**Narrate each step as it runs:**

> **Switch:** "It detected the environment from the request — this one's production,
> so it's routing to the approval gate."

> **Approval:** "The workflow is paused. In the real world, this could be bridged from
> your ITSM tool — when a CAB approves in ServiceNow, it auto-approves here.
> For now I'll click approve."
> *(Click approve in AO UI)*

> **Provision:** "Now it's launching a real EC2 instance. RHEL 9, t3.micro.
> This calls the same `amazon.aws.ec2_instance` module you'd use in any Ansible playbook.
> In your world, swap this for vSphere, Azure, whatever you provision with."

> **While loop:** "The server is spinning up — this is a While loop, polling SSH port 22.
> It'll retry every iteration until the server responds. You can see the iterations ticking over.
> This is how you handle anything that needs wait-and-retry logic."
> *(Watch 2–4 iterations)*

> **Server ready:** "SSH is reachable — the loop exits and we fan out."

> **Parallel registrations:** "Four jobs just kicked off simultaneously — DNS, monitoring, CMDB, backup.
> Same playbook, different parameters. Like your Aria forEach loops. Each team owns their playbook."

> **Validate:** "All four finished. Validation is checking everything registered correctly."

> **Close + Git:** "The request is closed in ServiceNow, and the full onboarding report is committed to Git."

### Step 5 — Show the ServiceNow audit trail (2 min)

**What to do:** Open the RITM in ServiceNow. Scroll through the work notes.

**What to say:**
> "Every single step is here. Provisioning details, IP address, service registrations,
> validation results. Your CAB doesn't need to ask 'what happened?' — it's all on the request.
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
- Input schema: `server_name` (string), `environment` (string), `ritm_sys_id` (string)

**What to say:**
> "Every workflow starts with a trigger. EDA watches ServiceNow for new requests.
> The trigger defines what data the workflow receives — structured fields, not free text."

### Act 3 — Route by environment (3 min)

**What to do:** Add a **switch node**. Connect from trigger.

**What to configure:**
- Cases: `dev`, `staging`, `prod` based on `${trigger_snow.environment}`

**What to say:**
> "Same as Aria decision elements — condition-based routing.
> Dev and staging go straight to provisioning. Prod needs approval."

### Act 4 — Production approval (3 min)

**What to do:** Add an **approval node** on the prod path. Dev/staging skip to provision.

**What to say:**
> "Named approvers, decision windows — or bridged from ServiceNow."

### Act 5 — Provision (3 min)

**What to do:** Add **Provision Server** AAP node. All three paths converge here.

**What to configure:**
- Extra vars: `server_name`, `os_type`, `environment`, `ritm_sys_id` from trigger

**What to say:**
> "All paths arrive here. Dev went straight, prod waited for approval.
> This one launches a real EC2 instance — in your world, swap for your vSphere playbook."

### Act 6 — While loop: Wait for Server Ready (5 min)

**What to do:** Add a **loop node** (While type). Connect from provision.

**What to configure:**
- Loop type: While
- Condition: `${wait_for_server.artifacts.server_ready} != true`
- Max iterations: 10
- Inner node: Check Server Ready job template with `server_ip` from provision artifacts

**What to say:**
> "This is the While loop. It keeps checking SSH port 22 on the new server.
> Each iteration runs a job template — `wait_for` on port 22, 15-second timeout.
> When the server responds, `server_ready` becomes true and the loop exits.
> Max iterations as a safety net — you don't want infinite loops in production.
> This pattern works for anything: waiting for a service to be healthy, polling an API,
> retry logic after a deployment."

### Act 7 — Parallel registrations (5 min)

**What to do:** Add **4 parallel AAP nodes** from the loop: DNS, Monitoring, CMDB, Backup.

**What to say:**
> "Four jobs running simultaneously. Same playbook, different service_name.
> In your world: Centrify, CyberArk, BMC, DNS/IPAM — same pattern."

### Act 8 — Validate (2 min)

**What to do:** Add **Validate Server** node. Connect all 4 registrations to it.

**What to say:**
> "Nothing moves until all four complete. Post-checks catch failures before we call it done."

### Act 9 — Close the loop (2 min)

**What to do:** Add **Close Request** and **Git commit** nodes from validation.

**What to say:**
> "Request closed in ServiceNow, audit report committed to Git. Full traceability."

---

## Closing (5 min)

**What to say:**
> "You've now seen it running and seen it built. Let's map this to your world:
>
> - Replace Provision Server with your vSphere provisioning playbook
> - Replace Register Service with your Centrify, CyberArk, BMC, DNS/IPAM playbooks
> - The workflow structure stays the same — you're swapping the AAP actions
>
> Your teams own the playbooks. AO owns the orchestration.
> ServiceNow is the audit trail. The While loop handles wait-and-retry.
> Parallel execution means registrations don't bottleneck each other.
> Day 2 operations use the same model — swap the trigger, reuse the playbooks."

---

## Cheat Sheet — Working Workflow Nodes

| # | Node | Type | Job Template | Key Config |
|---|------|------|-------------|------------|
| 1 | ServiceNow Request | EDA trigger | — | Polls RITMs matching "Server Onboarding" |
| 2 | Route by Environment | Switch | — | dev / staging / prod |
| 3 | CAB Approval | Approval | — | prod path only |
| 4 | Provision Server | AAP job | Provision Server | Real EC2 — `server_name`, `environment` |
| 5 | Wait for Server Ready | While loop | Check Server Ready | SSH port 22 check, max 10 iterations |
| 6 | Register DNS | AAP job | Register Service | `service_name: dns` |
| 7 | Register Monitoring | AAP job | Register Service | `service_name: monitoring` |
| 8 | Register CMDB | AAP job | Register Service | `service_name: cmdb` |
| 9 | Register Backup | AAP job | Register Service | `service_name: backup` |
| 10 | Validate Server | AAP job | Validate Server | `server_name`, `server_ip` |
| 11 | Close Request | AAP job | Manage SNOW Request | `action: close` |

## Post-Demo Cleanup

```bash
ansible-playbook playbooks/terminate_demo_instances.yml
```

Terminates all EC2 instances tagged `managed_by: ao-overview-demo`.
