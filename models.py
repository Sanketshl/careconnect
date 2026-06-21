from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(50),  default="elderly")
    phone      = db.Column(db.String(20))
    location   = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    volunteer     = db.relationship("Volunteer",   backref="user", uselist=False, cascade="all, delete")
    help_requests = db.relationship("HelpRequest", foreign_keys="HelpRequest.user_id", backref="requester", lazy=True)
    sos_alerts    = db.relationship("SOSAlert",    backref="user", lazy=True, cascade="all, delete")
    notifications = db.relationship("Notification",backref="user", lazy=True, cascade="all, delete")

# ── Admin model (separate table, separate login) ───────────────────────────────
class Admin(db.Model):
    __tablename__ = "admins"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HelpRequest(db.Model):
    __tablename__ = "help_requests"
    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title              = db.Column(db.String(200))
    category           = db.Column(db.String(100))
    urgency            = db.Column(db.String(20))
    description        = db.Column(db.Text)
    status             = db.Column(db.String(20), default="open")
    assigned_volunteer = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)
    rating             = db.Column(db.Float,   nullable=True)
    carecoins          = db.Column(db.Integer, nullable=True, default=0)
    rated_at           = db.Column(db.DateTime, nullable=True)
    latitude           = db.Column(db.Float,   nullable=True)
    longitude          = db.Column(db.Float,   nullable=True)
    delivery_address   = db.Column(db.String(300), nullable=True)

class Volunteer(db.Model):
    __tablename__ = "volunteers"
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    rating          = db.Column(db.Float,   default=0)
    completed_tasks = db.Column(db.Integer, default=0)
    carecoins       = db.Column(db.Integer, default=0)

class Subscription(db.Model):
    __tablename__ = "subscriptions"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    plan       = db.Column(db.String(20), default="free")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

class EmergencyContact(db.Model):
    __tablename__ = "emergency_contacts"
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id"))
    name     = db.Column(db.String(100))
    phone    = db.Column(db.String(20))
    email    = db.Column(db.String(120))
    relation = db.Column(db.String(50))

class SOSAlert(db.Model):
    __tablename__ = "sos_alerts"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    latitude   = db.Column(db.Float)
    longitude  = db.Column(db.Float)
    message    = db.Column(db.Text)
    status     = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime,   default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = "notifications"
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    type    = db.Column(db.String(20))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

class WellnessCall(db.Model):
    __tablename__ = "wellness_logs"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    phone        = db.Column(db.String(20))
    status       = db.Column(db.String(20), default="pending")
    sentiment    = db.Column(db.String(20))
    raw_speech   = db.Column(db.Text)
    keywords     = db.Column(db.Text)
    auto_alert   = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class CareCoinTransaction(db.Model):
    __tablename__ = "carecoin_transactions"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type         = db.Column(db.String(20))
    amount       = db.Column(db.Integer, default=0)
    description  = db.Column(db.String(255))
    balance_after= db.Column(db.Integer, default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)