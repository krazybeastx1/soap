"""Queue helpers used by the queue and login blueprints."""
import time

from utils.auth import (
    JWT_COOKIE,
    QUEUE_COOKIE,
    issue_token,
)
from utils.helpers import generate_queue_number

# Mock positions for the waiting spinner. Pure cosmetic.
QUEUE_POSITIONS = {
    1: "Arriving at the queue...",
    2: "Verifying your request...",
    3: "Allocating a SOAP handler...",
    4: "Almost there...",
    5: "Forwarding you to the portal...",
}

COUNTDOWN_SECONDS = 5


def build_session(response, queue_number: str):
    """Mint a JWT for the queue number and write it into the response cookies."""
    token = issue_token(sub=queue_number, role="user", queue=queue_number)
    response.set_cookie(
        JWT_COOKIE,
        token,
        httponly=True,
        samesite="Lax",
        max_age=60 * 60,
    )
    response.set_cookie(
        QUEUE_COOKIE,
        queue_number,
        httponly=False,
        samesite="Lax",
        max_age=60 * 60,
    )
    return token


def fresh_queue_number() -> str:
    return generate_queue_number()


def progress_message(elapsed: int) -> str:
    step = min(elapsed + 1, len(QUEUE_POSITIONS))
    return QUEUE_POSITIONS.get(step, "Finalising...")


def percent_complete(elapsed: int) -> int:
    if COUNTDOWN_SECONDS <= 0:
        return 100
    return min(100, int((elapsed / COUNTDOWN_SECONDS) * 100))


def remaining_seconds(elapsed: int) -> int:
    return max(0, COUNTDOWN_SECONDS - elapsed)
