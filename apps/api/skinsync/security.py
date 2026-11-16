"""Authentication primitives: Argon2id passwords, signed access tokens, rotating refresh
tokens, CSRF double-submit, Redis rate limiting, auth dependencies.

Cookies (never localStorage):
  ss_access  HttpOnly, SameSite=Lax, path=/        short-lived signed token
  ss_refresh HttpOnly, SameSite=Lax, path=/api/v1/auth   opaque random secret (hash stored)
  ss_csrf    readable by JS, SameSite=Lax           echoed in X-CSRF-Token on unsafe requests
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, Request, Response
from sqlalchemy.engine import Connection

from . import db
from .config import get_settings
from .errors import AppError

ph = PasswordHasher()  # argon2-cffi defaults are Argon2id with RFC 9106 low-memory parameters
_DUMMY_HASH = ph.hash("timing-equaliser-not-a-real-password")
_COMMON = {p.strip().lower() for p in (Path(__file__).parent / "common_passwords.txt").read_text().splitlines()
           if p.strip() and not p.startswith("#")}

ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE = "ss_access", "ss_refresh", "ss_csrf"
HINT_COOKIE = "ss_signed_in"  # not a secret: only tells the client a refresh is worth trying
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


# ---------------------------------------------------------------- passwords
def validate_password(pw: str, email: str) -> None:
    if len(pw) < 10:
        raise AppError(422, "WEAK_PASSWORD", "Use at least 10 characters.")
    if len(pw) > 256:
        raise AppError(422, "WEAK_PASSWORD", "Use at most 256 characters.")
    low = pw.lower()
    core = low.rstrip("0123456789!@#$%&*.?_-")  # "password123!" -> "password"
    if low in _COMMON or core in _COMMON or low == email.lower() or low == email.split("@")[0].lower():
        raise AppError(422, "WEAK_PASSWORD", "That password is too common or too easy to guess.")


def hash_password(pw: str) -> str:
    return ph.hash(pw)


def verify_password(stored: str | None, pw: str) -> bool:
    try:
        return ph.verify(stored or _DUMMY_HASH, pw) and stored is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ---------------------------------------------------------------- signed tokens
def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign(payload: dict, purpose: str) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    mac = hmac.new(get_settings().secret_key.encode(), f"{purpose}.{body}".encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(mac)}"


def unsign(token: str, purpose: str) -> dict | None:
    try:
        body, mac = token.split(".", 1)
        want = hmac.new(get_settings().secret_key.encode(), f"{purpose}.{body}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(want, _unb64(mac)):
            return None
        data = json.loads(_unb64(body))
        if data.get("exp", 0) < time.time():
            return None
        return data
    except (ValueError, json.JSONDecodeError):
        return None


def token_hash(secret: str) -> bytes:
    return hashlib.sha256(secret.encode()).digest()


# ---------------------------------------------------------------- sessions
def _cookie_kwargs(path: str = "/") -> dict:
    s = get_settings()
    return dict(httponly=True, secure=s.cookie_secure, samesite="lax", path=path)


def issue_session(conn: Connection, response: Response, user_id: str, family_id: str | None = None) -> None:
    s = get_settings()
    access = sign({"sub": user_id, "exp": int(time.time()) + s.access_token_minutes * 60}, "access")
    refresh = secrets.token_urlsafe(32)
    db.execute(conn, """INSERT INTO refresh_tokens (user_id, family_id, token_hash, expires_at)
                        VALUES (:u, :f, :h, :e)""",
               u=user_id, f=family_id or str(uuid.uuid4()), h=token_hash(refresh),
               e=datetime.now(UTC) + timedelta(days=s.refresh_token_days))
    response.set_cookie(ACCESS_COOKIE, access, max_age=s.access_token_minutes * 60, **_cookie_kwargs())
    response.set_cookie(REFRESH_COOKIE, refresh, max_age=s.refresh_token_days * 86400,
                        **_cookie_kwargs("/api/v1/auth"))
    response.set_cookie(HINT_COOKIE, "1", max_age=s.refresh_token_days * 86400, httponly=False,
                        secure=s.cookie_secure, samesite="lax", path="/")


def rotate_refresh(conn: Connection, response: Response, refresh: str) -> str:
    rec = db.row(conn, "SELECT * FROM refresh_tokens WHERE token_hash = :h", h=token_hash(refresh))
    if rec is None or rec["expires_at"] < datetime.now(UTC):
        raise AppError(401, "UNAUTHENTICATED", "Please sign in again.")
    # Atomic claim: succeeds only for an unused, unrevoked token. A second use (theft or a race)
    # finds 0 rows and revokes the whole family.
    claimed = db.execute(conn, """UPDATE refresh_tokens SET used_at = now()
                                  WHERE id = :i AND used_at IS NULL AND revoked_at IS NULL""", i=rec["id"])
    if claimed != 1:
        with db.transaction() as c2:  # own transaction: must survive the 401 below
            db.execute(c2, "UPDATE refresh_tokens SET revoked_at = now() WHERE family_id = :f AND revoked_at IS NULL",
                       f=rec["family_id"])
            audit(c2, rec["user_id"], "security.refresh_reuse_detected", f"user:{rec['user_id']}")
        raise AppError(401, "UNAUTHENTICATED", "Please sign in again.")
    issue_session(conn, response, str(rec["user_id"]), str(rec["family_id"]))
    return str(rec["user_id"])


def end_session(conn: Connection, response: Response, refresh: str | None) -> None:
    if refresh:
        rec = db.row(conn, "SELECT family_id FROM refresh_tokens WHERE token_hash = :h", h=token_hash(refresh))
        if rec:
            db.execute(conn, "UPDATE refresh_tokens SET revoked_at = now() WHERE family_id = :f", f=rec["family_id"])
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    response.delete_cookie(HINT_COOKIE, path="/")


# ---------------------------------------------------------------- CSRF
def issue_csrf(response: Response) -> str:
    tok = secrets.token_urlsafe(24)
    s = get_settings()
    response.set_cookie(CSRF_COOKIE, tok, httponly=False, secure=s.cookie_secure, samesite="lax", path="/",
                        max_age=86400)
    return tok


def check_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get("x-csrf-token")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise AppError(403, "CSRF_FAILED", "Security check failed. Refresh the page and try again.")


# ---------------------------------------------------------------- rate limiting
_redis = None


def get_redis():
    global _redis
    if _redis is None:
        import redis

        _redis = redis.Redis.from_url(get_settings().redis_url, socket_timeout=0.5, socket_connect_timeout=0.5)
    return _redis


def rate_limit(bucket: str, limit: int, window_s: int):
    """Fixed-window limiter per client IP. Fails open if Redis is down (logged), so an
    outage of the cache never takes down core flows (NFR-03)."""

    def dep(request: Request):
        if not get_settings().rate_limit_enabled:
            return
        ip = request.client.host if request.client else "unknown"
        key = f"rl:{bucket}:{ip}:{int(time.time()) // window_s}"
        try:
            r = get_redis()
            n = r.incr(key)
            if n == 1:
                r.expire(key, window_s)
        except Exception:
            return
        if n > limit:
            raise AppError(429, "RATE_LIMITED", "Too many requests. Please wait a moment and try again.",
                           {"retry_after_seconds": window_s})

    return dep


def account_lock_check(email: str) -> None:
    """Per-account failed-login throttle, independent of IP."""
    try:
        n = int(get_redis().get(f"loginfail:{email.lower()}") or 0)
    except Exception:
        return
    if n >= 8:
        raise AppError(429, "RATE_LIMITED", "Too many sign-in attempts. Try again in 15 minutes.")


def account_fail(email: str) -> None:
    try:
        r = get_redis()
        k = f"loginfail:{email.lower()}"
        r.incr(k)
        r.expire(k, 900)
    except Exception:
        pass


def account_ok(email: str) -> None:
    try:
        get_redis().delete(f"loginfail:{email.lower()}")
    except Exception:
        pass


# ---------------------------------------------------------------- current user
@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    role: str
    email_verified: bool

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def optional_user(request: Request, conn: Connection = Depends(db.get_conn)) -> CurrentUser | None:
    tok = request.cookies.get(ACCESS_COOKIE)
    data = unsign(tok, "access") if tok else None
    if not data:
        return None
    rec = db.row(conn, "SELECT id, email, role, email_verified_at FROM users WHERE id = :i", i=data["sub"])
    if not rec:
        return None
    return CurrentUser(str(rec["id"]), rec["email"], rec["role"], rec["email_verified_at"] is not None)


def require_user(user: CurrentUser | None = Depends(optional_user)) -> CurrentUser:
    if user is None:
        raise AppError(401, "UNAUTHENTICATED", "Please sign in to use this feature.")
    return user


def require_admin(user: CurrentUser = Depends(require_user)) -> CurrentUser:
    if not user.is_admin:
        raise AppError(403, "FORBIDDEN", "Administrator access is required.")
    return user


def audit(conn: Connection, actor: str | None, action: str, target: str | None = None,
          old: dict | None = None, new: dict | None = None, reason: str | None = None,
          request_id: str | None = None) -> None:
    db.execute(conn, """INSERT INTO audit_log (actor_id, action, target, old_value, new_value, reason, request_id)
                        VALUES (:a, :ac, :t, CAST(:o AS jsonb), CAST(:n AS jsonb), :r, :rid)""",
               a=actor, ac=action, t=target, o=json.dumps(old) if old is not None else None,
               n=json.dumps(new, default=str) if new is not None else None, r=reason, rid=request_id)


def audit_now(actor, action, target=None, **kw) -> None:
    """Audit in a separate transaction so the record survives a failing request."""
    with db.transaction() as c:
        audit(c, actor, action, target, **kw)
