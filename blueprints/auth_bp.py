"""Auth blueprint: queue gate, login (queue number), logout."""
from flask import (
    Blueprint,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from utils.auth import (
    JWT_COOKIE,
    QUEUE_COOKIE,
    verify_token,
)
from utils.queue import (
    COUNTDOWN_SECONDS,
    build_session,
    fresh_queue_number,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def root():
    return redirect(url_for("auth.queue"))


@auth_bp.route("/queue")
def queue():
    queue_number = fresh_queue_number()
    response = make_response(
        render_template(
            "queue.html",
            queue_number=queue_number,
            countdown=COUNTDOWN_SECONDS,
        )
    )
    build_session(response, queue_number)
    return response


@auth_bp.route("/api/queue/regenerate", methods=["POST"])
def regenerate_queue():
    queue_number = fresh_queue_number()
    response = make_response({"queue_number": queue_number}, 200)
    build_session(response, queue_number)
    return response


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        entered = (request.form.get("queue_number") or "").strip()
        cookie_queue = request.cookies.get(QUEUE_COOKIE, "").strip()

        if not cookie_queue:
            return render_template(
                "login.html",
                error="Queue session expired. Please request a new ticket.",
                queue_hint=None,
            )

        if not entered:
            return render_template(
                "login.html",
                error="Please enter your queue number.",
                queue_hint=cookie_queue,
            )

        if entered != cookie_queue:
            return render_template(
                "login.html",
                error="Invalid Queue Number",
                queue_hint=cookie_queue,
            )

        token = request.cookies.get(JWT_COOKIE)
        payload, err = verify_token(token)
        if err or not payload:
            return redirect(url_for("auth.queue"))

        return redirect(url_for("dashboard.home"))

    return render_template(
        "login.html",
        error=None,
        queue_hint=request.cookies.get(QUEUE_COOKIE),
    )


@auth_bp.route("/logout")
def logout():
    response = redirect(url_for("auth.queue"))
    response.delete_cookie(JWT_COOKIE)
    response.delete_cookie(QUEUE_COOKIE)
    return response
