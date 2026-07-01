from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any

from guardweave.core.enums import Capability, Decision, TrustLevel
from guardweave.core.exceptions import ActionDeniedError, ActionRequiresApprovalError
from guardweave.sdk.guardweave import GuardWeave


def guardweave(
    capability: Capability,
    trust_level: TrustLevel = TrustLevel.MEDIUM,
    environment: str | None = None,
    agent_id: str | None = None,
    deny_message: str = "Action blocked by GuardWeave policy.",
    raise_on_deny: bool = True,
) -> Callable[..., Any]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        gw_instance = GuardWeave(
            agent_id=agent_id,
            trust_level=trust_level,
            environment=environment,
        )

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    result = await gw_instance.check_action(
                        action=func.__name__,
                        capability=capability,
                        target=kwargs.get("target", kwargs.get("path", "")),
                        parameters={"args": str(args), "kwargs": str(kwargs)},
                    )
                    if result.decision == Decision.ALLOW:
                        return await func(*args, **kwargs)
                    elif result.decision == Decision.ASK:
                        raise ActionRequiresApprovalError(
                            f"Action '{func.__name__}' requires approval. "
                            f"Request ID: {result.approval_request_id}"
                        )
                    else:
                        if raise_on_deny:
                            raise ActionDeniedError(deny_message)
                        return None
                except (ActionDeniedError, ActionRequiresApprovalError):
                    raise
                except Exception as e:
                    await gw_instance.log_action(
                        action=func.__name__,
                        capability=capability,
                        decision=Decision.DENY,
                        reason=f"Error during guard check: {e}",
                    )
                    if raise_on_deny:
                        raise ActionDeniedError(deny_message) from e
                    return None

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(
                        gw_instance.check_action(
                            action=func.__name__,
                            capability=capability,
                            target=kwargs.get("target", kwargs.get("path", "")),
                            parameters={"args": str(args), "kwargs": str(kwargs)},
                        )
                    )
                    if result.decision == Decision.ALLOW:
                        return func(*args, **kwargs)
                    else:
                        if raise_on_deny:
                            raise ActionDeniedError(deny_message)
                        return None
                finally:
                    loop.close()

            return sync_wrapper

    return decorator
