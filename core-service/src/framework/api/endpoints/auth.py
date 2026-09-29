from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from src.app.dtos.account import LoginData
from src.app.dtos.auth import AuthTokens, CurrentUser
from src.app.use_cases.auth import LogoutUser, LogUser, RefreshTokens
from src.domain.exceptions.users import InvalidRefreshToken, UserCantLog
from src.domain.value_objects.users import UserPrivileges
from src.framework.dependencies.authentication import (
    authorize_user,
    get_log_user,
    get_logout_user,
    get_refresh_tokens,
)
from src.shared.consts import ACCESS_COOKIE_NAME, AUTH_COOKIE_PATH, REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH
from src.shared.settings.application import app_settings

auth_router = APIRouter(tags=["auth"], prefix="/api")

cookie_secure = app_settings.COOKIE_SECURE
cookie_samesite = app_settings.COOKIE_SAMESITE


def set_auth_cookies(response: Response, tokens: AuthTokens) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=tokens.access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        max_age=tokens.access_expires_in,
        path=AUTH_COOKIE_PATH,
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=tokens.refresh_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        max_age=tokens.refresh_expires_in,
        path=REFRESH_COOKIE_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        path=AUTH_COOKIE_PATH,
    )
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        path=REFRESH_COOKIE_PATH,
    )


@auth_router.post(
    "/auth/login",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Incorrect logging data!"}},
)
async def log_user(
    log_user_: Annotated[LogUser, Depends(get_log_user)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    login_data = LoginData(username=form_data.username, password=form_data.password)

    try:
        tokens = await log_user_.execute(login_data)
    except UserCantLog:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="incorrect logging data!")

    response = JSONResponse({"ok": True})
    set_auth_cookies(response, tokens)

    return response


@auth_router.post(
    "/auth/refresh",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Invalid or expired refresh token!"}},
)
async def refresh_tokens(refresh_tokens_: Annotated[RefreshTokens, Depends(get_refresh_tokens)], request: Request):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing!")

    try:
        tokens = await refresh_tokens_.execute(refresh_token)
    except InvalidRefreshToken:
        response = JSONResponse({"detail": "Invalid refresh token!"}, status_code=status.HTTP_401_UNAUTHORIZED)
        clear_auth_cookies(response)
        return response

    response = JSONResponse({"ok": True})
    set_auth_cookies(response, tokens)

    return response


@auth_router.get(
    "/auth/me",
    response_model=CurrentUser,
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "User not logged."}},
    dependencies=[Depends(authorize_user)],
)
async def check_is_user_logged(request: Request) -> CurrentUser:
    user_id = request.state.user_id
    user_privileges: UserPrivileges | None = request.state.user_privileges

    if user_id is None or user_privileges is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        return CurrentUser(is_admin=user_privileges.is_admin)


@auth_router.post(
    "/auth/logout",
    dependencies=[Depends(authorize_user)],
)
async def logout_user(logout_user_: Annotated[LogoutUser, Depends(get_logout_user)], request: Request):
    session_id = request.state.session_id
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    await logout_user_.execute(session_id, refresh_token)

    response = JSONResponse({"ok": True})
    clear_auth_cookies(response)

    return response
