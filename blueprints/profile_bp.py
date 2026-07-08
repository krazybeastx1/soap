"""Profile blueprint: shows the JWT payload and the flag (when admin)."""
import hashlib

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from utils.auth import (
    PUBLIC_KEY,
    current_user_from_cookie,
    verify_token,
)
from utils.helpers import read_flag

profile_bp = Blueprint("profile", __name__)


def _company_info():
    return {
        "name": "SOAP Company",
        "tagline": "Clean engineering since 2014",
        "address": "1 Soap Plaza, Bubbleton",
        "founded": "2014",
    }


@profile_bp.route("/profile")
def profile():
    user = current_user_from_cookie()
    if not user:
        return redirect(url_for("auth.queue"))

    is_admin = (user.get("role") == "admin")
    flag = read_flag() if is_admin else None

    return render_template(
        "profile.html",
        user=user,
        company=_company_info(),
        is_admin=is_admin,
        flag=flag,
    )


@profile_bp.route("/api/debug/token")
def debug_token():
    """
    Diagnostic endpoint. Returns the public key bytes the server uses to
    verify HS256 (sha256 fingerprint + length), and the result of verifying
    the current `soap_token` cookie. Useful when a forged token doesn't
    validate — confirms whether the key on the server matches the key the
    client used to sign.
    """
    token = request.cookies.get("soap_token", "")
    payload, err = verify_token(token) if token else (None, "no cookie")

    pub_bytes = PUBLIC_KEY.encode("utf-8")
    return jsonify({
        "server_public_key": {
            "sha256": hashlib.sha256(pub_bytes).hexdigest(),
            "length": len(pub_bytes),
            "preview": pub_bytes[:60].decode("utf-8", errors="replace") + "...",
        },
        "token_seen": bool(token),
        "token_error": err,
        "token_payload": payload,
    })
