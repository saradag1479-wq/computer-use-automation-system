# Computer-Use Automation System

## What this project does

The project demonstrates a small local synthetic back-office workflow for a banking-style member lookup.
Example task:

> Find member M1001 and report the member name and account status.

The first time, an LLM helps work through the browser screen. Once the task succeeds, the system saves the useful actions as a capability.

The next time, the saved capability is replayed directly. There is no LLM making decisions during replay.

## Simple flow

1. Open the member portal.
2. Read the current screen.
3. Decide what to click/type.
4. Complete the member lookup.
5. Save the successful steps.
6. The saved capability uses `{{member_id}}` as a runtime input. The same capability can therefore be replayed for different members without changing the saved workflow.
7. Stop and ask for a human when the system cannot safely continue.

## Run it

Create a virtual environment and install packages:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Start the demo application:

```bash
python -m uvicorn app.server:app --reload
```

Then run the saved capability:

```bash
python -m replay.runner --artifact artifacts/member_lookup.json --member-id M1001
```

## LLM discovery

The first run uses the LLM to discover the actions needed to complete the task on the live UI. After a successful run, those actions are saved as a reusable capability artifact.

Run discovery with:

python -m agent.discover --goal "Find member M1001 and report the member name and account status" --url "http://127.0.0.1:8000"

The saved capability can then be replayed with different member IDs. Replay does not use the LLM to decide what to do.

Example:

python -m replay.runner --artifact artifacts/member_lookup.json --member-id M1001

python -m replay.runner --artifact artifacts/member_lookup.json --member-id M1002

## Design choice

The important part is not the framework. The important part is the separation:

**LLM discovery -> saved capability -> deterministic replay**

The saved capability contains the actual steps needed to perform the job. Replay does not ask an LLM what to do next.

## Safety

The demo only allows the local application and a small set of browser actions. Credentials, tokens, and sensitive fields should not be stored in capabilities or logs.

## Human handoff

## Human handoff

If the agent gets stuck, the handoff record captures the task, current step, browser state, screenshot, and reason for escalation. In a production implementation, a human operator can then take over the same live session and return control to the automation.


## Submission notes

## Submission notes

The repository includes example discovery and replay evidence under `evidence/`. The demo uses synthetic local data only. No real credentials or customer data are included.

