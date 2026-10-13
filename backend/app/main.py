from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.modules.auth.api.router import me_router
from app.modules.auth.api.router import router as auth_router
from app.modules.sync.api.router import router as sync_router
from app.shared.errors import DomainError, TooManyRequestsError, UnauthorizedError


def create_app() -> FastAPI:
    app = FastAPI(title="BackFinanzas", version="0.1.0")
    # Solo el origen del frontend; con credenciales porque la cookie de refresh es httpOnly.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[get_settings().frontend_url.rstrip("/")],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        status = 422
        if isinstance(exc, UnauthorizedError):
            status = 401
        elif isinstance(exc, TooManyRequestsError):
            status = 429
        return JSONResponse(status_code=status, content={"code": exc.code, "message": exc.message})

    app.include_router(auth_router)
    app.include_router(me_router)
    app.include_router(sync_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
