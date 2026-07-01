from enum import StrEnum


class Capability(StrEnum):
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    FILE_EXECUTE = "file:execute"
    NETWORK_HTTP = "network:http"
    NETWORK_RAW = "network:raw"
    CODE_EXEC = "code:exec"
    CODE_EVAL = "code:eval"
    SHELL = "shell"
    API_CALL = "api:call"
    DB_READ = "db:read"
    DB_WRITE = "db:write"
    DB_EXECUTE = "db:execute"
    SECRETS_ACCESS = "secrets:access"
    IDENTITY_IMPERSONATE = "identity:impersonate"
    DATA_EXFILTRATE = "data:exfiltrate-sensitive"
    AGENT_SPAWN = "agent:spawn"
    AGENT_TERMINATE = "agent:terminate"
    POLICY_MODIFY = "policy:modify"
    AUDIT_MODIFY = "audit:modify"


class TrustLevel(StrEnum):
    SANDBOX = "sandbox"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class RiskLevel(StrEnum):
    TRIVIAL = "trivial"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
