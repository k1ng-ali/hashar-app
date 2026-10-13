from fastapi import APIRouter, Cookie, Depends, Request, Response, status

from app.core.config import REFRESH_TOKEN_EXPIRE, settings
from app.core.security import REFRESH_COOKIE_NAME
from app.deps.auth import get_current_user
from app.deps.services import get_auth_service
from app.schemas.auth import DeleteAccountIn, DevLoginIn, LoginIn, RegisterIn, TokenOut
from app.schemas.user import CurrentUser, DemoUserOut, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=int(REFRESH_TOKEN_EXPIRE.total_seconds()),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )


def _client_ip(request: Request) -> str | None:
    # За Cloudflare и Caddy реальный адрес выставляет uvicorn --proxy-headers (см. deploy/Caddyfile)
    return request.client.host if request.client else None


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterIn,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    token, refresh_token = await service.register(
        payload=payload, client_ip=_client_ip(request), user_agent=request.headers.get("user-agent")
    )
    _set_refresh_cookie(response, refresh_token)
    return token


@router.post("/login", response_model=TokenOut)
async def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    token, refresh_token = await service.login(
        payload=payload, client_ip=_client_ip(request), user_agent=request.headers.get("user-agent")
    )
    _set_refresh_cookie(response, refresh_token)
    return token


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
    service: AuthService = Depends(get_auth_service),
):
    token, new_refresh_token = await service.refresh(refresh_token=refresh_token)
    _set_refresh_cookie(response, new_refresh_token)
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
    service: AuthService = Depends(get_auth_service),
):
    await service.logout(refresh_token=refresh_token)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=COOKIE_PATH)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    await service.logout_all(user_id=user.id)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=COOKIE_PATH)


@router.get("/me", response_model=UserOut)
async def me(
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return await service.me(user_id=user.id)


@router.post("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    payload: DeleteAccountIn,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    await service.delete_account(user_id=user.id, payload=payload)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=COOKIE_PATH)


# ─── DEV_MODE ─────────────────────────────────────────────────────────────────


@router.get("/dev-users", response_model=list[DemoUserOut])
async def dev_users(service: AuthService = Depends(get_auth_service)):
    return await service.list_demo_users()


@router.post("/dev-login", response_model=TokenOut)
async def dev_login(
    payload: DevLoginIn,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    token, refresh_token = await service.dev_login(
        user_id=payload.user_id, user_agent=request.headers.get("user-agent")
    )
    _set_refresh_cookie(response, refresh_token)
    return token
