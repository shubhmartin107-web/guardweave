from __future__ import annotations

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from guardweave.core.enums import Capability, Decision, TrustLevel
from guardweave.sdk.guardweave import GuardWeave


class GuardWeaveMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        agent_id: str = "api-middleware",
        trust_level: TrustLevel = TrustLevel.MEDIUM,
        environment: str = "production",
        excluded_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self._gw = GuardWeave(
            agent_id=agent_id,
            trust_level=trust_level,
            environment=environment,
        )
        self._excluded_paths = excluded_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if any(path.startswith(ex) for ex in self._excluded_paths):
            return await call_next(request)

        method = request.method
        is_write = method in ("POST", "PUT", "PATCH", "DELETE")
        capability = Capability.API_CALL
        if is_write:
            capability = Capability.FILE_WRITE if "/file" in path else Capability.API_CALL

        try:
            result = await self._gw.check_action(
                action=f"{method}:{path}",
                capability=capability,
                target=path,
                parameters={"method": method, "query": str(request.query_params)},
            )
            if result.decision == Decision.DENY:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Action denied by GuardWeave policy",
                        "reason": result.reason,
                        "risk_score": result.risk_score,
                        "risk_level": result.risk_level.value,
                    },
                )
            return await call_next(request)
        except Exception as e:
            return JSONResponse(
                status_code=403,
                content={"error": f"GuardWeave blocked request: {e!s}"},
            )
