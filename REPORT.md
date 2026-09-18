# Architecture

I kept the system small and focused on one complete workflow rather than building a large platform.

The demo uses a local member back-office application. The discovery process opens the application, observes the current page, asks the LLM what action should be taken, and performs that action through Playwright.

After a successful run, the actions are saved as a structured capability. The replay process reads that capability and executes the saved actions directly. This keeps the model out of the production replay path.

The main components are:

- Demo back-office application
- LLM discovery process
- Capability artifact
- Deterministic replay process
- Safety checks
- Human handoff record
- Evidence/logging

# Artifact schema

The capability is stored as JSON.

It contains:

- capability ID and version
- target application
- input parameters
- ordered steps
- target strategy
- action type
- optional input value
- reason for the action
- expected output
- success checkpoint
- safety configuration

The artifact is intentionally separate from the original LLM conversation. This makes the capability easier to review, version, and replay.

Member ID is a runtime parameter represented as {{member_id}} in the saved capability. During replay, the value is supplied at runtime, so the same capability can be reused for different members without changing the workflow.
# Determinism & error handling

Replay does not call the LLM.

For each saved step, the runner finds the expected UI target, performs the action, and checks the expected result.

I separate failures into three practical groups:

- Business outcome: for example, the member does not exist.
- Recoverable problem: for example, a temporary timeout or dismissible UI condition.
- Hard failure: the expected target or checkpoint cannot be found after the allowed attempts.

This prevents a normal business result from being reported as a system failure.

# Heterogeneity & multi-tenant

Only one web surface is implemented for the assignment.

The browser interaction is kept behind a simple automation boundary so another implementation can later support a different type of surface, such as a legacy web application or desktop application.

For multiple institutions, capabilities would be associated with a tenant/application profile and version. When a vendor changes the UI, the affected capability can be reviewed and updated rather than changing the whole agent.

# Escalation & handoff

The agent creates a handoff request when it cannot safely continue.

The request records:

- task
- capability
- current step
- session
- current UI state
- screenshot
- reason for escalation

The current implementation records a structured handoff request containing the task, capability, current step, session information, UI state, screenshot, and reason for escalation. A production implementation would connect this handoff record to an operator interface that allows the human to take over the same live session and return control to automation.
A full co-browsing interface is intentionally not included.

# Safety

The demo uses an explicit allowlist for the application and browser actions.

Actions outside that list are rejected. Risky or irreversible actions would require a separate approval policy.

The system does not intentionally store passwords, access tokens, or full sensitive customer information in capability artifacts.

The demo uses synthetic member information only.

# Cuts

I intentionally did not build:

- production multi-tenant infrastructure
- a desktop automation implementation
- distributed workers
- a full operator/co-browsing UI
- a large capability marketplace
- complex deployment infrastructure

Those features would add breadth but would not demonstrate the central workflow as clearly as a small working vertical slice.
