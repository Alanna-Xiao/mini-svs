from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.errors import MiniSvsError


def create_app() -> FastAPI:
    app = FastAPI(title="mini-svs API", version="0.1.0")

    @app.exception_handler(MiniSvsError)
    async def handle_mini_svs_error(
        _request: Request, error: MiniSvsError
    ) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content=error.as_response())

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "location": [str(item) for item in issue["loc"]],
                "message": issue["msg"],
                "type": issue["type"],
            }
            for issue in error.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "The request body is invalid.",
                    "details": {"issues": details},
                }
            },
        )

    app.include_router(router)
    return app


app = create_app()
