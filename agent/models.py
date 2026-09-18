from typing import Any, Literal
from pydantic import BaseModel

ActionType = Literal["goto", "fill", "click", "extract_text", "assert_text"]

class Target(BaseModel):
    strategy: Literal["url", "label", "text", "role_text"]
    value: str

class Step(BaseModel):
    id: str
    action: ActionType
    target: Target
    value: str | None = None
    rationale: str = ""
    timeout_ms: int = 5000
    retry_count: int = 1

class CapabilityArtifact(BaseModel):
    capability_id: str
    version: int
    description: str
    target_surface: dict[str, Any]
    inputs: list[dict[str, Any]]
    steps: list[Step]
    outputs: list[dict[str, Any]]
    checkpoint: dict[str, Any]
    safety: dict[str, Any]
