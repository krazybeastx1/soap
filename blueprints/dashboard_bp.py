"""Dashboard blueprint: corporate landing page after queue login."""
from flask import Blueprint, redirect, render_template, request, url_for

from utils.auth import current_user_from_cookie

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def home():
    user = current_user_from_cookie()
    if not user:
        return redirect(url_for("auth.queue"))

    cards = [
        {
            "title": "Employee Profile",
            "icon": "user",
            "description": "View and update your personal information.",
            "href": url_for("profile.profile"),
        },
        {
            "title": "Documents",
            "icon": "doc",
            "description": "Access payslips, contracts, and tax forms.",
            "href": "#",
        },
        {
            "title": "Payroll",
            "icon": "wallet",
            "description": "Review your compensation and benefits.",
            "href": "#",
        },
        {
            "title": "HR",
            "icon": "people",
            "description": "Time off, performance reviews, training.",
            "href": "#",
        },
        {
            "title": "Support",
            "icon": "life-ring",
            "description": "Open a ticket with the IT help desk.",
            "href": "#",
        },
        {
            "title": "Internal News",
            "icon": "news",
            "description": "Latest company announcements.",
            "href": "#",
        },
    ]

    news = [
        {
            "date": "Today",
            "title": "Q2 All-Hands recap",
            "body": "Catch up on the highlights from the Q2 All-Hands meeting.",
        },
        {
            "date": "Yesterday",
            "title": "New queueing portal launched",
            "body": "The new ticket-based queue improves portal response times.",
        },
        {
            "date": "Mon",
            "title": "Office closure notice",
            "body": "The office will be closed on the upcoming public holiday.",
        },
    ]

    return render_template(
        "dashboard.html",
        user=user,
        cards=cards,
        news=news,
    )
