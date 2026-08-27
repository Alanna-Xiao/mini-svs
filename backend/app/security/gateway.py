import hmac
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


GATEWAY_HEADER = "x-mini-svs-gateway-token"


class GatewayAuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        expected_token = os.getenv("MINI_SVS_GATEWAY_TOKEN", "")
        supplied_token = request.headers.get(GATEWAY_HEADER, "")
        if expected_token and not hmac.compare_digest(expected_token, supplied_token):
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "gateway_auth_required",
                        "message": "A valid synthesis gateway token is required.",
                    }
                },
                headers={"cache-control": "no-store"},
            )
        return await call_next(request)
