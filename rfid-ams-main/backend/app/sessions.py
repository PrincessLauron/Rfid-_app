from datetime import timedelta
from fastapi import Request, Response
from typing import Optional

ACCESS_COOKIE = "ams_access"
REFRESH_COOKIE = "ams_refresh"


def set_tokens_in_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # Short-lived access cookie, HttpOnly
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=int(timedelta(minutes=30).total_seconds()),
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )
    # Longer-lived refresh cookie
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=int(timedelta(days=7).total_seconds()),
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )


def clear_tokens(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def get_access_from_cookies(request: Request) -> Optional[str]:
    return request.cookies.get(ACCESS_COOKIE)


def get_refresh_from_cookies(request: Request) -> Optional[str]:
    return request.cookies.get(REFRESH_COOKIE)


