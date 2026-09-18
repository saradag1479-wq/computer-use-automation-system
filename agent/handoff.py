from dataclasses import dataclass, asdict
from pathlib import Path
import json

@dataclass
class HandoffRequest:
    capability_id: str
    goal: str
    session_id: str
    current_step: str
    state: str
    screenshot: str | None
    reason: str

def create_handoff(request, path="evidence/handoff.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(asdict(request), indent=2), encoding="utf-8")
