import argparse
import json
import os
import uuid
from pathlib import Path

from openai import OpenAI
from playwright.sync_api import sync_playwright

from agent.models import CapabilityArtifact, Step
from agent.safety import validate_action, validate_url, redact
from agent.handoff import HandoffRequest, create_handoff

SYSTEM_PROMPT = '''You are helping operate a local back-office browser application.

Use only these actions:
goto, fill, click, extract_text, assert_text.

Prefer labels and visible text instead of coordinates.

Return JSON only:
{"steps":[
  {
    "id": "s1",
    "action": "goto|fill|click|extract_text|assert_text",
    "target": {"strategy": "url|label|text|role_text", "value": "..."},
    "value": "...",
    "rationale": "..."
  }
]}
'''

def ask_llm(goal, observation):
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.getenv("LLM_BASE_URL") or None
    )

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Goal: {goal}\n\n"
                    f"Current page:\n{observation}\n\n"
                    "Create the smallest safe sequence of actions."
                )
            }
        ]
    )

    return json.loads(response.choices[0].message.content)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    validate_url(args.url, ["127.0.0.1", "localhost"])

    session_id = str(uuid.uuid4())
    Path("evidence").mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(args.url)
            observation = page.locator("body").inner_text()

            page.screenshot(
                path="evidence/discovery_start.png",
                full_page=True
            )

            plan = ask_llm(args.goal, observation)
            steps = []

            for raw in plan["steps"]:
                validate_action(raw["action"])
                step = Step(**raw)

                if step.action == "goto":
                    page.goto(step.target.value)

                elif step.action == "fill":
                    page.get_by_label(step.target.value).fill(
                        step.value or ""
                    )

                elif step.action == "click":
                    page.get_by_role(
                        "button",
                        name=step.target.value
                    ).click()

                elif step.action == "extract_text":
                    page.get_by_role("status").inner_text()

                elif step.action == "assert_text":
                    body = page.locator("body").inner_text()
                    if step.target.value not in body:
                        raise RuntimeError(
                            "Expected checkpoint was not found."
                        )

                steps.append(step)

            artifact = CapabilityArtifact(
                capability_id="member_lookup",
                version=1,
                description=args.goal,
                target_surface={"base_url": args.url},
                inputs=[
                    {
                        "name": "member_id",
                        "type": "string",
                        "required": True
                    }
                ],
                steps=steps,
                outputs=[
                    {"name": "result", "type": "string"}
                ],
                checkpoint={
                    "type": "text_contains",
                    "value": "Member Name:"
                },
                safety={
                    "allowed_domains": ["127.0.0.1", "localhost"],
                    "allowed_actions": sorted(
                        [
                            "goto",
                            "fill",
                            "click",
                            "extract_text",
                            "assert_text"
                        ]
                    )
                }
            )

            Path("artifacts").mkdir(exist_ok=True)
            Path("artifacts/member_lookup.json").write_text(
                artifact.model_dump_json(indent=2),
                encoding="utf-8"
            )

            Path("evidence/discovery_log.json").write_text(
                json.dumps(
                    {
                        "session_id": session_id,
                        "goal": args.goal,
                        "status": "success",
                        "steps": len(steps),
                        "observation": redact(observation)
                    },
                    indent=2
                ),
                encoding="utf-8"
            )

            page.screenshot(
                path="evidence/discovery_success.png",
                full_page=True
            )

        except Exception as exc:
            page.screenshot(
                path="evidence/discovery_failure.png",
                full_page=True
            )

            create_handoff(
                HandoffRequest(
                    capability_id="member_lookup",
                    goal=args.goal,
                    session_id=session_id,
                    current_step="discovery",
                    state=redact(page.locator("body").inner_text()),
                    screenshot="evidence/discovery_failure.png",
                    reason=str(exc)
                )
            )
            raise

        finally:
            browser.close()

if __name__ == "__main__":
    main()
