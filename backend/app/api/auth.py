from fastapi import APIRouter, Cookie, Depends, Request, Response, status

from app.core.config import REFRESH_TOKEN_EXPIRE, TRUSTED_DEVICE_EXPIRE, settings
from app.core.security import DEVICE_COOKIE_NAME, REFRESH_COOKIE_NAME
from app.deps.auth import get_current_user
from app.deps.services import get_auth_service
from app.schemas.auth import (
    ChallengeOut,
    DeleteAccountIn,
    DevLoginIn,
    ForgotPasswordIn,
    GoogleLoginIn,
    GoogleVerifyIn,
    LoginIn,
    PhoneCodeIn,
    RegisterIn,
    SmsSendIn,
    SmsSentOut,
    SmsVerifyIn,
    TokenOut,
    UpdateProfileIn,
)
from app.schemas.user import CurrentUser, DemoUserOut, UserOut
from app.services.auth_service import AuthResult, AuthService

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


def _set_device_cookie(response: Response, device_token: str) -> None:
    response.set_cookie(
        key=DEVICE_COOKIE_NAME,
        value=device_token,
        max_age=int(TRUSTED_DEVICE_EXPIRE.total_seconds()),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )


def _respond(response: Response, result: AuthResult) -> TokenOut | ChallengeOut:
    """Сессия — с cookie; challenge — сначала подтвердить личность."""
    if result.challenge:
        return result.challenge
    _set_refresh_cookie(response, result.refresh_token)
    if result.device_token:
        _set_device_cookie(response, result.device_token)
    return result.token


def _client_ip(request: Request) -> str | None:
    # За Cloudflare и Caddy реальный адрес выставляет uvicorn --proxy-headers (см. deploy/Caddyfile)
    return request.client.host if request.client else None


@router.post("/register", response_model=ChallengeOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterIn,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    """Создаёт неподтверждённый аккаунт; сессию выдаст /auth/verify/*."""
    return _respond(response, await service.register(payload=payload, client_ip=_client_ip(request)))


@router.post("/login", response_model=TokenOut | ChallengeOut)
async def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    device_token: str | None = Cookie(None, alias=DEVICE_COOKIE_NAME),
    service: AuthService = Depends(get_auth_service),
):
    """Сессия — на подтверждённом устройстве; иначе challenge для /auth/verify/*."""
    result = await service.login(
        payload=payload,
        client_ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        device_token=device_token,
    )
    return _respond(response, result)


@router.post("/google", response_model=TokenOut)
async def google_login(
    payload: GoogleLoginIn,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.google_login(
        payload=payload, client_ip=_client_ip(request), user_agent=request.headers.get("user-agent")
    )
    return _respond(response, result)


# ─── Подтверждение личности ───────────────────────────────────────────────────


@router.post("/verify/sms/send", response_model=SmsSentOut)
async def send_sms_code(
    payload: SmsSendIn,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    return await service.send_sms_code(payload=payload, client_ip=_client_ip(request))


@router.post("/verify/sms", response_model=TokenOut)
async def verify_sms(
    payload: SmsVerifyIn,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.verify_sms(
        payload=payload, client_ip=_client_ip(request), user_agent=request.headers.get("user-agent")
    )
    return _respond(response, result)


@router.post("/verify/google", response_model=TokenOut)
async def verify_google(
    payload: GoogleVerifyIn,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.verify_google(
        payload=payload, client_ip=_client_ip(request), user_agent=request.headers.get("user-agent")
    )
    return _respond(response, result)


@router.post("/password/forgot", response_model=ChallengeOut)
async def forgot_password(
    payload: ForgotPasswordIn,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Новый пароль задаётся вместе с подтверждением: /auth/verify/* с new_password."""
    return await service.forgot_password(payload=payload, client_ip=_client_ip(request))


@router.post("/password/change", response_model=ChallengeOut)
async def change_password(
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return await service.password_challenge(user_id=user.id)


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


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UpdateProfileIn,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return await service.update_profile(user_id=user.id, payload=payload, client_ip=_client_ip(request))


@router.post("/me/phone/code", response_model=SmsSentOut)
async def send_phone_code(
    payload: PhoneCodeIn,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Код из SMS на новый номер +992 — затем PATCH /auth/me с этим кодом."""
    return await service.send_phone_code(user_id=user.id, payload=payload, client_ip=_client_ip(request))


@router.post("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    payload: DeleteAccountIn,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    await service.delete_account(user_id=user.id, payload=payload)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=COOKIE_PATH)
    response.delete_cookie(key=DEVICE_COOKIE_NAME, path=COOKIE_PATH)


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
