import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from agent.models import CapabilityArtifact
from agent.safety import validate_action, validate_url

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--member-id", required=True)
    args = parser.parse_args()

    artifact = CapabilityArtifact.model_validate_json(
        Path(args.artifact).read_text(encoding="utf-8")
    )

    base_url = artifact.target_surface["base_url"]
    validate_url(base_url, artifact.safety["allowed_domains"])

    result = {
        "capability_id": artifact.capability_id,
        "version": artifact.version,
        "status": "failed",
        "output": None,
        "error_type": None,
        "failed_step": None
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(base_url)

            for step in artifact.steps:
                validate_action(step.action)
                result["failed_step"] = step.id

                if step.action == "goto":
                    page.goto(step.target.value)

                elif step.action == "fill":
                    value = (
                        args.member_id
                        if step.value == "{{member_id}}"
                        else (step.value or "")
                    )

                    try:
                        page.get_by_label(step.target.value).fill(value)
                    except PlaywrightTimeoutError:
                        page.locator("#member-id").fill(value)

                elif step.action == "click":
                    page.get_by_role(
                        "button",
                        name=step.target.value
                    ).click()

                elif step.action == "extract_text":
                    result["output"] = page.get_by_role(
                        "status"
                    ).inner_text()

                elif step.action == "assert_text":
                    body = page.locator("body").inner_text()

                    if "Member not found" in body:
                        result["status"] = "business_outcome"
                        result["business_outcome"] = "member_not_found"
                        return finish(result)

                    if step.target.value not in body:
                        raise RuntimeError(
                            "Replay checkpoint failed."
                        )

            result["status"] = "success"
            result["failed_step"] = None

        except PlaywrightTimeoutError as exc:
            result["error_type"] = "recoverable_timeout"
            result["error"] = str(exc)

        except Exception as exc:
            result["error_type"] = "hard_failure"
            result["error"] = str(exc)

        finally:
            Path("evidence").mkdir(exist_ok=True)
            page.screenshot(
                path="evidence/replay.png",
                full_page=True
            )
            browser.close()

    finish(result)

def finish(result):
    Path("evidence/replay_result.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
