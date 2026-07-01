from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from guardweave.core.enums import (
    ApprovalStatus,
    Capability,
    Decision,
    RiskLevel,
    TrustLevel,
)


class RuleMatch(BaseModel):
    capabilities: list[Capability] | None = None
    targets: list[str] | None = None
    agents: list[str] | None = None
    sessions: list[str] | None = None
    risk_score_min: int | None = None
    risk_score_max: int | None = None


class Rule(BaseModel):
    id: str = Field(default_factory=lambda: f"rule_{uuid4().hex[:8]}")
    description: str = ""
    match: RuleMatch
    decision: Decision
    risk_score_modifier: int = 0
    reason: str = ""


class Policy(BaseModel):
    id: str = Field(default_factory=lambda: f"pol_{uuid4().hex[:8]}")
    name: str
    version: str = "1.0"
    description: str = ""
    trust_level: TrustLevel = TrustLevel.MEDIUM
    environment: str = "development"
    rules: list[Rule] = Field(default_factory=list)
    default_decision: Decision = Decision.ASK
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True


class AgentSession(BaseModel):
    agent_id: str
    session_id: str = Field(default_factory=lambda: f"ses_{uuid4().hex[:12]}")
    trust_level: TrustLevel = TrustLevel.MEDIUM
    environment: str = "development"
    declared_capabilities: list[Capability] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActionContext(BaseModel):
    agent_id: str
    session_id: str
    action: str
    capability: Capability
    target: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    trust_level: TrustLevel = TrustLevel.MEDIUM
    environment: str = "development"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityDeclaration(BaseModel):
    agent_id: str
    capabilities: list[Capability]
    trust_level: TrustLevel = TrustLevel.MEDIUM
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    id: str = Field(default_factory=lambda: f"eval_{uuid4().hex[:12]}")
    decision: Decision
    risk_score: int
    risk_level: RiskLevel
    matched_rule: Rule | None = None
    policy_id: str = ""
    reason: str = ""
    requires_approval: bool = False
    approval_request_id: str | None = None
    context: ActionContext | None = None


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"aud_{uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    agent_id: str
    session_id: str
    action: str
    capability: Capability
    target: str = ""
    decision: Decision
    risk_score: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    policy_id: str = ""
    rule_id: str | None = None
    reason: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    chain_hash: str = ""
    previous_hash: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"apr_{uuid4().hex[:12]}")
    agent_id: str
    session_id: str
    action: str
    capability: Capability
    target: str = ""
    risk_score: int = 0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    context: dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decided_at: datetime | None = None
    decided_by: str | None = None
    feedback: str | None = None
    escalation_level: int = 0
    timeout_seconds: int = 300
    policy_id: str = ""
    polices: list[Rule] | None = None
