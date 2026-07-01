from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from guardweave.persistence.base import Base


class PolicyModel(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False, default="1.0")
    description = Column(Text, default="")
    trust_level = Column(String, nullable=False, default="medium")
    environment = Column(String, nullable=False, default="development")
    default_decision = Column(String, nullable=False, default="ask")
    policy_yaml = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)

    rules = relationship("RuleModel", back_populates="policy", cascade="all, delete-orphan")


class RuleModel(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True)
    policy_id = Column(String, ForeignKey("policies.id"), primary_key=True, nullable=False)
    description = Column(Text, default="")
    match_json = Column(JSON, default=dict)
    decision = Column(String, nullable=False)
    risk_score_modifier = Column(Integer, default=0)
    reason = Column(Text, default="")

    policy = relationship("PolicyModel", back_populates="rules")


class AuditEntryModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    agent_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)
    capability = Column(String, nullable=False)
    target = Column(Text, default="")
    decision = Column(String, nullable=False)
    risk_score = Column(Integer, default=0)
    risk_level = Column(String, default="low")
    policy_id = Column(String, default="")
    rule_id = Column(String, nullable=True)
    reason = Column(Text, default="")
    context = Column(JSON, default=dict)
    chain_hash = Column(String, default="")
    previous_hash = Column(String, default="")
    metadata_json = Column(JSON, default=dict)


class ApprovalRequestModel(Base):
    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)
    capability = Column(String, nullable=False)
    target = Column(Text, default="")
    risk_score = Column(Integer, default=0)
    risk_level = Column(String, default="medium")
    context = Column(JSON, default=dict)
    status = Column(String, nullable=False, default="pending", index=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String, nullable=True)
    feedback = Column(Text, nullable=True)
    escalation_level = Column(Integer, default=0)
    timeout_seconds = Column(Integer, default=300)
    policy_id = Column(String, default="")
