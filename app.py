from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import connect_db
from extensions import db, bcrypt, jwt
from seed import run_seed

from routes.auth         import auth_bp
from routes.requests      import requests_bp
from routes.sos          import sos_bp
from routes.volunteer    import volunteer_bp
from routes.admin        import admin_bp
from routes.wallet       import wallet_bp
from routes.ai_voice     import ai_bp
from routes.geolocation  import geo_bp
from routes.twilio_voice import twilio_bp

try:
    from routes.Subscription import sub_bp
except ImportError:
    from routes.Subscription import sub_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/*": {"origins": "*"}},
         allow_headers=["Content-Type", "Authorization", "Accept"],
         methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
         supports_credentials=False)

    @app.after_request
    def add_cors(response):
        response.headers["Access-Control-Allow-Origin"]  = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        return response

    @app.route("/api/<path:path>", methods=["OPTIONS"])
    def options(path):
        return jsonify({"ok": True}), 200

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    connect_db(app)

    with app.app_context():
        db.create_all()
        print("✅ All tables ready (Users, Requests, WellnessCalls, CareWallets, Transactions)")
        run_seed(app)

    # ── Register all blueprints ───────────────────────────────────────────────
    app.register_blueprint(auth_bp,      url_prefix="/api/auth")
    app.register_blueprint(requests_bp,  url_prefix="/api/requests")
    app.register_blueprint(sos_bp,       url_prefix="/api/sos")
    app.register_blueprint(volunteer_bp, url_prefix="/api/volunteer")
    app.register_blueprint(sub_bp,       url_prefix="/api/subscription")
    app.register_blueprint(admin_bp,     url_prefix="/api/admin")
    app.register_blueprint(wallet_bp,    url_prefix="/api/wallet")
    app.register_blueprint(ai_bp,        url_prefix="/api/ai")
    app.register_blueprint(geo_bp,       url_prefix="/api/geo")
    app.register_blueprint(twilio_bp,    url_prefix="/api/twilio")

    # ── APScheduler: daily 6 AM wellness calls (synopsis requirement) ─────────
    try:
        from routes.scheduler import init_scheduler
        init_scheduler(app)
    except Exception as ex:
        print("⚠️  APScheduler not started:", ex)
        print("   Install: pip install apscheduler --break-system-packages")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")