"""SOAP Company Token Queue — entrypoint."""
import logging
import os
from flask import Flask, render_template

from blueprints.auth_bp import auth_bp
from blueprints.dashboard_bp import dashboard_bp
from blueprints.profile_bp import profile_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("SOAP_SECRET", "soap-company-default")
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="Page not found"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("error.html", code=500, message="Internal server error"), 500

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
