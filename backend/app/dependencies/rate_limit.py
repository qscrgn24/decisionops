# ruff: noqa: B008
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status

from app.auth.models import User
from app.auth.session import get_current_user
from app.core.config import settings
from app.services.rate_limit import RateLimitExceeded, RateLimitPolicy, TokenBucketRateLimiter

SIGNUP_POLICY = RateLimitPolicy(name="signup", requests=settings.SIGNUP_RATE_LIMIT_REQUESTS, window_seconds=settings.SIGNUP_RATE_LIMIT_WINDOW_S)
LOGIN_POLICY = RateLimitPolicy(name="login", requests=settings.LOGIN_RATE_LIMIT_REQUESTS, window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_S)
UPLOAD_POLICY = RateLimitPolicy(name="dataset-upload", requests=settings.UPLOAD_RATE_LIMIT_REQUESTS, window_seconds=settings.UPLOAD_RATE_LIMIT_WINDOW_S)
PREVIEW_POLICY = RateLimitPolicy(name="dataset-preview", requests=settings.PREVIEW_RATE_LIMIT_REQUESTS, window_seconds=settings.PREVIEW_RATE_LIMIT_WINDOW_S)
RUN_CREATE_POLICY = RateLimitPolicy(name="run-create", requests=settings.RUN_CREATE_RATE_LIMIT_REQUESTS, window_seconds=settings.RUN_CREATE_RATE_LIMIT_WINDOW_S)
EXECUTE_POLICY = RateLimitPolicy(name="optimization-execute", requests=settings.EXECUTE_RATE_LIMIT_REQUESTS, window_seconds=settings.EXECUTE_RATE_LIMIT_WINDOW_S)
AUTH_READ_POLICY = RateLimitPolicy(name="authenticated-read", requests=settings.AUTH_READ_RATE_LIMIT_REQUESTS, window_seconds=settings.AUTH_READ_RATE_LIMIT_WINDOW_S)


def _get_limiter(request: Request) -> TokenBucketRateLimiter:
    limiter = getattr(request.app.state, "rate_limiter", None)

    if not isinstance(limiter, TokenBucketRateLimiter):
        raise RuntimeError("Rate limiter is not configured.")

    return limiter


def _enforce_limit(*, limiter: TokenBucketRateLimiter, identity: str, policy: RateLimitPolicy) -> None:
    try:
        limiter.check(identity=identity, policy=policy)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests.", headers={"Retry-After": str(exc.retry_after_seconds)}) from exc


def ip_rate_limit(policy: RateLimitPolicy) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        client = request.client
        identity = client.host if client is not None else "unknown"

        _enforce_limit(limiter=_get_limiter(request), identity=f"ip:{identity}", policy=policy)

    return dependency


def user_rate_limit(policy: RateLimitPolicy) -> Callable[..., None]:
    def dependency(request: Request, user: User = Depends(get_current_user)) -> None:
        _enforce_limit(limiter=_get_limiter(request), identity=f"user:{user.id}", policy=policy)

    return dependency


limit_signup = ip_rate_limit(SIGNUP_POLICY)
limit_login = ip_rate_limit(LOGIN_POLICY)
limit_upload = user_rate_limit(UPLOAD_POLICY)
limit_preview = user_rate_limit(PREVIEW_POLICY)
limit_run_create = user_rate_limit(RUN_CREATE_POLICY)
limit_execute = user_rate_limit(EXECUTE_POLICY)
limit_auth_read = user_rate_limit(AUTH_READ_POLICY)
