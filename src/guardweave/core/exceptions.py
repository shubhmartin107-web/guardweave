class GuardWeaveError(Exception):
    pass


class PolicyNotFoundError(GuardWeaveError):
    pass


class PolicyParseError(GuardWeaveError):
    pass


class ActionDeniedError(GuardWeaveError):
    pass


class ActionRequiresApprovalError(GuardWeaveError):
    pass


class ApprovalTimeoutError(GuardWeaveError):
    pass


class InvalidCapabilityError(GuardWeaveError):
    pass


class AuditChainBrokenError(GuardWeaveError):
    pass


class AgentNotFoundError(GuardWeaveError):
    pass
