"""Sign-up, sign-in, refresh rotation, sign-out, email verification, password reset.

No account enumeration: sign-up for an existing email, unknown-email sign-in and reset
requests all return the same responses as the success path.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response
from pydantic import EmailStr, Field
from sqlalchemy.engine import Connection

from .. import db, mailer
from ..config import get_settings
from ..errors import AppError
from ..security import (
    REFRESH_COOKIE,
    account_fail,
    account_lock_check,
    account_ok,
    audit,
    audit_now,
    end_session,
    hash_password,
    issue_csrf,
    issue_session,
    rate_limit,
    rotate_refresh,
    token_hash,
    validate_password,
    verify_password,
)
from .common import Strict

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupIn(Strict):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    age_confirmed_18: bool
    accept_terms: bool


class LoginIn(Strict):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    claim_tokens: list[str] = Field(default_factory=list, max_length=20)


class EmailIn(Strict):
    email: EmailStr


class TokenIn(Strict):
    token: str = Field(min_length=10, max_length=200)


class ResetIn(Strict):
    token: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=1, max_length=256)


def _one_time_token(conn: Connection, user_id, purpose: str, minutes: int) -> str:
    tok = secrets.token_urlsafe(32)
    db.execute(conn, """INSERT INTO auth_tokens (token_hash, user_id, purpose, expires_at) VALUES (:h, :u, :p, :e)""",
               h=token_hash(tok), u=user_id, p=purpose, e=datetime.now(UTC) + timedelta(minutes=minutes))
    return tok


def _consume(conn: Connection, tok: str, purpose: str):
    rec = db.row(conn, """SELECT * FROM auth_tokens WHERE token_hash = :h AND purpose = :p FOR UPDATE""",
                 h=token_hash(tok), p=purpose)
    if not rec or rec["used_at"] or rec["expires_at"] < datetime.now(UTC):
        raise AppError(400, "INVALID_TOKEN", "This link is invalid or has expired.")
    db.execute(conn, "UPDATE auth_tokens SET used_at = now() WHERE token_hash = :h", h=rec["token_hash"])
    return rec["user_id"]


def _claim_all(conn, tokens: list[str], user_id: str) -> int:
    from ..services import comparisons

    return sum(1 for t in tokens if comparisons.claim(conn, t, user_id))


@router.get("/csrf")
def csrf(response: Response):
    return {"csrf_token": issue_csrf(response)}


@router.post("/signup", status_code=202, dependencies=[Depends(rate_limit("signup", 10, 3600))])
def signup(body: SignupIn, request: Request, conn: Connection = Depends(db.get_conn)):
    if not body.age_confirmed_18:
        raise AppError(422, "AGE_REQUIRED", "You must be 18 or older to create an account.")
    if not body.accept_terms:
        raise AppError(422, "TERMS_REQUIRED", "Please accept the terms to continue.")
    validate_password(body.password, body.email)
    generic = {"status": "check_email",
               "message": "If this email can be registered, we have sent a confirmation link."}
    if db.scalar(conn, "SELECT 1 FROM users WHERE email_lower = lower(:e)", e=body.email):
        mailer.send(body.email, "SkinSync sign-up attempt",
                    "Someone tried to create an account with this email. If it was you, sign in or reset your password.")
        return generic
    uid = str(db.scalar(conn, """INSERT INTO users (email, password_hash, age_confirmed_18)
                                 VALUES (:e, :h, true) RETURNING id""", e=body.email, h=hash_password(body.password)))
    db.execute(conn, "INSERT INTO profiles (user_id) VALUES (:u)", u=uid)
    v = get_settings().policy_version
    db.execute(conn, "INSERT INTO consents (user_id, purpose, policy_version, granted) VALUES (:u, 'terms', :v, true)",
               u=uid, v=v)
    tok = _one_time_token(conn, uid, "verify_email", 60 * 24)
    mailer.send(body.email, "Confirm your SkinSync email",
                f"Confirm your email: {get_settings().public_base_url}/auth/verify?token={tok}\nThe link expires in 24 hours.")
    audit(conn, uid, "auth.signup", f"user:{uid}", request_id=request.state.request_id)
    # Same response whether or not the email was already registered (no enumeration).
    # Guest results are claimed at first sign-in, after the email is confirmed.
    return generic


@router.post("/login", dependencies=[Depends(rate_limit("login", 20, 300))])
def login(body: LoginIn, request: Request, response: Response, conn: Connection = Depends(db.get_conn)):
    account_lock_check(body.email)
    u = db.row(conn, "SELECT id, password_hash FROM users WHERE email_lower = lower(:e)", e=body.email)
    if not verify_password(u["password_hash"] if u else None, body.password):
        account_fail(body.email)
        if u:
            audit_now(str(u["id"]), "auth.login_failed", f"user:{u['id']}", request_id=request.state.request_id)
        raise AppError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    account_ok(body.email)
    uid = str(u["id"])
    if not db.scalar(conn, "SELECT email_verified_at IS NOT NULL FROM users WHERE id = :u", u=uid):
        raise AppError(403, "EMAIL_NOT_VERIFIED", "Confirm your email first. We sent you a link when you signed up.",
                       {"can_resend": True})
    issue_session(conn, response, uid)
    audit(conn, uid, "auth.login", f"user:{uid}", request_id=request.state.request_id)
    return {"signed_in": True, "claimed_results": _claim_all(conn, body.claim_tokens, uid)}


@router.post("/refresh", dependencies=[Depends(rate_limit("refresh", 60, 300))])
def refresh(request: Request, response: Response, conn: Connection = Depends(db.get_conn)):
    tok = request.cookies.get(REFRESH_COOKIE)
    if not tok:
        raise AppError(401, "UNAUTHENTICATED", "Please sign in again.")
    rotate_refresh(conn, response, tok)
    return {"refreshed": True}


@router.post("/logout")
def logout(request: Request, response: Response, conn: Connection = Depends(db.get_conn)):
    end_session(conn, response, request.cookies.get(REFRESH_COOKIE))
    return {"signed_out": True}


@router.post("/verify-email")
def verify_email(body: TokenIn, conn: Connection = Depends(db.get_conn)):
    uid = _consume(conn, body.token, "verify_email")
    db.execute(conn, "UPDATE users SET email_verified_at = coalesce(email_verified_at, now()) WHERE id = :u", u=uid)
    return {"verified": True}


@router.post("/resend-verification", status_code=202, dependencies=[Depends(rate_limit("reset", 5, 3600))])
def resend_verification(body: EmailIn, conn: Connection = Depends(db.get_conn)):
    u = db.row(conn, "SELECT id FROM users WHERE email_lower = lower(:e) AND email_verified_at IS NULL", e=body.email)
    if u:
        tok = _one_time_token(conn, u["id"], "verify_email", 60 * 24)
        mailer.send(body.email, "Confirm your SkinSync email",
                    f"Confirm your email: {get_settings().public_base_url}/auth/verify?token={tok}")
    return {"status": "check_email"}


@router.post("/request-password-reset", status_code=202, dependencies=[Depends(rate_limit("reset", 5, 3600))])
def request_reset(body: EmailIn, conn: Connection = Depends(db.get_conn)):
    u = db.row(conn, "SELECT id FROM users WHERE email_lower = lower(:e)", e=body.email)
    if u:
        tok = _one_time_token(conn, u["id"], "reset_password", 30)
        mailer.send(body.email, "Reset your SkinSync password",
                    f"Reset your password: {get_settings().public_base_url}/auth/reset?token={tok}\n"
                    "The link expires in 30 minutes. If you did not ask for this, ignore this email.")
    return {"status": "check_email", "message": "If an account exists for this email, we have sent a reset link."}


@router.post("/reset-password", dependencies=[Depends(rate_limit("reset", 10, 3600))])
def reset_password(body: ResetIn, request: Request, response: Response, conn: Connection = Depends(db.get_conn)):
    uid = _consume(conn, body.token, "reset_password")
    email = db.scalar(conn, "SELECT email FROM users WHERE id = :u", u=uid)
    validate_password(body.password, email)
    db.execute(conn, "UPDATE users SET password_hash = :h, updated_at = now() WHERE id = :u",
               h=hash_password(body.password), u=uid)
    db.execute(conn, "UPDATE refresh_tokens SET revoked_at = now() WHERE user_id = :u AND revoked_at IS NULL", u=uid)
    audit(conn, str(uid), "auth.password_reset", f"user:{uid}", request_id=request.state.request_id)
    end_session(conn, response, None)
    return {"reset": True}
